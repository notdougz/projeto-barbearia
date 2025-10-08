from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Agendamento
from datetime import date, datetime

@login_required
def home(request):
    # A home para um usuário logado é sempre o painel
    return redirect('painel_barbeiro')

@login_required
def painel_barbeiro(request):
    # Lógica simples para mostrar a agenda de hoje, que iremos expandir depois
    hoje = date.today()
    agendamentos = Agendamento.objects.filter(data=hoje).order_by('hora')
    
    context = {
        'agendamentos': agendamentos,
        'data_selecionada': hoje,
    }
    return render(request, 'agendamentos/painel_barbeiro.html', context)

# Vamos adicionar as outras views (agendar, clientes, calendário) aqui, passo a passo.