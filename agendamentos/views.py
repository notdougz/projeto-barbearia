from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Agendamento, Cliente, Servico
from datetime import date, datetime, timedelta
from .forms import ClienteForm, AgendamentoForm, PrevisaoChegadaForm, ServicoForm
from .smsdev_service import smsdev_service

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
            
            # Envia SMS para o cliente (usando SMSDev)
            sms_result = smsdev_service.enviar_barbeiro_a_caminho(agendamento, previsao_minutos)
            
            if sms_result['sucesso']:
                messages.success(request, f'Status alterado para "À caminho" e SMS enviado! Previsão: {previsao_minutos} minutos.')
            else:
                messages.warning(request, f'Status alterado para "À caminho", mas falha no SMS: {sms_result["erro"]}')
            
            # Log do resultado do SMS
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"SMS enviado para {agendamento.cliente.nome}: {sms_result}")
            
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

@login_required
def financeiro(request):
    """Visualizar relatório financeiro com status de pagamento dos clientes"""
    # Obter data selecionada
    data_selecionada = request.GET.get('data')
    if data_selecionada:
        try:
            data_selecionada = datetime.strptime(data_selecionada, '%Y-%m-%d').date()
        except ValueError:
            data_selecionada = date.today()
    else:
        data_selecionada = date.today()
    
    # Obter filtro de status de pagamento
    filtro_pagamento = request.GET.get('filtro', 'todos')  # todos, pendente, pago, visao_geral
    
    # Buscar agendamentos do dia
    agendamentos = Agendamento.objects.filter(data=data_selecionada).order_by('hora')
    
    # Aplicar filtro de pagamento
    if filtro_pagamento == 'pendente':
        agendamentos = agendamentos.filter(status_pagamento='pendente')
    elif filtro_pagamento == 'pago':
        agendamentos = agendamentos.filter(status_pagamento='pago')
    # Se for 'todos' ou 'visao_geral', não precisa filtrar
    
    # Calcular estatísticas do dia
    todos_agendamentos = Agendamento.objects.filter(data=data_selecionada)
    total_pendente = todos_agendamentos.filter(status_pagamento='pendente').count()
    total_pago = todos_agendamentos.filter(status_pagamento='pago').count()
    total_geral = todos_agendamentos.count()
    
    # Calcular valores monetários do dia
    valor_pendente = sum([a.servico.preco for a in todos_agendamentos.filter(status_pagamento='pendente')])
    valor_recebido = sum([a.servico.preco for a in todos_agendamentos.filter(status_pagamento='pago')])
    valor_total = valor_pendente + valor_recebido
    
    # Calcular estatísticas mensais baseadas na data selecionada
    mes_atual = data_selecionada.month
    ano_atual = data_selecionada.year
    data_inicio_mes = datetime(ano_atual, mes_atual, 1).date()
    if mes_atual == 12:
        data_fim_mes = datetime(ano_atual + 1, 1, 1).date()
    else:
        data_fim_mes = datetime(ano_atual, mes_atual + 1, 1).date()
    
    agendamentos_mes = Agendamento.objects.filter(
        data__gte=data_inicio_mes,
        data__lt=data_fim_mes
    )
    
    total_mes = sum([a.servico.preco for a in agendamentos_mes])
    recebido_mes = sum([a.servico.preco for a in agendamentos_mes.filter(status_pagamento='pago')])
    pendente_mes = sum([a.servico.preco for a in agendamentos_mes.filter(status_pagamento='pendente')])
    pagos_mes = agendamentos_mes.filter(status_pagamento='pago').count()
    pendentes_mes = agendamentos_mes.filter(status_pagamento='pendente').count()
    agendamentos_mes_count = agendamentos_mes.count()
    
    # Taxa de recebimento mensal
    taxa_recebimento_mes = (recebido_mes / total_mes * 100) if total_mes > 0 else 0
    
    # Calcular estatísticas anuais
    data_inicio_ano = datetime(ano_atual, 1, 1).date()
    data_fim_ano = datetime(ano_atual + 1, 1, 1).date()
    
    agendamentos_ano = Agendamento.objects.filter(
        data__gte=data_inicio_ano,
        data__lt=data_fim_ano
    )
    
    total_ano = sum([a.servico.preco for a in agendamentos_ano])
    recebido_ano = sum([a.servico.preco for a in agendamentos_ano.filter(status_pagamento='pago')])
    pendente_ano = sum([a.servico.preco for a in agendamentos_ano.filter(status_pagamento='pendente')])
    pagos_ano = agendamentos_ano.filter(status_pagamento='pago').count()
    pendentes_ano = agendamentos_ano.filter(status_pagamento='pendente').count()
    agendamentos_ano_count = agendamentos_ano.count()
    
    # Taxa de recebimento anual
    taxa_recebimento_ano = (recebido_ano / total_ano * 100) if total_ano > 0 else 0
    
    # Percentuais para gráfico
    percentual_recebido_mes = (recebido_mes / total_mes * 100) if total_mes > 0 else 0
    percentual_pendente_mes = (pendente_mes / total_mes * 100) if total_mes > 0 else 0
    
    # Buscar cortes detalhados mensais
    cortes_pagos_mes = agendamentos_mes.filter(status_pagamento='pago').order_by('-data', 'hora')
    cortes_pendentes_mes = agendamentos_mes.filter(status_pagamento='pendente').order_by('-data', 'hora')
    
    # Buscar cortes detalhados anuais
    cortes_pagos_ano = agendamentos_ano.filter(status_pagamento='pago').order_by('-data', 'hora')
    cortes_pendentes_ano = agendamentos_ano.filter(status_pagamento='pendente').order_by('-data', 'hora')
    
    context = {
        'agendamentos': agendamentos,
        'data_selecionada': data_selecionada,
        'filtro_pagamento': filtro_pagamento,
        'total_pendente': total_pendente,
        'total_pago': total_pago,
        'total_geral': total_geral,
        'valor_pendente': valor_pendente,
        'valor_recebido': valor_recebido,
        'valor_total': valor_total,
        # Estatísticas mensais
        'total_mes': total_mes,
        'recebido_mes': recebido_mes,
        'pendente_mes': pendente_mes,
        'pagos_mes': pagos_mes,
        'pendentes_mes': pendentes_mes,
        'agendamentos_mes': agendamentos_mes_count,
        'taxa_recebimento_mes': taxa_recebimento_mes,
        # Estatísticas anuais
        'total_ano': total_ano,
        'recebido_ano': recebido_ano,
        'pendente_ano': pendente_ano,
        'pagos_ano': pagos_ano,
        'pendentes_ano': pendentes_ano,
        'agendamentos_ano': agendamentos_ano_count,
        'taxa_recebimento_ano': taxa_recebimento_ano,
        # Percentuais para gráfico
        'percentual_recebido_mes': percentual_recebido_mes,
        'percentual_pendente_mes': percentual_pendente_mes,
        # Cortes detalhados
        'cortes_pagos_mes': cortes_pagos_mes,
        'cortes_pendentes_mes': cortes_pendentes_mes,
        'cortes_pagos_ano': cortes_pagos_ano,
        'cortes_pendentes_ano': cortes_pendentes_ano,
    }
    
    return render(request, 'agendamentos/financeiro.html', context)

