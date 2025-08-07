from functools import lru_cache
from odoo.tools import config
import redis


@lru_cache()
def xink_redis_client():
    redis_host = config.get('redis_host', 'localhost')
    redis_port = int(config.get('redis_port', 6379))
    return redis.StrictRedis(host=redis_host, port=redis_port, db=0, decode_responses=True)
