from django.urls import path

from . import auth_views, views

urlpatterns = [
    path("auth/register/", auth_views.register, name="auth-register"),
    path("auth/login/", auth_views.login, name="auth-login"),
    path("features/", views.feature_list_create, name="feature-list-create"),
    path("features/<uuid:feature_id>/", views.feature_detail, name="feature-detail"),
    path("features/<uuid:feature_id>/vote/", views.feature_vote, name="feature-vote"),
    path("features/<uuid:feature_id>/vote/<uuid:vote_id>/", views.vote_admin_delete, name="vote-admin-delete"),
    path("features/<uuid:feature_id>/pin/", views.feature_pin, name="feature-pin"),
]