@login_required
def alterar_status_pagamento(request, pk):
    """Alternar status de pagamento de um agendamento"""
    agendamento = get_object_or_404(Agendamento, pk=pk)
    
    # Alternar entre pendente e pago
    if agendamento.status_pagamento == 'pendente':
        agendamento.status_pagamento = 'pago'
        messages.success(request, f'Pagamento de {agendamento.cliente.nome} marcado como PAGO!')
    else:
        agendamento.status_pagamento = 'pendente'
        messages.success(request, f'Pagamento de {agendamento.cliente.nome} marcado como PENDENTE!')
    
    agendamento.save()
    
    # Redirecionar de volta para a página financeiro mantendo a data
    return redirect(f"{request.META.get('HTTP_REFERER', 'financeiro')}")

# ===== GESTÃO DE SERVIÇOS =====

@login_required
def lista_servicos(request):
    """Listar todos os serviços"""
    servicos = Servico.objects.all().order_by('nome')
    return render(request, 'agendamentos/lista_servicos.html', {'servicos': servicos})

@login_required
def criar_servico(request):
    """Criar um novo serviço"""
    if request.method == 'POST':
        form = ServicoForm(request.POST)
        if form.is_valid():
            servico = form.save()
            messages.success(request, f'Serviço "{servico.nome}" criado com sucesso!')
            return redirect('lista_servicos')
    else:
        form = ServicoForm()
    
    return render(request, 'agendamentos/servico_form.html', {
        'form': form, 
        'titulo': 'Novo Serviço',
        'botao_texto': 'Criar Serviço'
    })

@login_required
def editar_servico(request, pk):
    """Editar um serviço existente"""
    servico = get_object_or_404(Servico, pk=pk)
    
    if request.method == 'POST':
        form = ServicoForm(request.POST, instance=servico)
        if form.is_valid():
            servico = form.save()
            messages.success(request, f'Serviço "{servico.nome}" atualizado com sucesso!')
            return redirect('lista_servicos')
    else:
        form = ServicoForm(instance=servico)
    
    return render(request, 'agendamentos/servico_form.html', {
        'form': form, 
        'servico': servico,
        'titulo': f'Editar Serviço: {servico.nome}',
        'botao_texto': 'Salvar Alterações'
    })

@login_required
def deletar_servico(request, pk):
    """Deletar um serviço"""
    servico = get_object_or_404(Servico, pk=pk)
    
    # Verificar se o serviço está sendo usado em agendamentos
    agendamentos_count = Agendamento.objects.filter(servico=servico).count()
    
    if request.method == 'POST':
        if agendamentos_count > 0:
            messages.error(request, f'Não é possível deletar o serviço "{servico.nome}" pois ele está sendo usado em {agendamentos_count} agendamento(s).')
            return redirect('lista_servicos')
        
        nome_servico = servico.nome
        servico.delete()
        messages.success(request, f'Serviço "{nome_servico}" deletado com sucesso!')
        return redirect('lista_servicos')
    
    return render(request, 'agendamentos/servico_confirm_delete.html', {
        'servico': servico,
        'agendamentos_count': agendamentos_count
    })