from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('agendamentos.urls')),
]

# Servir arquivos estáticos em produção
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
else:
    # Para produção, usar whitenoise
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
