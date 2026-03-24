from rest_framework.throttling import SimpleRateThrottle

# NOTE: These throttles use Django's default LocMemCache, which is per-process.
# In production with multiple workers (gunicorn, uvicorn), replace with Redis
# via django-redis so throttle state is shared across all processes:
#   CACHES = { "default": { "BACKEND": "django_redis.cache.RedisCache", ... } }


class _UserThrottle(SimpleRateThrottle):
    """Base throttle that keys on the authenticated user's ID."""

    def get_cache_key(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return None
        return self.cache_format % {
            "scope": self.scope,
            "ident": request.user.pk,
        }


class FeatureCreateThrottle(_UserThrottle):
    scope = "feature_create"
    rate = "5/hour"


class VoteThrottle(_UserThrottle):
    scope = "vote"
    rate = "30/hour"
