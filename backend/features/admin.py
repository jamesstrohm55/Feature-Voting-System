from django.contrib import admin

from .models import FeatureRequest, Vote


@admin.register(FeatureRequest)
class FeatureRequestAdmin(admin.ModelAdmin):
    list_display = ["title", "author", "status", "vote_count", "created_at"]
    list_editable = ["status"]
    readonly_fields = ["id", "vote_count", "created_at", "updated_at"]


@admin.register(Vote)
class VoteAdmin(admin.ModelAdmin):
    list_display = ["user", "feature_request", "created_at"]
    readonly_fields = ["id", "created_at"]
