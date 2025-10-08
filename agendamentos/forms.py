from django import forms
from .models import Cliente, Agendamento
from datetime import datetime, timedelta

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'observacoes']

class AgendamentoForm(forms.ModelForm):
    # Campo para selecionar cliente existente ou adicionar um novo
    cliente_existente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by('nome'),
        required=False,
        label="Cliente Fiel"
    )
    # Campos para um novo cliente
    nome_novo_cliente = forms.CharField(required=False, label="Nome (Novo Cliente)")
    telefone_novo_cliente = forms.CharField(required=False, label="Telefone (Novo Cliente)")

    class Meta:
        model = Agendamento
        fields = ['servico', 'data', 'hora', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }