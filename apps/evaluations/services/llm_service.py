"""
LLM Service - Google Gemini API integration for artwork evaluation.
Uses the new `google-genai` SDK.
"""
import json
import time
import logging
from google import genai
from google.genai import types
from django.conf import settings
from PIL import Image
from apps.evaluations.services.exam_rubrics import get_rubric_scheme, FULL_PARTIAL_NONE_RULE
from core.language import normalize_language

logger = logging.getLogger(__name__)

PROMPT_I18N = {
    'uz': {
        'intro': "Siz professional san'at baholovchisiz. Berilgan rasmni davlat mezonlari asosida baholang.",
        'categories': 'BAHOLASH KATEGORIYALARI',
        'rubric': 'RASMIY IMTIHON MEZONI',
        'scheme': "Yo'nalish",
        'max_score': 'Umumiy maksimal ball',
        'rule': 'Qoida',
        'sections': "Bo'lim va mezonlar",
        'rules': 'BAHOLASH QOIDALARI',
        'rules_list': [
            "Har bir mezonda faqat `full | partial | none` darajadan birini tanlang.",
            "`awarded_score` qiymati mezon maksimaliga mos bo'lsin:",
            "full => max_score",
            "partial => max_score / 2",
            "none => 0",
            "Rasmiy mezon bo'yicha `official_rubric.total_score` ni aniq hisoblang.",
            "Qo'shimcha ravishda ichki 0-100 kategoriyalar bo'yicha ham feedback bering.",
            "Barcha izoh, tahlil, strengths/improvements va summary matnlarini o'zbek tilida yozing.",
            "Faqat JSON qaytaring, boshqa matn yo'q.",
        ],
        'response': 'JAVOB FORMATI (JSON)',
        'max_short': 'maks',
        'points': 'ball',
        'analysis_placeholder': 'Detalli tahlil...',
        'feedback_placeholder': 'qisqa izoh',
        'summary_placeholder': "Ushbu asarning umumiy tahlili va yakun xulosa...",
    },
    'en': {
        'intro': 'You are a professional art evaluator. Evaluate the submitted artwork using the official criteria.',
        'categories': 'EVALUATION CATEGORIES',
        'rubric': 'OFFICIAL EXAM RUBRIC',
        'scheme': 'Scheme',
        'max_score': 'Maximum score',
        'rule': 'Rule',
        'sections': 'Sections and criteria',
        'rules': 'EVALUATION RULES',
        'rules_list': [
            'For every criterion, choose only one level: `full | partial | none`.',
            '`awarded_score` must match the criterion max score mapping:',
            'full => max_score',
            'partial => max_score / 2',
            'none => 0',
            'Compute `official_rubric.total_score` precisely from the official rubric.',
            'Also provide internal category feedback on the 0-100 scale.',
            'Write all narrative fields (analysis, strengths, improvements, criterion feedback, summary) in English.',
            'Return JSON only, no extra text.',
        ],
        'response': 'RESPONSE FORMAT (JSON)',
        'max_short': 'max',
        'points': 'points',
        'analysis_placeholder': 'Detailed analysis...',
        'feedback_placeholder': 'brief note',
        'summary_placeholder': 'Overall analysis and final conclusion for this artwork...',
    },
    'ru': {
        'intro': 'Вы профессиональный эксперт по искусству. Оцените предоставленную работу по официальным критериям.',
        'categories': 'КАТЕГОРИИ ОЦЕНКИ',
        'rubric': 'ОФИЦИАЛЬНАЯ ЭКЗАМЕНАЦИОННАЯ РУБРИКА',
        'scheme': 'Направление',
        'max_score': 'Максимальный балл',
        'rule': 'Правило',
        'sections': 'Разделы и критерии',
        'rules': 'ПРАВИЛА ОЦЕНКИ',
        'rules_list': [
            'Для каждого критерия выберите только один уровень: `full | partial | none`.',
            '`awarded_score` должен соответствовать максимуму критерия:',
            'full => max_score',
            'partial => max_score / 2',
            'none => 0',
            'Точно рассчитайте `official_rubric.total_score` по официальной рубрике.',
            'Дополнительно дайте внутреннюю обратную связь по категориям в диапазоне 0-100.',
            'Пишите все текстовые поля (analysis, strengths, improvements, feedback, summary) на русском языке.',
            'Верните только JSON, без дополнительного текста.',
        ],
        'response': 'ФОРМАТ ОТВЕТА (JSON)',
        'max_short': 'макс',
        'points': 'балл',
        'analysis_placeholder': 'Детальный анализ...',
        'feedback_placeholder': 'краткий комментарий',
        'summary_placeholder': 'Общий анализ работы и итоговый вывод...',
    },
}


