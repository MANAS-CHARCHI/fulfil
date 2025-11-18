import json
from django_redis import get_redis_connection

redis = get_redis_connection('default')

def publish_progress(task_id, payload):
    r = get_redis_connection("default")
    r.publish(f"progress_{task_id}", json.dumps(payload))