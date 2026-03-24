from rest_framework.throttling import SimpleRateThrottle

# NOTE: These throttles use Django's default LocMemCache, which is per-process.
# In production with multiple workers (gunicorn, uvicorn), replace with Redis
# via django-redis so throttle state is shared across all processes:
#   CACHES = { "default": { "BACKEND": "django_redis.cache.RedisCache", ... } }


class _SessionThrottle(SimpleRateThrottle):
    """Base throttle that keys on X-Session-Id instead of IP address."""

    def get_cache_key(self, request, view):
        session_id = request.headers.get("X-Session-Id")
        if not session_id:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": session_id,
        }

    def throttle_failure(self):
        """Called by DRF internals — we override the exception in the view layer."""
        return False


class FeatureCreateThrottle(_SessionThrottle):
    scope = "feature_create"
    rate = "5/hour"


class VoteThrottle(_SessionThrottle):
    scope = "vote"
    rate = "30/hour"
