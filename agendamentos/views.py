from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Cliente, Agendamento, Servico
from .forms import ClienteForm, AgendamentoForm
from datetime import date

@login_required
def painel_barbeiro(request):
    data_selecionada_str = request.GET.get('data')
    if data_selecionada_str:
        data_selecionada = date.fromisoformat(data_selecionada_str)
    else:
        data_selecionada = date.today()

    agendamentos = Agendamento.objects.filter(data=data_selecionada).order_by('hora')
    
    return render(request, 'agendamentos/painel_barbeiro.html', {
        'agendamentos': agendamentos,
        'data_selecionada': data_selecionada,
    })

@login_required
def agendar_para_cliente(request):
    if request.method == 'POST':
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            cliente = None
            # Verifica se um cliente existente foi selecionado
            if form.cleaned_data['cliente_existente']:
                cliente = form.cleaned_data['cliente_existente']
            # Se não, cria um novo cliente
            elif form.cleaned_data['nome_novo_cliente'] and form.cleaned_data['telefone_novo_cliente']:
                cliente, created = Cliente.objects.get_or_create(
                    telefone=form.cleaned_data['telefone_novo_cliente'],
                    defaults={'nome': form.cleaned_data['nome_novo_cliente']}
                )

            if cliente:
                agendamento = form.save(commit=False)
                agendamento.cliente = cliente
                agendamento.save()
                return redirect('home')
            else:
                form.add_error(None, "Você precisa selecionar um cliente existente ou preencher os dados de um novo cliente.")
    else:
        form = AgendamentoForm()
    
    return render(request, 'agendamentos/agendar_novo.html', {'form': form})