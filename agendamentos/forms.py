from datetime import datetime, timedelta
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
            # Combina a data e a hora para criar um objeto datetime completo
            horario_inicio = datetime.combine(data, hora)
            duracao = timedelta(minutes=servico.duracao)
            horario_fim = horario_inicio + duracao

            # Pega todos os agendamentos no dia selecionado para verificar conflitos
            agendamentos_no_dia = Agendamento.objects.filter(data=data)

            # Se estivermos editando um agendamento, devemos excluí-lo da verificação
            if self.instance.pk:
                agendamentos_no_dia = agendamentos_no_dia.exclude(pk=self.instance.pk)

            # Itera sobre os agendamentos existentes para checar sobreposição
            for agendamento_existente in agendamentos_no_dia:
                inicio_existente = datetime.combine(
                    agendamento_existente.data, agendamento_existente.hora
                )
                duracao_existente = timedelta(
                    minutes=agendamento_existente.servico.duracao
                )
                fim_existente = inicio_existente + duracao_existente

                # A condição de sobreposição: se o início de um é antes do fim do outro, E vice-versa
                if horario_inicio < fim_existente and inicio_existente < horario_fim:
                    raise forms.ValidationError(
                        f"Este horário conflita com um agendamento existente das "
                        f"{inicio_existente.strftime('%H:%M')} às {fim_existente.strftime('%H:%M')}."
                    )

        return cleaned_data