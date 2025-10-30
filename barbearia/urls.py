from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("agendamentos.urls")),
    # Evitar 404 ruidosos para ícones quando ainda não há arquivos reais
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("apple-touch-icon.png", lambda request: HttpResponse(status=204)),
    path("apple-touch-icon-precomposed.png", lambda request: HttpResponse(status=204)),
    path("apple-touch-icon-120x120.png", lambda request: HttpResponse(status=204)),
    path("apple-touch-icon-120x120-precomposed.png", lambda request: HttpResponse(status=204)),
]

# Servir arquivos estáticos
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
