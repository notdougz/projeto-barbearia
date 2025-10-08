from django import forms
from .models import Cliente, Agendamento

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'observacoes']

class AgendamentoForm(forms.ModelForm):
    # Campo para selecionar cliente existente
    cliente_existente = forms.ModelChoiceField(
        queryset=Cliente.objects.all().order_by('nome'),
        required=False,
        label="Cliente Fiel"
    )
    # Campos para um novo cliente (cliente de passagem)
    nome_novo_cliente = forms.CharField(required=False, label="Nome (Cliente Novo/Avulso)")
    
    class Meta:
        model = Agendamento
        fields = ['cliente_existente', 'nome_novo_cliente', 'servico', 'data', 'hora', 'observacoes']
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }