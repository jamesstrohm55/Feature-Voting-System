from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response

from .models import FeatureRequest, Vote
from .serializers import (
    FeatureRequestCreateSerializer,
    FeatureRequestListSerializer,
    FeatureStatusUpdateSerializer,
)
from .throttles import FeatureCreateThrottle, VoteThrottle

_THROTTLED_RESPONSE = Response(
    {"detail": "Rate limit exceeded. Try again later."},
    status=status.HTTP_429_TOO_MANY_REQUESTS,
)

_STAFF_ONLY = Response(
    {"detail": "Staff permission required."},
    status=status.HTTP_403_FORBIDDEN,
)


@api_view(["GET", "POST"])
def feature_list_create(request):
    """GET: list all features ranked by votes. POST: create a new feature."""
    if request.method == "GET":
        features = FeatureRequest.objects.select_related("author")

        search = request.query_params.get("search", "").strip()
        if search:
            features = features.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        # Pinned first, then highest votes, then newest.
        features = features.order_by("-is_pinned", "-vote_count", "-created_at")

        user_voted_feature_ids = set(
            Vote.objects.filter(user=request.user).values_list(
                "feature_request_id", flat=True
            )
        )

        serializer = FeatureRequestListSerializer(
            features,
            many=True,
            context={
                "user": request.user,
                "user_voted_feature_ids": user_voted_feature_ids,
            },
        )
        return Response(serializer.data)

    # POST — rate-limited to 5/hour per user.
    throttle = FeatureCreateThrottle()
    if not throttle.allow_request(request, None):
        return _THROTTLED_RESPONSE

    serializer = FeatureRequestCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    feature = serializer.save(author=request.user)

    read_serializer = FeatureRequestListSerializer(
        feature,
        context={
            "user": request.user,
            "user_voted_feature_ids": set(),
        },
    )
    return Response(read_serializer.data, status=status.HTTP_201_CREATED)


@api_view(["PATCH", "DELETE"])
def feature_detail(request, feature_id):
    """PATCH: update status (staff only). DELETE: delete feature (staff or owner)."""
    feature = get_object_or_404(FeatureRequest, id=feature_id)

    if request.method == "PATCH":
        if not request.user.is_staff:
            return _STAFF_ONLY

        serializer = FeatureStatusUpdateSerializer(feature, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        read_serializer = FeatureRequestListSerializer(
            feature,
            context={
                "user": request.user,
                "user_voted_feature_ids": set(),
            },
        )
        return Response(read_serializer.data)

    # DELETE — staff can delete any, regular users can only delete their own.
    if not request.user.is_staff and feature.author_id != request.user.id:
        return Response(
            {"detail": "You can only delete your own features."},
            status=status.HTTP_403_FORBIDDEN,
        )

    feature.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(["POST", "DELETE"])
@throttle_classes([VoteThrottle])
def feature_vote(request, feature_id):
    """POST: upvote a feature. DELETE: remove upvote."""
    feature = get_object_or_404(FeatureRequest, id=feature_id)

    if request.method == "POST":
        if feature.author_id == request.user.id:
            return Response(
                {"detail": "You cannot vote on your own feature request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with transaction.atomic():
                Vote.objects.create(user=request.user, feature_request=feature)
                FeatureRequest.objects.filter(id=feature.id).update(
                    vote_count=F("vote_count") + 1
                )
        except IntegrityError:
            return Response(
                {"detail": "You have already voted on this feature."},
                status=status.HTTP_409_CONFLICT,
            )

        feature.refresh_from_db()
        return Response(
            {"vote_count": feature.vote_count, "has_voted": True},
            status=status.HTTP_201_CREATED,
        )

    # DELETE — remove own vote
    try:
        with transaction.atomic():
            vote = Vote.objects.get(user=request.user, feature_request=feature)
            vote.delete()
            FeatureRequest.objects.filter(id=feature.id).update(
                vote_count=F("vote_count") - 1
            )
    except Vote.DoesNotExist:
        return Response(
            {"detail": "You have not voted on this feature."},
            status=status.HTTP_404_NOT_FOUND,
        )

    feature.refresh_from_db()
    return Response(
        {"vote_count": feature.vote_count, "has_voted": False},
        status=status.HTTP_200_OK,
    )


@api_view(["DELETE"])
def vote_admin_delete(request, feature_id, vote_id):
    """Staff-only: remove any vote by ID."""
    if not request.user.is_staff:
        return _STAFF_ONLY

    feature = get_object_or_404(FeatureRequest, id=feature_id)
    vote = get_object_or_404(Vote, id=vote_id, feature_request=feature)

    with transaction.atomic():
        vote.delete()
        FeatureRequest.objects.filter(id=feature.id).update(
            vote_count=F("vote_count") - 1
        )

    feature.refresh_from_db()
    return Response(
        {"vote_count": feature.vote_count},
        status=status.HTTP_200_OK,
    )


@api_view(["PATCH"])
def feature_pin(request, feature_id):
    """Staff-only: toggle is_pinned."""
    if not request.user.is_staff:
        return _STAFF_ONLY

    feature = get_object_or_404(FeatureRequest, id=feature_id)
    feature.is_pinned = not feature.is_pinned
    feature.save(update_fields=["is_pinned", "updated_at"])

    return Response({"is_pinned": feature.is_pinned})
