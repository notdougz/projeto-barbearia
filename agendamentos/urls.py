from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.painel_barbeiro, name='home'), # Painel agora é a home
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('painel/', views.painel_barbeiro, name='painel_barbeiro'),
    path('calendario/', views.calendario_view, name='calendario'),
    path('agendar/', views.agendar_para_cliente, name='agendar'), # Nova view de agendamento

    # URLs de Clientes
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/novo/', views.criar_cliente, name='criar_cliente'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),

    # APIs
    path('api/horarios-disponiveis/', views.api_horarios_disponiveis, name='api_horarios_disponiveis'),
    path('api/todos-agendamentos/', views.api_todos_agendamentos, name='api_todos_agendamentos'),
]