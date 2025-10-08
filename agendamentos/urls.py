from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
<<<<<<< HEAD
    path('', views.painel_barbeiro, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('painel/', views.painel_barbeiro, name='painel_barbeiro'),
    path('agendar/', views.agendar, name='agendar'),

    # NOVAS URLs PARA CLIENTES (AGORA ESTÃO ATIVAS)
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/novo/', views.criar_cliente, name='criar_cliente'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/deletar/<int:pk>/', views.deletar_cliente, name='deletar_cliente'),
=======
    # A página inicial agora é o painel do barbeiro
    path('', views.painel_barbeiro, name='home'),
    
    # URLs de Autenticação para o barbeiro
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    
    # Página principal do barbeiro
    path('painel/', views.painel_barbeiro, name='painel_barbeiro'),
    
    # As outras URLs (clientes, agendar, calendario) serão adicionadas depois.
>>>>>>> 7b9e49f04d82b2b24ff1ad937110835770b250b8
]