from django.urls import path

from . import auth_views, views

urlpatterns = [
    path("auth/register/", auth_views.register, name="auth-register"),
    path("auth/login/", auth_views.login, name="auth-login"),
    path("features/", views.feature_list_create, name="feature-list-create"),
    path("features/<uuid:feature_id>/vote/", views.feature_vote, name="feature-vote"),
]
