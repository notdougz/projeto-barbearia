import re

from django import forms

from .models import Agendamento, Cliente, Servico


def normalizar_telefone_brasileiro(telefone):
    """
    Normaliza números de telefone brasileiros para o formato internacional +55XXXXXXXXXXX
    Adiciona automaticamente o +55 se não estiver presente.

    Aceita vários formatos de entrada:
    - 11999999999 -> +5511999999999
    - (11) 99999-9999 -> +5511999999999
    - +5511999999999 -> +5511999999999 (já está correto)
    - 5511999999999 -> +5511999999999
    - +55 11 99999-9999 -> +5511999999999

    Args:
        telefone (str): Número de telefone em qualquer formato

    Returns:
        str: Número no formato +55XXXXXXXXXXX ou None se inválido
    """
    if not telefone:
        return None

    # Remove todos os caracteres não numéricos, exceto +
    telefone_limpo = re.sub(r"[^\d+]", "", telefone.strip())

    # Se já começa com +55, retorna como está (após limpar caracteres extras)
    if telefone_limpo.startswith("+55"):
        telefone_limpo = "+55" + telefone_limpo[3:].replace("+", "")
        # Verifica se tem tamanho válido após o +55 (10 ou 11 dígitos)
        if len(telefone_limpo) in [13, 14]:  # +55 + 10 ou 11 dígitos
            return telefone_limpo

    # Se começa com 55 (sem o +), adiciona o +
    if telefone_limpo.startswith("55") and len(telefone_limpo) >= 12:
        telefone_limpo = "+" + telefone_limpo
        # Verifica se tem tamanho válido
        if len(telefone_limpo) in [13, 14]:
            return telefone_limpo

    # Se não tem código do país, assume que é número brasileiro
    # Remove zeros à esquerda do DDD se houver
    telefone_limpo = telefone_limpo.lstrip("0")

    # Verifica se tem 10 ou 11 dígitos (DDD + número)
    if len(telefone_limpo) == 10 or len(telefone_limpo) == 11:
        return "+55" + telefone_limpo

    # Se não couber em nenhum padrão, retorna None (inválido)
    return None


class ClienteForm(forms.ModelForm):
    class Meta:
        model = Cliente
        fields = ["nome", "telefone", "endereco", "observacoes"]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nome completo"}
            ),
            "telefone": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "11999999999 ou +5511999999999",
                    "help_text": "Digite o número com ou sem +55. O sistema adicionará automaticamente.",
                }
            ),
            "endereco": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Endereço completo (rua, número, bairro, cidade)...",
                }
            ),
            "observacoes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observações sobre o cliente...",
                }
            ),
        }

    def clean_telefone(self):
        """Normaliza e valida o telefone brasileiro, adicionando +55 automaticamente"""
        telefone = self.cleaned_data.get("telefone")

        if telefone:  # Só valida se telefone foi informado
            # Normaliza o telefone para formato internacional (+55XXXXXXXXXXX)
            telefone_normalizado = normalizar_telefone_brasileiro(telefone)

            if not telefone_normalizado:
                raise forms.ValidationError(
                    "Número de telefone inválido. Digite o número com DDD (ex: 11999999999 ou +5511999999999)"
                )

            # Verifica se já existe outro cliente com este telefone normalizado
            # Exclui o próprio cliente caso seja uma edição
            queryset = Cliente.objects.filter(telefone=telefone_normalizado)
            if self.instance.pk:  # Se estiver editando, exclui o próprio registro
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                cliente_existente = queryset.first()
                raise forms.ValidationError(
                    f"Já existe um cliente cadastrado com este telefone: {cliente_existente.nome}"
                )

            # Retorna o telefone normalizado (com +55)
            return telefone_normalizado

        return telefone

    def clean_nome(self):
        """Valida se o nome já existe para outro cliente"""
        nome = self.cleaned_data.get("nome")

        if nome:
            # Remove espaços extras e compara em minúsculas
            nome_limpo = nome.strip()

            # Verifica se já existe outro cliente com este nome (case-insensitive)
            queryset = Cliente.objects.filter(nome__iexact=nome_limpo)
            if self.instance.pk:  # Se estiver editando, exclui o próprio registro
                queryset = queryset.exclude(pk=self.instance.pk)

            if queryset.exists():
                cliente_existente = queryset.first()
                raise forms.ValidationError(
                    f"Já existe um cliente cadastrado com este nome: {cliente_existente.nome}"
                )

        return nome


class AgendamentoForm(forms.ModelForm):
    class Meta:
        model = Agendamento
        fields = ["cliente", "servico", "data", "hora", "observacoes"]
        widgets = {
            "cliente": forms.HiddenInput(),
            "servico": forms.Select(attrs={"class": "form-control"}),
            "data": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "hora": forms.Select(attrs={"class": "form-control", "id": "hora-select"}),
            "observacoes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Observações sobre o agendamento...",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas serviços ativos
        self.fields["servico"].queryset = Servico.objects.filter(ativo=True)
        self.fields["servico"].empty_label = "Selecione um serviço..."
        # Configurar campo de cliente
        self.fields["cliente"].queryset = Cliente.objects.all().order_by("nome")
        self.fields["cliente"].empty_label = "Selecione um cliente"
        self.fields["cliente"].label = "Cliente"

        # Gerar opções de horário de 10 em 10 minutos
        from datetime import time

        horarios = []
        for hora in range(6, 22):  # Das 6h às 21h50
            for minuto in [0, 10, 20, 30, 40, 50]:
                horario = time(hora, minuto)
                horarios.append((horario.strftime("%H:%M"), horario.strftime("%H:%M")))

        self.fields["hora"].choices = [("", "Selecione um horário...")] + horarios


class ServicoForm(forms.ModelForm):
    class Meta:
        model = Servico
        fields = ["nome", "descricao", "duracao", "preco", "ativo"]
        widgets = {
            "nome": forms.TextInput(
                attrs={"class": "form-control", "placeholder": "Nome do serviço"}
            ),
            "descricao": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Descrição do serviço...",
                }
            ),
            "duracao": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "30",
                    "min": "1",
                    "max": "300",
                }
            ),
            "preco": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "25.00",
                    "step": "0.01",
                    "min": "0",
                }
            ),
            "ativo": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
        labels = {
            "nome": "Nome do Serviço",
            "descricao": "Descrição",
            "duracao": "Duração (minutos)",
            "preco": "Preço (R$)",
            "ativo": "Serviço ativo",
        }
        help_texts = {
            "duracao": "Duração estimada do serviço em minutos",
            "preco": "Preço do serviço em reais",
            "ativo": "Desmarque para desativar o serviço temporariamente",
        }


class PrevisaoChegadaForm(forms.Form):
    """Formulário para capturar a previsão de chegada"""

    previsao_minutos = forms.IntegerField(
        label="Previsão de Chegada (minutos)",
        min_value=1,
        max_value=180,
        widget=forms.NumberInput(
            attrs={
                "class": "form-control",
                "placeholder": "Ex: 15",
                "min": "1",
                "max": "180",
            }
        ),
        help_text="Quantos minutos até chegar ao cliente?",
    )
