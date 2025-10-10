from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Agendamento, Cliente, Servico
from datetime import date, datetime, timedelta
from .forms import ClienteForm, AgendamentoForm, PrevisaoChegadaForm
from .services import NotificationService

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
def on_the_way_agendamento(request, pk):
    """Marcar um agendamento como 'À caminho' com previsão de chegada"""
    agendamento = get_object_or_404(Agendamento, pk=pk)
    
    if request.method == 'POST':
        form = PrevisaoChegadaForm(request.POST)
        if form.is_valid():
            previsao_minutos = form.cleaned_data['previsao_minutos']
            
            # Atualiza o agendamento
            agendamento.status = 'a_caminho'
            agendamento.previsao_chegada = previsao_minutos
            agendamento.save()
            
            # Envia notificação para o cliente
            success, message = NotificationService.notify_client_on_the_way(agendamento, previsao_minutos)
            
            if success:
                messages.success(request, f'Status alterado para "À caminho" e cliente notificado! Previsão: {previsao_minutos} minutos.')
            else:
                messages.warning(request, f'Status alterado para "À caminho", mas falha na notificação: {message}')
            
            return redirect('painel_barbeiro')
    else:
        form = PrevisaoChegadaForm()
    
    return render(request, 'agendamentos/previsao_chegada.html', {
        'agendamento': agendamento,
        'form': form
    })

@login_required
def concluir_agendamento(request, pk):
    """Marcar um agendamento como concluído"""
    agendamento = get_object_or_404(Agendamento, pk=pk)
    agendamento.status = 'concluido'
    agendamento.save()
    messages.success(request, f'Agendamento de {agendamento.cliente.nome} marcado como concluído!')
    return redirect('painel_barbeiro')

@login_required
def agendamentos_mensais(request):
    """Visualizar agendamentos do mês em formato de calendário"""
    # Obter parâmetros de data (mês/ano)
    ano = request.GET.get('ano', datetime.now().year)
    mes = request.GET.get('mes', datetime.now().month)
    
    try:
        ano = int(ano)
        mes = int(mes)
        data_inicio = datetime(ano, mes, 1).date()
        if mes == 12:
            data_fim = datetime(ano + 1, 1, 1).date()
        else:
            data_fim = datetime(ano, mes + 1, 1).date()
    except (ValueError, TypeError):
        # Se houver erro, usar mês atual
        hoje = datetime.now().date()
        data_inicio = datetime(hoje.year, hoje.month, 1).date()
        if hoje.month == 12:
            data_fim = datetime(hoje.year + 1, 1, 1).date()
        else:
            data_fim = datetime(hoje.year, hoje.month + 1, 1).date()
        ano = hoje.year
        mes = hoje.month
    
    # Buscar agendamentos do mês
    agendamentos = Agendamento.objects.filter(
        data__gte=data_inicio,
        data__lt=data_fim
    ).order_by('data', 'hora')
    
    # Organizar agendamentos por data
    agendamentos_por_data = {}
    for agendamento in agendamentos:
        data_str = agendamento.data.strftime('%Y-%m-%d')
        if data_str not in agendamentos_por_data:
            agendamentos_por_data[data_str] = []
        agendamentos_por_data[data_str].append(agendamento)
    
    # Calcular informações do calendário
    primeiro_dia = datetime(ano, mes, 1)
    ultimo_dia = datetime(ano, mes + 1, 1) - timedelta(days=1) if mes < 12 else datetime(ano + 1, 1, 1) - timedelta(days=1)
    
    # Gerar semanas do calendário
    calendar_weeks = []
    current_date = primeiro_dia - timedelta(days=primeiro_dia.weekday())  # Começar no domingo da primeira semana
    
    for week in range(6):  # Máximo 6 semanas
        week_days = []
        for day in range(7):  # 7 dias por semana
            day_date = current_date + timedelta(days=week * 7 + day)
            is_current_month = day_date.month == mes and day_date.year == ano
            is_today = day_date.date() == date.today()
            date_str = day_date.strftime('%Y-%m-%d')
            
            week_days.append({
                'day': day_date.day,
                'date': day_date.date(),
                'date_str': date_str,
                'is_current_month': is_current_month,
                'is_today': is_today,
            })
        
        calendar_weeks.append(week_days)
        
        # Parar se já cobrimos todo o mês e chegamos ao final
        if week_days[-1]['date'] >= ultimo_dia.date():
            break
    
    # Mês anterior e próximo
    mes_anterior = mes - 1 if mes > 1 else 12
    ano_anterior = ano if mes > 1 else ano - 1
    mes_proximo = mes + 1 if mes < 12 else 1
    ano_proximo = ano if mes < 12 else ano + 1
    
    # Nome do mês
    nomes_meses = [
        '', 'Janeiro', 'Fevereiro', 'Março', 'Abril', 'Maio', 'Junho',
        'Julho', 'Agosto', 'Setembro', 'Outubro', 'Novembro', 'Dezembro'
    ]
    
    # Estatísticas do mês
    total_agendamentos = len(agendamentos)
    concluidos = len([a for a in agendamentos if a.status == 'concluido'])
    pendentes = len([a for a in agendamentos if a.status in ['confirmado', 'a_caminho']])
    
    context = {
        'agendamentos': agendamentos,
        'agendamentos_por_data': agendamentos_por_data,
        'calendar_weeks': calendar_weeks,
        'ano': ano,
        'mes': mes,
        'mes_nome': nomes_meses[mes],
        'primeiro_dia': primeiro_dia,
        'ultimo_dia': ultimo_dia,
        'mes_anterior': mes_anterior,
        'ano_anterior': ano_anterior,
        'mes_proximo': mes_proximo,
        'ano_proximo': ano_proximo,
        'total_agendamentos': total_agendamentos,
        'concluidos': concluidos,
        'pendentes': pendentes,
    }
    
    return render(request, 'agendamentos/agendamentos_mensais.html', context)