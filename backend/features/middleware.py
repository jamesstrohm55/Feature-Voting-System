from django.http import JsonResponse

from .models import Voter


class SessionIdMiddleware:
    """
    Resolves X-Session-Id header to a Voter instance on request.voter.
    Auto-creates the Voter on first sight.
    Only applies to /api/ routes.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        session_id = request.headers.get("X-Session-Id")
        if not session_id:
            return JsonResponse(
                {"detail": "X-Session-Id header is required."},
                status=401,
            )

        voter, _ = Voter.objects.get_or_create(session_id=session_id)
        request.voter = voter

        return self.get_response(request)
