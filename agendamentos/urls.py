from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('registro/', views.registro, name='registro'),
    path('completar-perfil/', views.completar_perfil, name='completar_perfil'),
    path('meu-perfil/', views.meu_perfil, name='meu_perfil'),
    path('meus-agendamentos/', views.meus_agendamentos, name='meus_agendamentos'),
    path('agendar/', views.agendar, name='agendar'),
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),
    path('api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
]
