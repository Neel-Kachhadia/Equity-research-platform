"""
Redis cache client for AWS ElastiCache.
All failures are non-fatal - gracefully degrades to database queries.
"""

import json
import logging
from typing import Optional, Any, Dict
from functools import wraps

import redis
from redis.exceptions import RedisError, ConnectionError, TimeoutError

from core.config import settings

logger = logging.getLogger(__name__)

_redis_client: Optional[redis.Redis] = None


def _get_redis_client() -> Optional[redis.Redis]:
    global _redis_client
    
    if not settings.redis.enabled:
        return None
    
    if _redis_client is None:
        try:
            _redis_client = redis.Redis.from_url(
                settings.redis.url,
                ssl=settings.redis.ssl,
                ssl_cert_reqs=None,
                decode_responses=True,
                socket_timeout=2,
                socket_connect_timeout=2,
                retry_on_timeout=True,
                health_check_interval=30
            )
            
            _redis_client.ping()
            logger.info("Redis client connected successfully")
            
        except (RedisError, ConnectionError, TimeoutError) as e:
            logger.warning(f"Redis connection failed (cache disabled): {e}")
            _redis_client = None
        except Exception as e:
            logger.error(f"Unexpected Redis error: {e}")
            _redis_client = None
    
    return _redis_client


def cache_get(key: str) -> Optional[Any]:
    client = _get_redis_client()
    if not client:
        return None
    
    try:
        value = client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.debug(f"Cache get failed for {key}: {e}")
        return None


def cache_set(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    client = _get_redis_client()
    if not client:
        return False
    
    try:
        ttl = ttl or settings.redis.ttl_default
        serialized = json.dumps(value, default=str)
        client.setex(key, ttl, serialized)
        return True
    except Exception as e:
        logger.debug(f"Cache set failed for {key}: {e}")
        return False


def cache_delete(key: str) -> bool:
    client = _get_redis_client()
    if not client:
        return False
    
    try:
        client.delete(key)
        return True
    except Exception as e:
        logger.debug(f"Cache delete failed for {key}: {e}")
        return False


def cache_invalidate_pattern(pattern: str) -> int:
    client = _get_redis_client()
    if not client:
        return 0
    
    try:
        keys = client.keys(pattern)
        if keys:
            return client.delete(*keys)
        return 0
    except Exception as e:
        logger.debug(f"Cache pattern delete failed for {pattern}: {e}")
        return 0


def build_document_key(doc_id: int) -> str:
    return f"doc:{doc_id}"


def build_company_docs_key(company_id: str, year: Optional[str] = None) -> str:
    if year:
        return f"docs:{company_id}:{year}"
    return f"docs:{company_id}:all"


def build_alpha_score_key(company_id: str, year: str, metric: str) -> str:
    return f"alpha:{company_id}:{year}:{metric}"


def build_company_alpha_key(company_id: str, year: str) -> str:
    return f"alpha:{company_id}:{year}:*"


def cached(ttl: Optional[int] = None, key_prefix: str = "cache"):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            key_parts = [key_prefix, func.__name__]
            key_parts.extend([str(arg) for arg in args])
            key_parts.extend([f"{k}={v}" for k, v in sorted(kwargs.items())])
            cache_key = ":".join(key_parts)
            
            cached_value = cache_get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit: {cache_key}")
                return cached_value
            
            logger.debug(f"Cache miss: {cache_key}")
            result = func(*args, **kwargs)
            
            if result is not None:
                cache_set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator


def cache_alpha_score(company_id: str, year: str, metric: str, score: float) -> bool:
    key = build_alpha_score_key(company_id, year, metric)
    return cache_set(key, score, settings.redis.ttl_alpha_scores)


def get_cached_alpha_score(company_id: str, year: str, metric: str) -> Optional[float]:
    return cache_get(build_alpha_score_key(company_id, year, metric))


def get_cached_company_alphas(company_id: str, year: str) -> Dict[str, float]:
    client = _get_redis_client()
    if not client:
        return {}
    
    try:
        pattern = build_company_alpha_key(company_id, year)
        keys = client.keys(pattern)
        
        result = {}
        for key in keys:
            metric = key.split(":")[-1]
            value = cache_get(key)
            if value is not None:
                result[metric] = value
        
        return result
    except Exception as e:
        logger.debug(f"Failed to get company alphas: {e}")
        return {}


def invalidate_company_cache(company_id: str, year: Optional[str] = None) -> int:
    pattern = f"*:{company_id}:*" if year is None else f"*:{company_id}:{year}:*"
    return cache_invalidate_pattern(pattern)
    #s