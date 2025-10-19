from django.contrib import admin

from .models import Agendamento, Cliente, Servico


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("nome", "telefone")
    search_fields = ("nome", "telefone")


@admin.register(Servico)
class ServicoAdmin(admin.ModelAdmin):
    list_display = ("nome", "preco", "duracao", "ativo")


@admin.register(Agendamento)
class AgendamentoAdmin(admin.ModelAdmin):
    list_display = ("cliente", "servico", "data", "hora", "status")
    list_filter = ("data", "status")
    search_fields = ("cliente__nome",)
