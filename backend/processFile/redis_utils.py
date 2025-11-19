# catalog/redis_utils.py
import logging
import json
from django_redis import get_redis_connection
from django.conf import settings

logger = logging.getLogger(__name__)

# use the cache 'default' which you configured in settings (redis://127.0.0.1:6379/1)
def _redis():
    try:
        return get_redis_connection("default")
    except Exception as e:
        # fallback: try CELERY_RESULT_BACKEND URL if defined
        try:
            from redis import Redis
            url = getattr(settings, "CELERY_RESULT_BACKEND", None)
            if url:
                r = Redis.from_url(url, decode_responses=True)
                logger.warning("Using fallback Redis via CELERY_RESULT_BACKEND")
                return r
        except Exception as e2:
            logger.exception("Fallback redis connection failed: %s", e2)
        logger.exception("Unable to get redis connection: %s", e)
        raise

def set_progress(job_id, processed=None, total=None, status=None, error=None):
    key = f"upload:{job_id}"
    payload = {}
    if processed is not None:
        payload['processed'] = str(int(processed))
    if total is not None:
        payload['total'] = str(int(total))
    if status is not None:
        payload['status'] = str(status)
    if error is not None:
        payload['error'] = str(error)
    if not payload:
        return False
    try:
        r = _redis()
        # use hset mapping for convenience
        r.hset(key, mapping=payload)
        # set expiration so keys don't live forever
        r.expire(key, 60*60*24)
        logger.debug("Set progress %s => %s", key, payload)
        return True
    except Exception as e:
        logger.exception("Failed to set progress for %s: %s", key, e)
        return False

def get_progress(job_id):
    key = f"upload:{job_id}"
    try:
        r = _redis()
        data = r.hgetall(key)
        # ensure keys are strings, not bytes
        return {k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in (data or {}).items()}
    except Exception as e:
        logger.exception("Failed to read progress for %s: %s", key, e)
        return {}
