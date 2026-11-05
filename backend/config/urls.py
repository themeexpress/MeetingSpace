from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.permissions import IsAdminUser

from accounts.views import AdminUserDetailView, AdminUserListCreateView
from config.views import health

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", health, name="health"),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("bookings.urls")),
    path(
        "api/admin/users/",
        AdminUserListCreateView.as_view(),
        name="admin-user-list",
    ),
    path(
        "api/admin/users/<int:pk>/",
        AdminUserDetailView.as_view(),
        name="admin-user-detail",
    ),
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[IsAdminUser]),
        name="schema",
    ),
    path(
        "api/docs/",
        SpectacularSwaggerView.as_view(permission_classes=[IsAdminUser], url_name="schema"),
        name="docs",
    ),
]
