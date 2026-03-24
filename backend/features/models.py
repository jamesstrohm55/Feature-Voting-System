import uuid

from django.conf import settings
from django.db import models


class FeatureRequest(models.Model):
    """A user-submitted feature request."""

    class Status(models.TextChoices):
        UNDER_REVIEW = "under_review", "Under Review"
        PLANNED = "planned", "Planned"
        IN_PROGRESS = "in_progress", "In Progress"
        SHIPPED = "shipped", "Shipped"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=200)
    description = models.TextField()
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="feature_requests"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.UNDER_REVIEW,
        db_index=True,
    )
    is_pinned = models.BooleanField(default=False, db_index=True)
    vote_count = models.PositiveIntegerField(default=0, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-vote_count", "-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(vote_count__gte=0),
                name="vote_count_non_negative",
            ),
        ]

    def __str__(self):
        return self.title


class Vote(models.Model):
    """A single upvote from a user on a feature request."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="votes"
    )
    feature_request = models.ForeignKey(
        FeatureRequest, on_delete=models.CASCADE, related_name="votes"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["user", "feature_request"],
                name="unique_vote_per_user_per_feature",
            ),
        ]

    def __str__(self):
        return f"Vote({self.user} -> {self.feature_request})"
