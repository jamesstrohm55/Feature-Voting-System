from django.urls import path

from . import views

urlpatterns = [
    path("features/", views.feature_list_create, name="feature-list-create"),
    path("features/<uuid:feature_id>/vote/", views.feature_vote, name="feature-vote"),
]
