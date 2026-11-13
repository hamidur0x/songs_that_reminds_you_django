from django.contrib import admin
from django.urls import include, path, re_path

from book.views import serve_media

urlpatterns = [
    path("admin/", admin.site.urls),
    # Range-aware media streaming (needed for audio seeking, esp. iOS Safari)
    re_path(r"^media/(?P<path>.+)$", serve_media, name="media"),
    path("", include("book.urls")),
]
