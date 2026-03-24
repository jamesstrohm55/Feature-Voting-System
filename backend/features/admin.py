from django.contrib import admin

from .models import FeatureRequest, Vote, Voter


@admin.register(Voter)
class VoterAdmin(admin.ModelAdmin):
    list_display = ["session_id", "created_at"]
    readonly_fields = ["id", "created_at"]


@admin.register(FeatureRequest)
class FeatureRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "vote_count", "created_at"]
    readonly_fields = ["id", "vote_count", "created_at", "updated_at"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["voter", "feature_request", "created_at"]
    readonly_fields = ["id", "created_at"]
