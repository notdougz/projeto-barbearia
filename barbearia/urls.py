from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("agendamentos.urls")),
    # Evitar 404 ruidosos para ícones quando ainda não há arquivos reais
    # Retorna 200 OK com conteúdo vazio para evitar 404 nos logs
    path("favicon.ico", lambda request: HttpResponse(b"", content_type="image/x-icon")),
    path("favicon.svg", lambda request: HttpResponse(b"", content_type="image/svg+xml")),
    path("apple-touch-icon.png", lambda request: HttpResponse(b"", content_type="image/png")),
    path("apple-touch-icon-precomposed.png", lambda request: HttpResponse(b"", content_type="image/png")),
    path("apple-touch-icon-120x120.png", lambda request: HttpResponse(b"", content_type="image/png")),
    path("apple-touch-icon-120x120-precomposed.png", lambda request: HttpResponse(b"", content_type="image/png")),
]

# Servir arquivos estáticos
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
