# 🎨 AI Art Evaluation System - To'liq Loyiha Spetsifikatsiyasi

## 📋 MUNDARIJA
1. [Loyiha haqida](#loyiha-haqida)
2. [Asosiy funksiyalar](#asosiy-funksiyalar)
3. [Texnologik stack](#texnologik-stack)
4. [Tizim arxitekturasi](#tizim-arxitekturasi)
5. [Database modellar](#database-modellar)
6. [LLM Integration](#llm-integration)
7. [API Endpoints](#api-endpoints)
8. [Loyiha strukturasi](#loyiha-strukturasi)
9. [Bosqichma-bosqich vazifalar](#bosqichma-bosqich-vazifalar)
10. [Environment va konfiguratsiya](#environment-va-konfiguratsiya)

---

## 🎯 LOYIHA HAQIDA

### Muammo
Hozirgi vaqtda ijodiy ishlar (rasmlar, tasviriy san'at) ni odamlar tekshiradi. Bu jarayonda:
- Subyektivlik va korrupsiya xavfi mavjud
- Vaqt talab qiladi
- Katta hajmdagi ishlarni baholash qiyin
- Doimiy va obyektiv mezonlar yo'q

### Yechim
LLM (Large Language Model) asosida AI tizimi yaratish:
- Ijodiy ishlarni avtomatik baholaydi
- Obyektiv va konsistent mezonlar bilan ishlaydi
- Tezkor natija beradi (2-5 soniya)
- Detalli feedback va tahlil beradi
- Korrupsiya xavfini kamaytiradi

### Foydalanuvchilar
1. **Rassomlar (Artists)** - o'z ishlarini yuklaydi va baholash oladi
2. **Adminlar** - tizimni boshqaradi, kategoriyalarni sozlaydi
3. **Hakamlar (Judges)** - AI natijalarini ko'rib chiqadi (ixtiyoriy)

---

## ⚙️ ASOSIY FUNKSIYALAR

### 1. Rasm Yuklash va Saqlash
- Foydalanuvchi rassmini yuklaydi (JPG, PNG, WebP)
- Max hajm: 10MB
- Avtomatik optimizatsiya va kompressiya
- S3/MinIO cloud storage ga saqlash

### 2. AI Baholash (Core Feature)
- Claude 3.5 Sonnet LLM yordamida tahlil
- 5 ta kategoriya bo'yicha baholash:
  1. **Kompozitsiya (20%)** - balans, simmetriya, focal point
  2. **Rang va yorug'lik (20%)** - ranglar uyg'unligi, kontrast
  3. **Texnika (25%)** - chiziqlash sifati, detalizatsiya
  4. **Kreativlik (20%)** - noyoblik, ijodiy yondashuv
  5. **Umumiy ta'sir (15%)** - emotional ta'sir, professional ko'rinish
- Har bir kategoriya uchun:
  - Ball (0-100)
  - Detalli tahlil
  - Kuchli tomonlar (strengths)
  - Yaxshilanish tavsiyalari (improvements)
- Umumiy ball (weighted average)

### 3. Natijalarni Ko'rsatish
- Vizual dashboard
- Kategoriya bo'yicha breakdown
- Tarix va statistika
- PDF export (ixtiyoriy)

### 4. Admin Panel
- Django admin orqali to'liq boshqaruv
- Kategoriyalar CRUD
- Foydalanuvchilar boshqaruvi
- Statistika va monitoring

### 5. Kredit Tizimi
- Har bir foydalanuvchi 10 ta bepul kredit oladi
- Har bir baholash 1 kredit sarflaydi
- Admin qo'shimcha kredit berishi mumkin

---

## 🛠 TEXNOLOGIK STACK

### Backend
- **Framework:** Django 4.2.9
- **API:** Django REST Framework 3.14
- **Authentication:** JWT (djangorestframework-simplejwt)
- **Database:** PostgreSQL 15
- **Cache:** Redis 7
- **Task Queue:** Celery 5.3.4
- **LLM Integration:** Anthropic Claude API (anthropic==0.18.1)
- **Image Processing:** Pillow 10.2.0
- **Storage:** AWS S3 / MinIO (boto3)

### Frontend (Minimal MVP)
- React 18 + TypeScript (ixtiyoriy)
- yoki Django Templates (tezkor ishga tushirish uchun)
- Tailwind CSS

### DevOps
- Docker + Docker Compose
- PostgreSQL container
- Redis container
- Celery worker va beat containers

### LLM
- **Provider:** Anthropic Claude
- **Model:** claude-3-5-sonnet-20241022
- **Narx:** ~$0.01 per rasm
- **Temperature:** 0.3 (konsistent natijalar uchun)

---

## 🏗 TIZIM ARXITEKTURASI

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND LAYER                        │
│  - Rasm yuklash interfeysi                              │
│  - Natijalar dashboard                                   │
│  - Baholash tarixi                                       │
└─────────────────────────────────────────────────────────┘
                         ↓ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│                    API GATEWAY                           │
│  Django REST Framework                                   │
│  - JWT Authentication                                    │
│  - Rate Limiting                                         │
│  - Request Validation                                    │
│  - CORS                                                  │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 DJANGO BACKEND CORE                      │
├──────────────────┬──────────────────┬───────────────────┤
│  Users App       │  Artworks App    │  Evaluations App  │
│  - User Model    │  - Artwork Model │  - Evaluation     │
│  - Auth          │  - Upload        │  - LLM Service    │
│  - Profiles      │  - Storage       │  - Scoring        │
│  - Permissions   │  - Categories    │  - History        │
└──────────────────┴──────────────────┴───────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                   SERVICES LAYER                         │
├──────────────────┬──────────────────┬───────────────────┤
│  Image Service   │  LLM Service     │  Scoring Service  │
│  - Validation    │  - Claude API    │  - Calculate      │
│  - Compression   │  - Prompt Build  │  - Aggregate      │
│  - S3 Upload     │  - Parse JSON    │  - Weighted Avg   │
└──────────────────┴──────────────────┴───────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                  EXTERNAL SERVICES                       │
├──────────────────┬──────────────────┬───────────────────┤
│  Claude API      │  AWS S3/MinIO    │  Redis Cache      │
│  (Anthropic)     │  (File Storage)  │  (Celery Broker)  │
└──────────────────┴──────────────────┴───────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                        │
│  PostgreSQL 15                                          │
│  - users, artworks, evaluations, categories,            │
│    category_scores, evaluation_history                  │
└─────────────────────────────────────────────────────────┘
```

### Workflow (Ishlash jarayoni)

1. **Foydalanuvchi rasmni yuklaydi**
   - Frontend → API: POST /api/artworks/
   - File validation (format, size)
   - S3/MinIO ga yuklash
   - Artwork record yaratish (status: pending)

2. **Async baholash boshlanadi**
   - Celery task trigger: `evaluate_artwork_async.delay(artwork_id)`
   - Artwork status → processing

3. **LLM Service ishlaydi**
   - Rasmni base64 ga encode qilish
   - Dynamic prompt yaratish (kategoriyalar asosida)
   - Claude API ga so'rov yuborish
   - JSON response olish

4. **Natijalarni saqlash**
   - Evaluation record yaratish
   - CategoryScore lar yaratish
   - Weighted average hisoblash
   - Artwork status → completed

5. **Foydalanuvchiga ko'rsatish**
   - GET /api/evaluations/{id}/
   - Detalli natija va feedback

---

## 💾 DATABASE MODELLAR

### 1. User (AbstractUser dan meros)
```python
class User(AbstractUser):
    role = CharField  # artist, admin, judge
    phone = CharField
    avatar = ImageField
    bio = TextField
    credits = IntegerField (default=10)
    
    # Django AbstractUser fields:
    # username, email, password, first_name, last_name,
    # is_staff, is_active, date_joined
```

### 2. Category
```python
class Category:
    id = AutoField (PK)
    name = CharField  # "Composition"
    name_uz = CharField  # "Kompozitsiya"
    description = TextField
    weight = DecimalField  # 20.00 (percentage)
    criteria = JSONField  # Detalli mezonlar
    is_active = BooleanField (default=True)
```

**Default kategoriyalar:**
```python
[
    {
        "name": "Composition",
        "name_uz": "Kompozitsiya",
        "weight": 20,
        "description": "Balans, simmetriya, focal point",
        "criteria": {
            "balance": "Vizual balans va simmetriya",
            "focal_point": "Diqqat markazining aniqligi",
            "lines_shapes": "Chiziqlar va shakllarning uyg'unligi"
        }
    },
    {
        "name": "Color and Light",
        "name_uz": "Rang va yorug'lik",
        "weight": 20,
        "description": "Rang palitrasining uyg'unligi, kontrast",
        "criteria": {
            "palette": "Rang palitrasining harmoniyasi",
            "contrast": "Kontrast va dinamiklik",
            "lighting": "Yorug'lik-soya balansi"
        }
    },
    {
        "name": "Technique",
        "name_uz": "Texnika",
        "weight": 25,
        "description": "Chiziqlash sifati, detalizatsiya",
        "criteria": {
            "line_quality": "Chiziqlarning sifati",
            "detail": "Detalizatsiya darajasi",
            "application": "Texnikaning to'g'ri qo'llanilishi"
        }
    },
    {
        "name": "Creativity",
        "name_uz": "Kreativlik",
        "weight": 20,
        "description": "Noyoblik, ijodiy yondashuv",
        "criteria": {
            "originality": "Noyoblik va originallik",
            "innovation": "Innovatsion yondashuv",
            "uniqueness": "O'ziga xoslik"
        }
    },
    {
        "name": "Overall Impact",
        "name_uz": "Umumiy ta'sir",
        "weight": 15,
        "description": "Emotional ta'sir, professional ko'rinish",
        "criteria": {
            "emotion": "Emotsional ta'sir",
            "professionalism": "Professional ko'rinish",
            "completion": "Tugallangan his"
        }
    }
]
```

### 3. Artwork
```python
class Artwork:
    id = AutoField (PK)
    user = ForeignKey(User)
    title = CharField (max_length=255)
    description = TextField (blank=True)
    image = ImageField (upload_to='artworks/%Y/%m/%d/')
    image_url = URLField (blank=True)  # S3 URL
    file_size = IntegerField  # bytes
    width = IntegerField
    height = IntegerField
    format = CharField  # jpg, png, webp
    status = CharField  # pending, processing, completed, failed
    created_at = DateTimeField (auto_now_add=True)
    updated_at = DateTimeField (auto_now=True)
```

### 4. Evaluation
```python
class Evaluation:
    id = AutoField (PK)
    artwork = OneToOneField(Artwork)
    
    # LLM metadata
    llm_provider = CharField (default='claude')
    llm_model = CharField  # claude-3-5-sonnet-20241022
    prompt_version = CharField
    
    # Natijalar
    total_score = DecimalField (max_digits=5, decimal_places=2)
    raw_response = JSONField  # LLM ning to'liq javobi
    
    # Performance metrics
    processing_time = DecimalField  # seconds
    api_cost = DecimalField (null=True)  # USD
    
    created_at = DateTimeField (auto_now_add=True)
```

### 5. CategoryScore
```python
class CategoryScore:
    id = AutoField (PK)
    evaluation = ForeignKey(Evaluation)
    category = ForeignKey(Category)
    
    score = DecimalField (0-100)
    feedback = TextField  # LLM tahlili
    strengths = JSONField  # ["...", "..."]
    improvements = JSONField  # ["...", "..."]
    
    unique_together = ['evaluation', 'category']
```

### 6. EvaluationHistory
```python
class EvaluationHistory:
    id = AutoField (PK)
    evaluation = ForeignKey(Evaluation)
    action = CharField  # started, completed, failed
    message = TextField
    metadata = JSONField
    created_at = DateTimeField (auto_now_add=True)
```

---

## 🤖 LLM INTEGRATION

### Claude API Configuration
```python
# settings.py
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
ANTHROPIC_MODEL = 'claude-3-5-sonnet-20241022'
ANTHROPIC_MAX_TOKENS = 2048
ANTHROPIC_TEMPERATURE = 0.3  # Konsistent natijalar uchun
```

### LLM Service Implementation

**File:** `apps/evaluations/services/llm_service.py`

```python
import anthropic
import json
import time
import base64
from django.conf import settings
from PIL import Image
import io

class LLMService:
    def __init__(self):
        self.client = anthropic.Anthropic(
            api_key=settings.ANTHROPIC_API_KEY
        )
        self.model = settings.ANTHROPIC_MODEL
    
    def evaluate_artwork(self, artwork, categories):
        """
        Asosiy baholash metodi
        
        Args:
            artwork: Artwork model instance
            categories: QuerySet of Category objects
            
        Returns:
            dict: {
                'success': bool,
                'result': dict or None,
                'processing_time': float,
                'api_cost': float,
                'raw_response': str,
                'model': str,
                'error': str (if failed)
            }
        """
        start_time = time.time()
        
        try:
            # 1. Rasmni tayyorlash
            image_data = self._prepare_image(artwork.image.path)
            
            # 2. Prompt yaratish
            prompt = self._build_prompt(categories)
            
            # 3. Claude API ga so'rov
            message = self.client.messages.create(
                model=self.model,
                max_tokens=settings.ANTHROPIC_MAX_TOKENS,
                temperature=settings.ANTHROPIC_TEMPERATURE,
                messages=[{
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_data,
                            },
                        },
                        {
                            "type": "text",
                            "text": prompt
                        }
                    ],
                }],
            )
            
            processing_time = time.time() - start_time
            
            # 4. Response parse qilish
            response_text = message.content[0].text
            result = self._parse_response(response_text)
            
            # 5. Cost hisoblash
            api_cost = self._calculate_cost(message)
            
            return {
                'success': True,
                'result': result,
                'processing_time': processing_time,
                'api_cost': api_cost,
                'raw_response': response_text,
                'model': self.model
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _prepare_image(self, image_path):
        """
        Rasmni optimize va base64 ga o'tkazish
        
        - Max size: 1568px (Claude limit)
        - Format: JPEG
        - Quality: 90
        """
        img = Image.open(image_path)
        
        # Resize if needed
        max_size = 1568
        if max(img.size) > max_size:
            img.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
        
        # Convert to JPEG
        buffer = io.BytesIO()
        img.convert('RGB').save(buffer, format='JPEG', quality=90)
        
        # Encode to base64
        return base64.b64encode(buffer.getvalue()).decode()
    
    def _build_prompt(self, categories):
        """
        Dynamic prompt generation
        
        Kategoriyalar asosida prompt yaratadi
        """
        # Kategoriyalarni format qilish
        categories_text = "\n".join([
            f"{i+1}. {cat.name_uz} ({cat.weight}%) - {cat.description}"
            for i, cat in enumerate(categories)
        ])
        
        # Kategoriya key mapping
        category_keys = {
            'Composition': 'composition',
            'Color and Light': 'color_light',
            'Technique': 'technique',
            'Creativity': 'creativity',
            'Overall Impact': 'overall_impact'
        }
        
        feedback_structure = ",\n    ".join([
            f'"{category_keys.get(cat.name, cat.name.lower())}": {{\n'
            f'      "score": <0-100>,\n'
            f'      "analysis": "Detalli tahlil...",\n'
            f'      "strengths": ["...", "..."],\n'
            f'      "improvements": ["...", "..."]\n'
            f'    }}'
            for cat in categories
        ])
        
        prompt = f"""Siz professional san'at baholovchisiz. Berilgan rasmni quyidagi kategoriyalar bo'yicha tahlil qilib, har biriga 0-100 oralig'ida ball bering.

BAHOLASH KATEGORIYALARI:
{categories_text}

IMPORTANT BAHOLASH QOIDALARI:
1. Har bir kategoriyaga objektiv va professional yondashuv
2. Ballni aniq mezonlar asosida bering (60-70: qoniqarli, 70-80: yaxshi, 80-90: juda yaxshi, 90-100: mukammal)
3. Har bir kategoriya uchun:
   - Aniq tahlil (minimum 2-3 jumla)
   - Kamida 2 ta kuchli tomon (strengths)
   - Kamida 2 ta yaxshilanish tavsiyasi (improvements)
4. Konstruktiv va motivatsion feedback bering
5. O'zbek tilidagi texnik terminlardan foydalaning

JAVOB FORMATI (faqat to'g'ri JSON, boshqa matn yo'q):
{{
  "scores": {{
    "composition": 85,
    "color_light": 78,
    "technique": 90,
    "creativity": 82,
    "overall_impact": 88
  }},
  "feedback": {{
    {feedback_structure}
  }},
  "summary": "Ushbu asarning umumiy tahlili va yakun xulosa (3-5 jumla)...",
  "grade": "A"
}}

GRADE TIZIMI:
- A (90-100): Mukammal
- B (80-89): Juda yaxshi
- C (70-79): Yaxshi
- D (60-69): Qoniqarli
- F (0-59): Qoniqarsiz

Endi rasmni tahlil qiling va FAQAT JSON formatida javob bering:"""
        
        return prompt
    
    def _parse_response(self, response_text):
        """
        LLM javobini JSON ga parse qilish
        
        Handles:
        - Markdown code blocks
        - Extra whitespace
        - JSON parsing errors
        """
        try:
            # Remove markdown if exists
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.startswith('```'):
                response_text = response_text[3:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            # Parse JSON
            return json.loads(response_text.strip())
            
        except json.JSONDecodeError as e:
            # Fallback: return error structure
            return {
                'error': 'JSON parse error',
                'message': str(e),
                'raw': response_text
            }
    
    def _calculate_cost(self, message):
        """
        API cost hisoblash
        
        Claude Sonnet pricing:
        - Input: $3 per 1M tokens
        - Output: $15 per 1M tokens
        """
        input_tokens = message.usage.input_tokens
        output_tokens = message.usage.output_tokens
        
        input_cost = input_tokens * 0.000003
        output_cost = output_tokens * 0.000015
        
        return round(input_cost + output_cost, 4)
```

### Scoring Service

**File:** `apps/evaluations/services/scoring_service.py`

```python
from decimal import Decimal
from apps.artworks.models import Category
from apps.evaluations.models import Evaluation, CategoryScore, EvaluationHistory

class ScoringService:
    def create_evaluation(self, artwork, llm_result):
        """
        LLM natijalaridan Evaluation yaratish
        
        Steps:
        1. Evaluation record yaratish
        2. Har bir kategoriya uchun CategoryScore yaratish
        3. Weighted average hisoblash
        4. Artwork status yangilash
        5. History log yaratish
        """
        categories = Category.objects.filter(is_active=True)
        
        # 1. Evaluation yaratish (total_score hali 0)
        evaluation = Evaluation.objects.create(
            artwork=artwork,
            llm_provider='claude',
            llm_model=llm_result['model'],
            prompt_version='1.0',
            total_score=Decimal('0.00'),
            raw_response=llm_result['result'],
            processing_time=Decimal(str(llm_result['processing_time'])),
            api_cost=Decimal(str(llm_result.get('api_cost', 0)))
        )
        
        # History: started
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action='started',
            message='Baholash boshlandi',
            metadata={'artwork_id': artwork.id}
        )
        
        # 2. CategoryScore lar yaratish va weighted score hisoblash
        total_weighted_score = Decimal('0.00')
        feedback_data = llm_result['result'].get('feedback', {})
        
        for category in categories:
            # Category key mapping
            category_key = self._get_category_key(category.name)
            category_feedback = feedback_data.get(category_key, {})
            
            score = Decimal(str(category_feedback.get('score', 0)))
            
            # CategoryScore yaratish
            CategoryScore.objects.create(
                evaluation=evaluation,
                category=category,
                score=score,
                feedback=category_feedback.get('analysis', 'Tahlil mavjud emas'),
                strengths=category_feedback.get('strengths', []),
                improvements=category_feedback.get('improvements', [])
            )
            
            # Weighted score qo'shish
            weight = category.weight / Decimal('100')
            total_weighted_score += (score * weight)
        
        # 3. Total score yangilash
        evaluation.total_score = round(total_weighted_score, 2)
        evaluation.save()
        
        # 4. Artwork status yangilash
        artwork.status = 'completed'
        artwork.save()
        
        # 5. History: completed
        EvaluationHistory.objects.create(
            evaluation=evaluation,
            action='completed',
            message=f'Baholash muvaffaqiyatli yakunlandi. Ball: {evaluation.total_score}',
            metadata={
                'total_score': float(evaluation.total_score),
                'processing_time': float(evaluation.processing_time)
            }
        )
        
        return evaluation
    
    def _get_category_key(self, category_name):
        """Kategoriya nomini LLM key ga map qilish"""
        mapping = {
            'Composition': 'composition',
            'Color and Light': 'color_light',
            'Technique': 'technique',
            'Creativity': 'creativity',
            'Overall Impact': 'overall_impact'
        }
        return mapping.get(category_name, category_name.lower().replace(' ', '_'))
```

---

## 🔌 API ENDPOINTS

### Authentication
```
POST   /api/auth/register/
POST   /api/auth/login/
POST   /api/auth/refresh/
POST   /api/auth/logout/
```

### Artworks
```
GET    /api/artworks/              # List user's artworks
POST   /api/artworks/              # Upload new artwork
GET    /api/artworks/{id}/         # Get artwork detail
PUT    /api/artworks/{id}/         # Update artwork
DELETE /api/artworks/{id}/         # Delete artwork
POST   /api/artworks/{id}/re-evaluate/  # Re-evaluate artwork
```

### Evaluations
```
GET    /api/evaluations/           # List user's evaluations
GET    /api/evaluations/{id}/      # Get evaluation detail with scores
```

### Categories
```
GET    /api/categories/            # List all active categories
```

### User Profile
```
GET    /api/profile/               # Get current user profile
PUT    /api/profile/               # Update profile
GET    /api/profile/stats/         # Get user statistics
```

---

## 📁 LOYIHA STRUKTURASI

```
art_evaluation_project/
│
├── config/                          # Django project settings
│   ├── __init__.py
│   ├── settings/
│   │   ├── __init__.py
│   │   ├── base.py                  # Base settings
│   │   ├── development.py           # Dev settings
│   │   └── production.py            # Prod settings
│   ├── urls.py                      # Root URL config
│   ├── wsgi.py
│   ├── asgi.py
│   └── celery.py                    # Celery config
│
├── apps/
│   │
│   ├── users/                       # User management
│   │   ├── __init__.py
│   │   ├── models.py                # User model
│   │   ├── serializers.py           # User serializers
│   │   ├── views.py                 # Auth views
│   │   ├── urls.py
│   │   ├── admin.py                 # User admin
│   │   ├── permissions.py           # Custom permissions
│   │   └── tests.py
│   │
│   ├── artworks/                    # Artwork management
│   │   ├── __init__.py
│   │   ├── models.py                # Artwork, Category models
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── image_service.py     # Image processing
│   │   │   └── storage_service.py   # S3/MinIO upload
│   │   └── tests.py
│   │
│   └── evaluations/                 # AI evaluation
│       ├── __init__.py
│       ├── models.py                # Evaluation, CategoryScore models
│       ├── serializers.py
│       ├── views.py
│       ├── urls.py
│       ├── admin.py
│       ├── tasks.py                 # Celery tasks
│       ├── services/
│       │   ├── __init__.py
│       │   ├── llm_service.py       # Claude integration
│       │   ├── scoring_service.py   # Score calculation
│       │   └── prompt_templates.py  # Prompt management
│       └── tests.py
│
├── core/                            # Shared utilities
│   ├── __init__.py
│   ├── exceptions.py                # Custom exceptions
│   ├── permissions.py               # Base permissions
│   ├── pagination.py                # Custom pagination
│   ├── mixins.py                    # Reusable mixins
│   └── validators.py                # Custom validators
│
├── fixtures/                        # Initial data
│   ├── categories.json              # Default categories
│   └── test_users.json              # Test users (dev only)
│
├── media/                           # User uploads (dev)
│   └── artworks/
│
├── static/                          # Static files
│   ├── css/
│   ├── js/
│   └── images/
│
├── templates/                       # Django templates
│   ├── base.html
│   └── admin/
│
├── requirements/
│   ├── base.txt                     # Base requirements
│   ├── development.txt              # Dev requirements
│   └── production.txt               # Prod requirements
│
├── docker-compose.yml               # Docker setup
├── Dockerfile                       # Django container
├── .env.example                     # Environment example
├── .gitignore
├── README.md
├── manage.py
└── pytest.ini                       # Test configuration
```

---

## ✅ BOSQICHMA-BOSQICH VAZIFALAR

### PHASE 1: Backend Setup (Kun 1-2)

#### 1.1 Django Project Initialization
- [ ] Django project yaratish: `django-admin startproject config .`
- [ ] Apps yaratish:
  - `python manage.py startapp users`
  - `python manage.py startapp artworks`
  - `python manage.py startapp evaluations`
- [ ] Folder strukturasini tuzatish (apps/ folder ga ko'chirish)
- [ ] Settings split (base, dev, prod)

#### 1.2 Database Models
- [ ] User model (AbstractUser extend)
- [ ] Category model
- [ ] Artwork model
- [ ] Evaluation model
- [ ] CategoryScore model
- [ ] EvaluationHistory model
- [ ] Migrations yaratish va run qilish

#### 1.3 Django Admin
- [ ] Har bir model uchun ModelAdmin yaratish
- [ ] List displays, filters, search qo'shish
- [ ] Inline admin (CategoryScore → Evaluation)
- [ ] Custom actions qo'shish

#### 1.4 DRF Setup
- [ ] REST Framework configure
- [ ] JWT authentication setup
- [ ] CORS middleware
- [ ] Serializers yaratish (barcha models uchun)
- [ ] ViewSets yaratish

---

### PHASE 2: LLM Integration (Kun 2-3)

#### 2.1 LLM Service
- [ ] `llm_service.py` yaratish
- [ ] Claude client initialize
- [ ] `evaluate_artwork()` method
- [ ] `_prepare_image()` - resize va base64
- [ ] `_build_prompt()` - dynamic prompt
- [ ] `_parse_response()` - JSON parsing
- [ ] `_calculate_cost()` - pricing

#### 2.2 Scoring Service
- [ ] `scoring_service.py` yaratish
- [ ] `create_evaluation()` method
- [ ] CategoryScore lar yaratish logic
- [ ] Weighted average hisoblash
- [ ] History logging

#### 2.3 Testing
- [ ] Test rasmlar bilan test qilish
- [ ] Different scenarios (good, bad, medium art)
- [ ] Error handling test
- [ ] JSON parsing test

---

### PHASE 3: Celery Async Tasks (Kun 3-4)

#### 3.1 Celery Setup
- [ ] Celery config in `config/celery.py`
- [ ] Redis broker configure
- [ ] Celery worker test

#### 3.2 Tasks
- [ ] `evaluate_artwork_async` task yaratish
- [ ] Task status tracking
- [ ] Error handling va retry logic
- [ ] Task result backend

#### 3.3 Integration
- [ ] Artwork upload → trigger async task
- [ ] Status updates (pending → processing → completed)
- [ ] Webhook yoki polling (frontend uchun)

---

### PHASE 4: Storage & File Management (Kun 4)

#### 4.1 Image Service
- [ ] Image validation (format, size)
- [ ] Image optimization
- [ ] Thumbnail generation (optional)

#### 4.2 S3/MinIO Integration
- [ ] boto3 setup
- [ ] Upload to S3/MinIO
- [ ] Generate signed URLs
- [ ] Delete from storage

---

### PHASE 5: API Endpoints (Kun 5)

#### 5.1 Authentication
- [ ] Register endpoint
- [ ] Login (JWT tokens)
- [ ] Refresh token
- [ ] Logout

#### 5.2 Artworks
- [ ] List artworks (pagination)
- [ ] Create artwork (upload)
- [ ] Detail view
- [ ] Update/Delete
- [ ] Re-evaluate action

#### 5.3 Evaluations
- [ ] List evaluations
- [ ] Detail view (with CategoryScores)

#### 5.4 Categories
- [ ] List categories

#### 5.5 Profile
- [ ] Get profile
- [ ] Update profile
- [ ] Statistics

---

### PHASE 6: Testing & Documentation (Kun 6-7)

#### 6.1 Unit Tests
- [ ] Models test
- [ ] Serializers test
- [ ] Views test
- [ ] Services test

#### 6.2 Integration Tests
- [ ] Full flow test (upload → evaluate → get result)
- [ ] Error scenarios

#### 6.3 API Documentation
- [ ] Swagger/OpenAPI setup
- [ ] Postman collection

---

### PHASE 7: Docker & Deployment (Kun 7-8)

#### 7.1 Docker Setup
- [ ] Dockerfile yaratish
- [ ] docker-compose.yml (db, redis, web, celery)
- [ ] Environment variables
- [ ] Test local docker

#### 7.2 Production Setup
- [ ] Production settings
- [ ] Static files collection
- [ ] Media files handling
- [ ] Security checklist

#### 7.3 Deployment
- [ ] Server setup (AWS, DigitalOcean, etc)
- [ ] Deploy va test
- [ ] Monitoring setup

---

### PHASE 8: Frontend (Kun 9-12) - OPTIONAL

**Minimal MVP uchun Django templates ishlatish mumkin**

#### 8.1 Basic UI
- [ ] Upload page
- [ ] Results dashboard
- [ ] History page
- [ ] Profile page

---

## 🔧 ENVIRONMENT VA KONFIGURATSIYA

### .env.example
```env
# Django
DEBUG=True
SECRET_KEY=your-secret-key-here
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://postgres:postgres@db:5432/art_evaluation

# Redis
REDIS_URL=redis://redis:6379/0

# Anthropic Claude
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# AWS S3 (yoki MinIO)
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_STORAGE_BUCKET_NAME=art-evaluation-bucket
AWS_S3_REGION_NAME=us-east-1

# File Upload
MAX_UPLOAD_SIZE=10485760  # 10MB
ALLOWED_IMAGE_FORMATS=jpeg,jpg,png,webp

# Celery
CELERY_BROKER_URL=${REDIS_URL}
CELERY_RESULT_BACKEND=django-db

# Email (optional)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

### requirements/base.txt
```txt
# Django
Django==4.2.9
djangorestframework==3.14.0
djangorestframework-simplejwt==5.3.1

# Database
psycopg2-binary==2.9.9
dj-database-url==2.1.0

# Celery
celery==5.3.4
redis==5.0.1
django-celery-beat==2.5.0
django-celery-results==2.5.1

# LLM
anthropic==0.18.1

# Image Processing
Pillow==10.2.0

# Storage
boto3==1.34.34

# Utils
python-dotenv==1.0.0
python-decouple==3.8

# Security
django-cors-headers==4.3.1

# Monitoring (optional)
django-debug-toolbar==4.2.0
```

### requirements/development.txt
```txt
-r base.txt

# Testing
pytest==7.4.3
pytest-django==4.7.0
pytest-cov==4.1.0
factory-boy==3.3.0

# Code Quality
black==23.12.1
flake8==7.0.0
isort==5.13.2

# Debugging
ipython==8.19.0
django-extensions==3.2.3
```

### Docker Compose
```yaml
version: '3.8'

services:
  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: art_evaluation
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 3s
      retries: 5

  web:
    build: .
    command: python manage.py runserver 0.0.0.0:8000
    volumes:
      - .:/app
      - media_files:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_healthy

  celery:
    build: .
    command: celery -A config worker -l info
    volumes:
      - .:/app
      - media_files:/app/media
    env_file:
      - .env
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - .:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis

volumes:
  postgres_data:
  media_files:
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements/base.txt requirements/
RUN pip install --no-cache-dir -r requirements/base.txt

# Copy project
COPY . .

# Collect static files (for production)
# RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
```

---

## 📊 INITIAL DATA (Fixtures)

### fixtures/categories.json
```json
[
  {
    "model": "artworks.category",
    "pk": 1,
    "fields": {
      "name": "Composition",
      "name_uz": "Kompozitsiya",
      "description": "Balans, simmetriya, va focal point tahlili",
      "weight": "20.00",
      "criteria": {
        "balance": "Vizual balans va simmetriya",
        "focal_point": "Diqqat markazining aniqligi",
        "lines_shapes": "Chiziqlar va shakllarning uyg'unligi",
        "space": "Bo'shliqdan foydalanish"
      },
      "is_active": true
    }
  },
  {
    "model": "artworks.category",
    "pk": 2,
    "fields": {
      "name": "Color and Light",
      "name_uz": "Rang va yorug'lik",
      "description": "Rang palitrasining uyg'unligi va yorug'lik balansi",
      "weight": "20.00",
      "criteria": {
        "palette": "Rang palitrasining harmoniyasi",
        "contrast": "Kontrast va dinamiklik",
        "lighting": "Yorug'lik-soya balansi",
        "mood": "Ranglar orqali mood yaratish"
      },
      "is_active": true
    }
  },
  {
    "model": "artworks.category",
    "pk": 3,
    "fields": {
      "name": "Technique",
      "name_uz": "Texnika",
      "description": "Chiziqlash sifati va texnik mahorat",
      "weight": "25.00",
      "criteria": {
        "line_quality": "Chiziqlarning sifati va aniqlik",
        "detail": "Detalizatsiya darajasi",
        "application": "Texnikaning to'g'ri qo'llanilishi",
        "mastery": "Umumiy texnik mahorat"
      },
      "is_active": true
    }
  },
  {
    "model": "artworks.category",
    "pk": 4,
    "fields": {
      "name": "Creativity",
      "name_uz": "Kreativlik",
      "description": "Noyoblik va ijodiy yondashuv",
      "weight": "20.00",
      "criteria": {
        "originality": "Noyoblik va originallik",
        "innovation": "Innovatsion yondashuv",
        "uniqueness": "O'ziga xoslik",
        "concept": "Konsepsiya va g'oya"
      },
      "is_active": true
    }
  },
  {
    "model": "artworks.category",
    "pk": 5,
    "fields": {
      "name": "Overall Impact",
      "name_uz": "Umumiy ta'sir",
      "description": "Emotional ta'sir va professional ko'rinish",
      "weight": "15.00",
      "criteria": {
        "emotion": "Emotsional ta'sir",
        "professionalism": "Professional ko'rinish",
        "completion": "Tugallangan his",
        "message": "Yetkazilayotgan xabar"
      },
      "is_active": true
    }
  }
]
```

---

## 🧪 TESTING EXAMPLES

### Test LLM Service
```python
# apps/evaluations/tests/test_llm_service.py
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from apps.artworks.models import Artwork, Category
from apps.evaluations.services.llm_service import LLMService

@pytest.mark.django_db
class TestLLMService:
    def test_evaluate_artwork_success(self, user, categories):
        # Create test artwork
        with open('test_image.jpg', 'rb') as f:
            image = SimpleUploadedFile(
                "test.jpg", 
                f.read(), 
                content_type="image/jpeg"
            )
        
        artwork = Artwork.objects.create(
            user=user,
            title="Test Artwork",
            image=image,
            file_size=1024,
            width=800,
            height=600,
            format='jpg'
        )
        
        # Run evaluation
        service = LLMService()
        result = service.evaluate_artwork(artwork, categories)
        
        # Assertions
        assert result['success'] is True
        assert 'result' in result
        assert 'scores' in result['result']
        assert result['processing_time'] > 0
```

---

## 📝 QAYERDAN BOSHLASH

### Quick Start Commands

```bash
# 1. Virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements/development.txt

# 3. Create .env file
cp .env.example .env
# Edit .env and add your keys

# 4. Database setup
python manage.py makemigrations
python manage.py migrate

# 5. Load initial data
python manage.py loaddata fixtures/categories.json

# 6. Create superuser
python manage.py createsuperuser

# 7. Run server
python manage.py runserver

# 8. Run Celery (new terminal)
celery -A config worker -l info

# 9. Run tests
pytest
```

### Development Workflow

1. **Model yaratish** → Migration → Admin register
2. **Serializer yaratish** → ViewSet → URL routing
3. **Service yaratish** → Business logic
4. **Task yaratish** → Async processing
5. **Test yozish** → Test coverage
6. **Documentation** → API docs

---

## 🎯 SUCCESS CRITERIA

Loyiha muvaffaqiyatli yakunlangan hisoblanadi agar:

1. ✅ Foydalanuvchi rasm yuklashi mumkin
2. ✅ Rasm avtomatik baholanadi (2-5 soniya ichida)
3. ✅ 5 ta kategoriya bo'yicha ball va feedback beriladi
4. ✅ Natijalar aniq va foydali
5. ✅ Django admin to'liq ishlaydi
6. ✅ API documentation mavjud
7. ✅ Docker bilan ishga tushirish mumkin
8. ✅ Tests pass bo'ladi (>80% coverage)

---

## 🚀 OPTIMIZATION IDEAS (Keyingi bosqichlar)

1. **Caching** - Redis bilan frequent queries cache qilish
2. **Rate Limiting** - API abuse oldini olish
3. **Webhooks** - Frontend uchun real-time updates
4. **Batch Processing** - Ko'p rasmlarni bir vaqtda baholash
5. **Analytics** - Usage statistics va insights
6. **Payment Integration** - Credit sotish tizimi
7. **Social Features** - Artworks ni share qilish
8. **Portfolio** - Artist portfolio page
9. **Compare** - Ikki rasmni solishtirish
10. **Export** - PDF/Excel report generation

---

## 📞 SUPPORT & RESOURCES

### Documentation Links
- Django: https://docs.djangoproject.com/
- DRF: https://www.django-rest-framework.org/
- Celery: https://docs.celeryq.dev/
- Anthropic Claude: https://docs.anthropic.com/
- PostgreSQL: https://www.postgresql.org/docs/

### Common Issues & Solutions
1. **Celery not working** → Check Redis connection
2. **Image too large** → Adjust MAX_UPLOAD_SIZE
3. **LLM timeout** → Increase API timeout
4. **JSON parse error** → Check LLM response format
5. **Migration conflicts** → Reset migrations if needed

---

## ✨ FINAL NOTES

Bu loyihani qurish uchun barcha kerakli ma'lumotlar bu documentda mavjud. Har bir qism detalli tushuntirilgan va kod misollari berilgan.

**Agent uchun yo'riqnoma:**
1. Phase 1 dan boshlang (Backend Setup)
2. Har bir checkbox ni ketma-ket bajaring
3. Kod yozishda berilgan strukturaga amal qiling
4. Test yozishni unutmang
5. Documentation ni yangilab turing

**Good luck! 🚀**
