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
)
from .throttles import FeatureCreateThrottle, VoteThrottle

_THROTTLED_RESPONSE = Response(
    {"detail": "Rate limit exceeded. Try again later."},
    status=status.HTTP_429_TOO_MANY_REQUESTS,
)


@api_view(["GET", "POST"])
def feature_list_create(request):
    """GET: list all features ranked by votes. POST: create a new feature."""
    if request.method == "GET":
        # Explicit ranking: highest votes first, then newest. The db_index on
        # vote_count lets Postgres satisfy this without a filesort.
        features = (
            FeatureRequest.objects
            .select_related("author")
        )

        search = request.query_params.get("search", "").strip()
        if search:
            features = features.filter(
                Q(title__icontains=search) | Q(description__icontains=search)
            )

        features = features.order_by("-vote_count", "-created_at")

        # Single query to resolve has_voted for every card — avoids N+1.
        voter_voted_feature_ids = set(
            Vote.objects.filter(voter=request.voter).values_list(
                "feature_request_id", flat=True
            )
        )

        serializer = FeatureRequestListSerializer(
            features,
            many=True,
            context={
                "voter": request.voter,
                "voter_voted_feature_ids": voter_voted_feature_ids,
            },
        )
        return Response(serializer.data)

    # POST — rate-limited to 5/hour per session.
    throttle = FeatureCreateThrottle()
    if not throttle.allow_request(request, None):
        return _THROTTLED_RESPONSE

    serializer = FeatureRequestCreateSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    feature = serializer.save(author=request.voter)

    # Return the full read representation
    read_serializer = FeatureRequestListSerializer(
        feature,
        context={
            "voter": request.voter,
            "voter_voted_feature_ids": set(),
        },
    )
    return Response(read_serializer.data, status=status.HTTP_201_CREATED)


@api_view(["POST", "DELETE"])
@throttle_classes([VoteThrottle])
def feature_vote(request, feature_id):
    """POST: upvote a feature. DELETE: remove upvote."""
    feature = get_object_or_404(FeatureRequest, id=feature_id)

    if request.method == "POST":
        # Cannot vote on own feature
        if feature.author_id == request.voter.id:
            return Response(
                {"detail": "You cannot vote on your own feature request."},
                status=status.HTTP_403_FORBIDDEN,
            )

        try:
            with transaction.atomic():
                Vote.objects.create(voter=request.voter, feature_request=feature)
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

    # DELETE
    try:
        with transaction.atomic():
            vote = Vote.objects.get(voter=request.voter, feature_request=feature)
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
