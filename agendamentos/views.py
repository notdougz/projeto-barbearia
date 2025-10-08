from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import Agendamento
from datetime import date, datetime
from .forms import ClienteForm, AgendamentoForm
from .models import Cliente

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

@login_required
def lista_clientes(request):
    clientes = Cliente.objects.all().order_by('nome')
    return render(request, 'agendamentos/lista_clientes.html', {'clientes': clientes})

@login_required
def criar_cliente(request):
    if request.method == 'POST':
        form = ClienteForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm()
    return render(request, 'agendamentos/cliente_form.html', {'form': form, 'titulo': 'Novo Cliente'})

@login_required
def editar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        form = ClienteForm(request.POST, instance=cliente)
        if form.is_valid():
            form.save()
            return redirect('lista_clientes')
    else:
        form = ClienteForm(instance=cliente)
    return render(request, 'agendamentos/cliente_form.html', {'form': form, 'titulo': 'Editar Cliente'})

@login_required
def deletar_cliente(request, pk):
    cliente = get_object_or_404(Cliente, pk=pk)
    if request.method == 'POST':
        cliente.delete()
        return redirect('lista_clientes')
    return render(request, 'agendamentos/cliente_confirm_delete.html', {'cliente': cliente})