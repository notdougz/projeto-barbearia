from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Agendamento, Cliente, Servico
from datetime import date, datetime
from .forms import ClienteForm, AgendamentoForm

@login_required
def painel_barbeiro(request):
    # Verificar se foi selecionada uma data específica
    data_selecionada = request.GET.get('data')
    if data_selecionada:
        try:
            data_selecionada = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
        except ValueError:
            data_selecionada = date.today()
    else:
        data_selecionada = date.today()
    
    agendamentos = Agendamento.objects.filter(data=data_selecionada).order_by('hora')
    
    context = {
        'agendamentos': agendamentos,
        'data_selecionada': data_selecionada,
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

@login_required
def agendar(request):
    """
    View para criar novos agendamentos.
    O barbeiro deve selecionar um cliente existente.
    """
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.status = 'confirmado'
            agendamento.save()
            
            messages.success(request, f'Agendamento criado com sucesso para {agendamento.cliente.nome}!')
            return redirect('painel_barbeiro')
    else:
        form = AgendamentoForm()
    
    return render(request, 'agendamentos/agendar.html', {'form': form})

@login_required
def editar_agendamento(request, pk):
    """Editar um agendamento existente"""
    agendamento = get_object_or_404(Agendamento, pk=pk)
    
    if request.method == 'POST':
        form = AgendamentoForm(request.POST, instance=agendamento)
        if form.is_valid():
            form.save()
            messages.success(request, 'Agendamento atualizado com sucesso!')
            return redirect('painel_barbeiro')
    else:
        form = AgendamentoForm(instance=agendamento)
    
    return render(request, 'agendamentos/agendar.html', {'form': form, 'agendamento': agendamento})

@login_required
def deletar_agendamento(request, pk):
    """Deletar um agendamento"""
    agendamento = get_object_or_404(Agendamento, pk=pk)
    
    if request.method == 'POST':
        agendamento.delete()
        messages.success(request, 'Agendamento deletado com sucesso!')
        return redirect('painel_barbeiro')
    
    return render(request, 'agendamentos/agendamento_confirm_delete.html', {'agendamento': agendamento})

@login_required
def confirmar_agendamento(request, pk):
    """Confirmar um agendamento"""
    agendamento = get_object_or_404(Agendamento, pk=pk)
    agendamento.status = 'confirmado'
    agendamento.save()
    messages.success(request, f'Agendamento de {agendamento.cliente.nome} confirmado!')
    return redirect('painel_barbeiro')

@login_required
def concluir_agendamento(request, pk):
    """Marcar um agendamento como concluído"""
    agendamento = get_object_or_404(Agendamento, pk=pk)
    agendamento.status = 'concluido'
    agendamento.save()
    messages.success(request, f'Agendamento de {agendamento.cliente.nome} marcado como concluído!')
    return redirect('painel_barbeiro')