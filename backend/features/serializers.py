from rest_framework import serializers

from .models import FeatureRequest


class FeatureRequestListSerializer(serializers.ModelSerializer):
    """Read serializer for the feature list. Includes per-viewer computed fields."""

    author_session_id = serializers.CharField(source="author.session_id", read_only=True)
    has_voted = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()

    class Meta:
        model = FeatureRequest
        fields = [
            "id",
            "title",
            "description",
            "author_session_id",
            "vote_count",
            "has_voted",
            "is_own",
            "created_at",
        ]
        read_only_fields = fields

    def get_has_voted(self, obj):
        voter = self.context.get("voter")
        if not voter:
            return False
        # Use prefetched voter_vote_ids set if available
        voter_vote_ids = self.context.get("voter_voted_feature_ids")
        if voter_vote_ids is not None:
            return obj.id in voter_vote_ids
        return obj.votes.filter(voter=voter).exists()

    def get_is_own(self, obj):
        voter = self.context.get("voter")
        if not voter:
            return False
        return obj.author_id == voter.id


class FeatureRequestCreateSerializer(serializers.ModelSerializer):
    """Write serializer — accepts title and description only."""

    class Meta:
        model = FeatureRequest
        fields = ["title", "description"]

    def validate_title(self, value):
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters.")
        return value.strip()

    def validate_description(self, value):
        if len(value.strip()) < 10:
            raise serializers.ValidationError(
                "Description must be at least 10 characters."
            )
        return value.strip()
