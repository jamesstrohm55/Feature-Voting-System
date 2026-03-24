from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.authtoken.models import Token


def _token_response(user, token):
    return {"token": token.key, "user_id": user.pk, "username": user.username}


@api_view(["POST"])
@permission_classes([AllowAny])
def register(request):
    """Create a new user and return an auth token."""
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""

    if not username or not password:
        return Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(password) < 6:
        return Response(
            {"detail": "Password must be at least 6 characters."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        return Response(
            {"detail": "Username already taken."},
            status=status.HTTP_409_CONFLICT,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response(_token_response(user, token), status=status.HTTP_201_CREATED)


@api_view(["POST"])
@permission_classes([AllowAny])
def login(request):
    """Authenticate and return an auth token."""
    username = (request.data.get("username") or "").strip()
    password = request.data.get("password") or ""

    if not username or not password:
        return Response(
            {"detail": "Username and password are required."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = authenticate(username=username, password=password)
    if user is None:
        return Response(
            {"detail": "Invalid credentials."},
            status=status.HTTP_401_UNAUTHORIZED,
        )

    token, _ = Token.objects.get_or_create(user=user)
    return Response(_token_response(user, token), status=status.HTTP_200_OK)
