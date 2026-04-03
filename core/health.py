"""
Health check endpoints for monitoring and container orchestration.
"""
import time
import logging

from django.db import connection
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

logger = logging.getLogger(__name__)


@extend_schema(
    tags=['Health'],
    summary='Liveness probe',
    responses={200: {'type': 'object'}},
)
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])
def health_check(request):
    """
    Basic liveness probe.
    Returns 200 if the application is running.
    Used by: Docker HEALTHCHECK, Kubernetes livenessProbe, load balancers.
    """
    return Response({
        'status': 'healthy',
        'service': 'ai-art-evaluation',
    })


@extend_schema(
    tags=['Health'],
    summary='Readiness probe',
    responses={200: {'type': 'object'}, 503: {'type': 'object'}},
)
@api_view(['GET'])
@permission_classes([AllowAny])
@throttle_classes([])
def readiness_check(request):
    """
    Readiness probe — checks all dependencies.
    Returns 200 if all services are accessible, 503 otherwise.
    Used by: Kubernetes readinessProbe, deployment verification.

    Checks:
    - Database connection
    - Redis/Celery broker
    - Storage (S3 if enabled)
    """
    checks = {}
    all_ok = True

    # 1. Database check
    try:
        start = time.time()
        connection.ensure_connection()
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
        checks['database'] = {
            'status': 'ok',
            'latency_ms': round((time.time() - start) * 1000, 2),
        }
    except Exception as e:
        checks['database'] = {'status': 'error', 'message': str(e)}
        all_ok = False
        logger.error(f'Health check: DB connection failed: {e}')

    # 2. Redis / Celery broker check
    if getattr(settings, 'CELERY_TASK_ALWAYS_EAGER', False):
        checks['redis'] = {
            'status': 'skipped',
            'mode': 'eager',
        }
    else:
        try:
            start = time.time()
            from redis import Redis
            broker_url = getattr(settings, 'CELERY_BROKER_URL', 'redis://localhost:6379/0')
            redis_client = Redis.from_url(broker_url, socket_timeout=3)
            redis_client.ping()
            redis_client.close()
            checks['redis'] = {
                'status': 'ok',
                'latency_ms': round((time.time() - start) * 1000, 2),
            }
        except Exception as e:
            checks['redis'] = {'status': 'error', 'message': str(e)}
            all_ok = False
            logger.error(f'Health check: Redis connection failed: {e}')

    # 3. Storage check (S3 if enabled)
    use_s3 = getattr(settings, 'USE_S3', False)
    if use_s3:
        try:
            import boto3
            s3 = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1'),
                endpoint_url=getattr(settings, 'AWS_S3_ENDPOINT_URL', None),
            )
            s3.head_bucket(Bucket=settings.AWS_STORAGE_BUCKET_NAME)
            checks['storage'] = {'status': 'ok', 'type': 's3'}
        except Exception as e:
            checks['storage'] = {'status': 'error', 'message': str(e)}
            all_ok = False
            logger.error(f'Health check: S3 connection failed: {e}')
    else:
        checks['storage'] = {'status': 'ok', 'type': 'local'}

    status_code = 200 if all_ok else 503

    return Response({
        'status': 'ready' if all_ok else 'not_ready',
        'checks': checks,
    }, status=status_code)