class LLMService:
    """
    Service for evaluating artwork using Google Gemini API (google-genai SDK).
    """

    def __init__(self):
        # Initialize the client with the API key
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
        self.model_name = settings.GEMINI_MODEL

    def evaluate_artwork(self, artwork, categories, language='uz', evaluation_scheme='painting'):
        """
        Main evaluation method.
        """
        from django.utils import translation
        language = normalize_language(language)
        
        start_time = time.time()

        try:
            # 1. Prepare image
            image = Image.open(artwork.image.path)

            # 2. Build prompt
            with translation.override(language):
                prompt = self._build_prompt(categories, language, evaluation_scheme)

            # 3. Call Gemini API
            # Config for JSON response
            config = types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type="application/json"
            )

            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[prompt, image],
                config=config
            )

            processing_time = time.time() - start_time

            # 4. Parse response
            response_text = response.text
            result = self._parse_response(response_text)

            # 5. Calculate cost (Approximate)
            api_cost = self._calculate_cost(response)

            logger.info(
                f"Artwork #{artwork.id} evaluated successfully in {processing_time:.2f}s "
                f"(cost: ${api_cost})"
            )

            return {
                'success': True,
                'result': result,
                'processing_time': processing_time,
                'api_cost': api_cost,
                'raw_response': response_text,
                'model': self.model_name
            }

        except Exception as e:
            processing_time = time.time() - start_time
            logger.error(f"Artwork #{artwork.id} evaluation failed: {str(e)}")
            
            # Debug: List available models if model not found
            if "404" in str(e) or "not found" in str(e).lower():
                try:
                    # In new SDK, listing models might be different, 
                    # but we try to log helpful info
                    logger.info("Attempting to list models is not fully supported in this SDK wrapper within this method context.")
                except Exception:
                    pass

            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }

    def _build_prompt(self, categories, language='uz', evaluation_scheme='painting'):
        copy = PROMPT_I18N.get(language, PROMPT_I18N['uz'])
        rubric_scheme = get_rubric_scheme(evaluation_scheme)
        categories_text = "\n".join([
            f"{i+1}. {cat.name} ({cat.weight}%) - {cat.description}"
            for i, cat in enumerate(categories)
        ])

        feedback_structure = ",\n    ".join([
            f'"{self._category_key(cat)}": {{\n'
            f'      "score": <0-100>,\n'
            f'      "analysis": "{copy["analysis_placeholder"]}",\n'
            f'      "strengths": ["...", "..."],\n'
            f'      "improvements": ["...", "..."]\n'
            f'    }}'
            for cat in categories
        ])
        score_structure = ",\n    ".join([
            f'"{self._category_key(cat)}": <0-100>'
            for cat in categories
        ])

        rubric_lines = []
        for section in rubric_scheme['sections']:
            rubric_lines.append(
                f"- {section['title']} ({copy['max_short']}: {section['max_score']} {copy['points']})"
            )
            for criterion in section['criteria']:
                rubric_lines.append(
                    f"  * [{criterion['key']}] {criterion['title']} - {criterion['max_score']} {copy['points']}"
                )
        rubric_text = "\n".join(rubric_lines)

        numbered_rules = "\n".join([f"{idx}. {rule}" for idx, rule in enumerate(copy['rules_list'], start=1)])
        required_keys = ", ".join([self._category_key(cat) for cat in categories])

        prompt = f"""{copy['intro']}

{copy['categories']}:
{categories_text}

{copy['rubric']}:
- {copy['scheme']}: {rubric_scheme['title']}
- {copy['max_score']}: {rubric_scheme['max_score']}
- {copy['rule']}: {FULL_PARTIAL_NONE_RULE}
- {copy['sections']}:
{rubric_text}

{copy['rules']}:
{numbered_rules}

JSON KEY QOIDASI:
- `scores` obyektida aynan shu kalitlar bo'lishi shart: {required_keys}
- `feedback` obyektida ham aynan shu kalitlar bo'lishi shart: {required_keys}
- JSON kalitlarini tarjima qilmang, o'zgartirmang, qisqartirmang va tashlab ketmang

{copy['response']}:
{{
  "official_rubric": {{
    "scheme": "{evaluation_scheme}",
    "max_score": {rubric_scheme['max_score']},
    "total_score": <0-{rubric_scheme['max_score']}>,
    "sections": [
      {{
        "section_key": "<section_key>",
        "section_score": <0-section_max>,
        "section_max_score": <section_max>,
        "criteria": [
          {{
            "criterion_key": "<criterion_key>",
            "level": "full|partial|none",
            "awarded_score": <computed_score>,
            "max_score": <criterion_max>,
            "feedback": "{copy['feedback_placeholder']}"
          }}
        ]
      }}
    ]
  }},
  "scores": {{
    {score_structure}
  }},
  "feedback": {{
    {feedback_structure}
  }},
  "summary": "{copy['summary_placeholder']}",
  "grade": "A"
}}
"""
        return prompt

    def _category_key(self, category):
        raw_name = (
            getattr(category, 'name_en', None)
            or getattr(category, 'name', '')
        ).strip().lower()
        key_map = {
            'composition': 'composition',
            'color and light': 'color_light',
            'technique': 'technique',
            'creativity': 'creativity',
            'overall impact': 'overall_impact',
        }
        return key_map.get(raw_name, raw_name.replace(' ', '_'))

    def _parse_response(self, response_text):
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            text = response_text.strip()
            if text.startswith('```json'):
                text = text[7:]
            if text.startswith('```'):
                text = text[3:]
            if text.endswith('```'):
                text = text[:-3]
            return json.loads(text.strip())

    def _calculate_cost(self, response):
        try:
            usage = response.usage_metadata
            input_tokens = usage.prompt_token_count
            output_tokens = usage.candidates_token_count
            # Pricing for Gemini 1.5 Flash (Approx)
            input_cost = input_tokens * (0.35 / 1_000_000)
            output_cost = output_tokens * (1.05 / 1_000_000)
            return round(input_cost + output_cost, 6)
        except Exception:
            return 0.0
