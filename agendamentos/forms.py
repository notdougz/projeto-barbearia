from datetime import timedelta
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import PerfilCliente, Agendamento

class RegistroComEmailForm(UserCreationForm):
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(required=True, label='Nome', max_length=100)
    
    class Meta:
        model = User
        fields = ['first_name', 'email', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.username = self.cleaned_data['email']  # Usa email como username
        user.first_name = self.cleaned_data['first_name']
        if commit:
            user.save()
        return user

class PerfilClienteForm(forms.ModelForm):
    class Meta:
        model = PerfilCliente
        fields = ['telefone', 'cep', 'rua', 'numero', 'complemento', 'bairro', 'cidade', 'estado']
        labels = {
            'telefone': 'Telefone',
            'cep': 'CEP',
            'rua': 'Rua',
            'numero': 'Número',
            'complemento': 'Complemento (Opcional)',
            'bairro': 'Bairro',
            'cidade': 'Cidade',
            'estado': 'Estado (UF)',
        }

class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ['servico', 'data', 'hora']
        # Adiciona "widgets" para que o HTML use inputs de data e hora
        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'hora': forms.TimeInput(attrs={'type': 'time'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        data = cleaned_data.get("data")
        hora = cleaned_data.get("hora")
        servico = cleaned_data.get("servico")

        if data and hora and servico:
            # Combina data e hora para criar um objeto datetime de início
            horario_inicio = data.strftime('%Y-%m-%d') + ' ' + hora.strftime('%H:%M:%S')
            
            # Calcula o horário de término baseado na duração do serviço
            duracao = timedelta(minutes=servico.duracao)
            horario_fim = (hora.to_datetime() + duracao).time()

            # Verifica se algum agendamento existente se sobrepõe ao novo horário
            # A lógica é: um agendamento conflita se ele começa antes do nosso terminar E termina depois do nosso começar
            agendamentos_conflitantes = Agendamento.objects.filter(
                data=data,
                hora__lt=horario_fim, 
                hora__gte=(hora.to_datetime() - timedelta(minutes=servico.duracao)).time()
            )

            if agendamentos_conflitantes.exists():
                raise forms.ValidationError("Este período de tempo está em conflito com outro agendamento.")

        return cleaned_data