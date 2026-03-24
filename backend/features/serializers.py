from rest_framework import serializers

from .models import FeatureRequest


class FeatureRequestListSerializer(serializers.ModelSerializer):
    """Read serializer for the feature list. Includes per-viewer computed fields."""

    author_username = serializers.CharField(source="author.username", read_only=True)
    has_voted = serializers.SerializerMethodField()
    is_own = serializers.SerializerMethodField()
    is_staff = serializers.SerializerMethodField()

    class Meta:
        model = FeatureRequest
        fields = [
            "id",
            "title",
            "description",
            "author_username",
            "status",
            "is_pinned",
            "vote_count",
            "has_voted",
            "is_own",
            "is_staff",
            "created_at",
        ]
        read_only_fields = fields

    def get_has_voted(self, obj):
        user = self.context.get("user")
        if not user:
            return False
        user_voted_ids = self.context.get("user_voted_feature_ids")
        if user_voted_ids is not None:
            return obj.id in user_voted_ids
        return obj.votes.filter(user=user).exists()

    def get_is_own(self, obj):
        user = self.context.get("user")
        if not user:
            return False
        return obj.author_id == user.id

    def get_is_staff(self, obj):
        user = self.context.get("user")
        if not user:
            return False
        return user.is_staff


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


class FeatureStatusUpdateSerializer(serializers.ModelSerializer):
    """Staff-only serializer for updating feature status."""

    class Meta:
        model = FeatureRequest
        fields = ["status"]
