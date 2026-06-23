from django.contrib import admin
from django.http import FileResponse, Http404
from django.urls import include, path, re_path

from pathlib import Path

FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend_dist"


def serve_frontend_asset(request, path):
    file_path = (FRONTEND_DIST / "assets" / path).resolve()
    assets_root = (FRONTEND_DIST / "assets").resolve()
    if not str(file_path).startswith(str(assets_root)) or not file_path.is_file():
        raise Http404("Asset not found")
    return FileResponse(file_path.open("rb"))


def serve_frontend_app(request, path=""):
    index_file = FRONTEND_DIST / "index.html"
    if not index_file.is_file():
        raise Http404("Frontend build not found")
    return FileResponse(index_file.open("rb"), content_type="text/html; charset=utf-8")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("monitoring.urls")),
    re_path(r"^assets/(?P<path>.*)$", serve_frontend_asset),
    re_path(r"^(?:login|dashboard)?/?$", serve_frontend_app),
    re_path(r"^(?!api/|admin/|assets/).*$", serve_frontend_app),
]
