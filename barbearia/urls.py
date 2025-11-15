from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
import os

def serve_favicon(request):
    """Serve o favicon SVG do diretório de arquivos estáticos"""
    favicon_path = os.path.join(settings.BASE_DIR, "agendamentos/static/agendamentos/favicon.svg")
    if os.path.exists(favicon_path):
        with open(favicon_path, "rb") as f:
            return HttpResponse(f.read(), content_type="image/svg+xml")
    return HttpResponse(b"", content_type="image/svg+xml")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("agendamentos.urls")),
    # Servir favicon real
    path("favicon.ico", serve_favicon),
    path("favicon.svg", serve_favicon),
    # Outros ícones (retornam 200 OK vazio)
    path("apple-touch-icon.png", lambda request: HttpResponse(b"", content_type="image/png")),
    path("apple-touch-icon-precomposed.png", lambda request: HttpResponse(b"", content_type="image/png")),
    path("apple-touch-icon-120x120.png", lambda request: HttpResponse(b"", content_type="image/png")),
    path("apple-touch-icon-120x120-precomposed.png", lambda request: HttpResponse(b"", content_type="image/png")),
]

# Servir arquivos estáticos
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
