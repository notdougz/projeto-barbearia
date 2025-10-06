from django.contrib import admin
from .models import PerfilCliente, Servico, Agendamento

# Registrar os modelos no painel administrativo
@admin.register(PerfilCliente)
class PerfilClienteAdmin(admin.ModelAdmin):
    list_display = ['user', 'telefone', 'cidade', 'bairro']
    search_fields = ['user__first_name', 'user__last_name', 'telefone']

@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ['nome', 'preco', 'duracao', 'ativo']
    list_filter = ['ativo']
    search_fields = ['nome']

@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ['cliente', 'servico', 'data', 'hora', 'status']
    list_filter = ['status', 'data']
    search_fields = ['cliente__first_name', 'cliente__last_name']
    date_hierarchy = 'data'
