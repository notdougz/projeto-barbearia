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

        # Verifica se já existe um agendamento nesse mesmo dia e hora
        if data and hora:
            if Agendamento.objects.filter(data=data, hora=hora).exists():
                # Se existir, levanta um erro de validação
                raise forms.ValidationError("Este horário já está ocupado. Por favor, escolha outro.")
        
        return cleaned_data