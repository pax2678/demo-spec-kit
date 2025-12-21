import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta
import logging
from config.settings import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis-based caching service for dashboard data."""
    
    def __init__(self):
        """Initialize Redis connection."""
        try:
            self.redis_client = redis.Redis.from_url(
                settings.REDIS_URL,
                password=settings.REDIS_PASSWORD,
                decode_responses=False,  # We'll handle encoding manually
                socket_keepalive=True,
                socket_keepalive_options={},
                health_check_interval=30
            )
            # Test connection
            self.redis_client.ping()
            logger.info("Redis connection established successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.redis_client = None
    
    def _serialize(self, value: Any) -> bytes:
        """Serialize value for Redis storage."""
        try:
            # Try JSON first for simple types
            if isinstance(value, (str, int, float, bool, list, dict)):
                return json.dumps(value).encode('utf-8')
            else:
                # Use pickle for complex objects
                return pickle.dumps(value)
        except Exception as e:
            logger.error(f"Failed to serialize value: {e}")
            return pickle.dumps(value)
    
    def _deserialize(self, data: bytes) -> Any:
        """Deserialize value from Redis storage."""
        try:
            # Try JSON first
            try:
                return json.loads(data.decode('utf-8'))
            except (json.JSONDecodeError, UnicodeDecodeError):
                # Fall back to pickle
                return pickle.loads(data)
        except Exception as e:
            logger.error(f"Failed to deserialize value: {e}")
            return None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        if not self.redis_client:
            return None
        
        try:
            data = self.redis_client.get(key)
            if data is None:
                return None
            return self._deserialize(data)
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set value in cache with optional TTL."""
        if not self.redis_client:
            return False
        
        try:
            serialized = self._serialize(value)
            
            if ttl is None:
                return self.redis_client.set(key, serialized)
            elif isinstance(ttl, timedelta):
                return self.redis_client.setex(key, int(ttl.total_seconds()), serialized)
            else:
                return self.redis_client.setex(key, ttl, serialized)
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.delete(key) > 0
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in cache."""
        if not self.redis_client:
            return False
        
        try:
            return self.redis_client.exists(key) > 0
        except Exception as e:
            logger.error(f"Cache exists error for key {key}: {e}")
            return False
    
    def expire(self, key: str, ttl: Union[int, timedelta]) -> bool:
        """Set expiration time for key."""
        if not self.redis_client:
            return False
        
        try:
            if isinstance(ttl, timedelta):
                ttl = int(ttl.total_seconds())
            return self.redis_client.expire(key, ttl)
        except Exception as e:
            logger.error(f"Cache expire error for key {key}: {e}")
            return False
    
    def get_many(self, keys: list) -> dict:
        """Get multiple keys from cache."""
        if not self.redis_client or not keys:
            return {}
        
        try:
            values = self.redis_client.mget(keys)
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    result[key] = self._deserialize(value)
            return result
        except Exception as e:
            logger.error(f"Cache get_many error: {e}")
            return {}
    
    def set_many(self, mapping: dict, ttl: Optional[Union[int, timedelta]] = None) -> bool:
        """Set multiple key-value pairs."""
        if not self.redis_client or not mapping:
            return False
        
        try:
            pipeline = self.redis_client.pipeline()
            for key, value in mapping.items():
                serialized = self._serialize(value)
                if ttl is None:
                    pipeline.set(key, serialized)
                elif isinstance(ttl, timedelta):
                    pipeline.setex(key, int(ttl.total_seconds()), serialized)
                else:
                    pipeline.setex(key, ttl, serialized)
            
            pipeline.execute()
            return True
        except Exception as e:
            logger.error(f"Cache set_many error: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern."""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete_pattern error for pattern {pattern}: {e}")
            return 0
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment value at key."""
        if not self.redis_client:
            return None
        
        try:
            return self.redis_client.incr(key, amount)
        except Exception as e:
            logger.error(f"Cache increment error for key {key}: {e}")
            return None
    
    def get_cache_info(self) -> Optional[dict]:
        """Get cache information and statistics."""
        if not self.redis_client:
            return None
        
        try:
            info = self.redis_client.info()
            return {
                "used_memory": info.get("used_memory_human"),
                "connected_clients": info.get("connected_clients"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds")
            }
        except Exception as e:
            logger.error(f"Failed to get cache info: {e}")
            return None


# Dashboard-specific cache keys and TTLs
class CacheKeys:
    """Cache key patterns for dashboard data."""
    
    # Metrics cache (5 minutes TTL)
    METRICS_PATTERN = "dashboard:metrics:{metric_type}:{timeframe}"
    METRICS_TTL = 300
    
    # User preferences cache (1 hour TTL)
    USER_PREFERENCES = "user:preferences:{user_id}"
    USER_PREFERENCES_TTL = 3600
    
    # Session cache (24 hours TTL)
    USER_SESSION = "session:{session_id}"
    USER_SESSION_TTL = 86400
    
    # Widget configuration cache (1 hour TTL)
    WIDGET_CONFIG = "widget:config:{widget_id}"
    WIDGET_CONFIG_TTL = 3600
    
    # Dashboard layout cache (1 hour TTL)
    DASHBOARD_LAYOUT = "dashboard:layout:{user_id}"
    DASHBOARD_LAYOUT_TTL = 3600
    
    # Rate limiting
    RATE_LIMIT = "rate_limit:{identifier}"
    RATE_LIMIT_TTL = 60


# Global cache service instance
cache_service = CacheService()


def get_cache_service() -> CacheService:
    """Get the global cache service instance."""
    return cache_service