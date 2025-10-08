from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    # A página inicial agora é o painel do barbeiro
    path('', views.painel_barbeiro, name='home'),
    
    # URLs de Autenticação para o barbeiro
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Página principal do barbeiro
    path('painel/', views.painel_barbeiro, name='painel_barbeiro'),
    
    # As outras URLs (clientes, agendar, calendario) serão adicionadas depois.
]