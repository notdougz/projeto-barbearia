from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.painel_barbeiro, name='home'),
    path('login/', auth_views.LoginView.as_view(template_name='agendamentos/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    # PAINEL PRINCIPAL
    path('painel/', views.painel_barbeiro, name='painel_barbeiro'),
    path('agendamentos-mensais/', views.agendamentos_mensais, name='agendamentos_mensais'),
    
    # FINANCEIRO
    path('financeiro/', views.financeiro, name='financeiro'),
    path('financeiro/alterar-pagamento/<int:pk>/', views.alterar_status_pagamento, name='alterar_status_pagamento'),
    
    # AGENDAMENTOS
    path('agendar/', views.agendar, name='agendar'),
    path('agendar/editar/<int:pk>/', views.editar_agendamento, name='editar_agendamento'),
    path('agendar/deletar/<int:pk>/', views.deletar_agendamento, name='deletar_agendamento'),
    path('agendar/confirmar/<int:pk>/', views.confirmar_agendamento, name='confirmar_agendamento'),
    path('agendar/a-caminho/<int:pk>/', views.on_the_way_agendamento, name='on_the_way_agendamento'),
    path('agendar/concluir/<int:pk>/', views.concluir_agendamento, name='concluir_agendamento'),

    # CLIENTES
    path('clientes/', views.lista_clientes, name='lista_clientes'),
    path('clientes/novo/', views.criar_cliente, name='criar_cliente'),
    path('clientes/editar/<int:pk>/', views.editar_cliente, name='editar_cliente'),
    path('clientes/deletar/<int:pk>/', views.deletar_cliente, name='deletar_cliente'),
]