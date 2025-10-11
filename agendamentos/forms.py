from django import forms
from .models import Cliente, Agendamento, Servico

class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ['nome', 'telefone', 'endereco', 'observacoes']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome completo'}),
            'telefone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '+5511999999999'}),
            'endereco': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Endereço completo (rua, número, bairro, cidade)...'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre o cliente...'}),
        }

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['cliente', 'servico', 'data', 'hora', 'observacoes']
        widgets = {
            'cliente': forms.HiddenInput(),
            'servico': forms.Select(attrs={'class': 'form-control'}),
            'data': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora': forms.Select(attrs={'class': 'form-control', 'id': 'hora-select'}),
            'observacoes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Observações sobre o agendamento...'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas serviços ativos
        self.fields['servico'].queryset = Servico.objects.filter(ativo=True)
        self.fields['servico'].empty_label = "Selecione um serviço..."
        # Configurar campo de cliente
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nome')
        self.fields['cliente'].empty_label = "Selecione um cliente"
        self.fields['cliente'].label = "Cliente"
        
        # Gerar opções de horário de 10 em 10 minutos
        from datetime import time
        horarios = []
        for hora in range(6, 22):  # Das 6h às 21h50
            for minuto in [0, 10, 20, 30, 40, 50]:
                horario = time(hora, minuto)
                horarios.append((horario.strftime('%H:%M'), horario.strftime('%H:%M')))
        
        self.fields['hora'].choices = [('', 'Selecione um horário...')] + horarios

class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ['nome', 'descricao', 'duracao', 'preco', 'ativo']
        widgets = {
            'nome': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nome do serviço'}),
            'descricao': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Descrição do serviço...'}),
            'duracao': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '30', 'min': '1', 'max': '300'}),
            'preco': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '25.00', 'step': '0.01', 'min': '0'}),
            'ativo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nome': 'Nome do Serviço',
            'descricao': 'Descrição',
            'duracao': 'Duração (minutos)',
            'preco': 'Preço (R$)',
            'ativo': 'Serviço ativo',
        }
        help_texts = {
            'duracao': 'Duração estimada do serviço em minutos',
            'preco': 'Preço do serviço em reais',
            'ativo': 'Desmarque para desativar o serviço temporariamente',
        }

class PrevisaoChegadaForm(forms.Form):
    """Formulário para capturar a previsão de chegada"""
    previsao_minutos = forms.IntegerField(
        label="Previsão de Chegada (minutos)",
        min_value=1,
        max_value=180,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ex: 15',
            'min': '1',
            'max': '180'
        }),
        help_text="Quantos minutos até chegar ao cliente?"
    )