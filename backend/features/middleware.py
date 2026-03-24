import re

from django.http import JsonResponse

from .models import Voter

# Accept UUID v4 (with or without hyphens) — matches crypto.randomUUID() output.
_SESSION_RE = re.compile(r"^[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}$", re.I)


class SessionIdMiddleware:
    """
    Maps the X-Session-Id header to a Voter row (auto-created on first request).
    Rejects malformed or missing session IDs before they hit any view.
    Only applies to /api/ routes; admin and static files pass through.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        # Let CORS preflight through — OPTIONS requests don't carry custom headers.
        if request.method == "OPTIONS":
            return self.get_response(request)

        session_id = (request.headers.get("X-Session-Id") or "").strip()

        if not session_id:
            return JsonResponse(
                {"detail": "X-Session-Id header is required."},
                status=401,
            )

        if not _SESSION_RE.match(session_id):
            return JsonResponse(
                {"detail": "X-Session-Id must be a valid UUID."},
                status=400,
            )

        voter, _ = Voter.objects.get_or_create(session_id=session_id)
        request.voter = voter

        return self.get_response(request)
