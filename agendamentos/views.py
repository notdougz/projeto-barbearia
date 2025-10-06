from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.core.mail import send_mail
from django.http import JsonResponse
from datetime import date, datetime, time, timedelta
from .models import Servico, Agendamento, PerfilCliente
from .forms import RegistroComEmailForm, PerfilClienteForm, AgendamentoForm

def home(request):
    return render(request, 'agendamentos/home.html')

def registro(request):
    if request.method == 'POST':
        form = RegistroComEmailForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Cadastro realizado! Complete seu perfil.')
            return redirect('completar_perfil')
    else:
        form = RegistroComEmailForm()
    return render(request, 'agendamentos/registro.html', {'form': form})

@login_required
def completar_perfil(request):
    if hasattr(request.user, 'perfil'):
        return redirect('meu_perfil')
    
    if request.method == 'POST':
        form = PerfilClienteForm(request.POST)
        if form.is_valid():
            perfil = form.save(commit=False)
            perfil.user = request.user
            perfil.save()
            messages.success(request, 'Perfil completado com sucesso!')
            return redirect('home')
    else:
        form = PerfilClienteForm()
    
    return render(request, 'agendamentos/completar_perfil.html', {'form': form})

@login_required
def meu_perfil(request):
    perfil = request.user.perfil
    
    if request.method == 'POST':
        form = PerfilClienteForm(request.POST, instance=perfil)
        if form.is_valid():
            form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('meu_perfil')
    else:
        form = PerfilClienteForm(instance=perfil)
    
    return render(request, 'agendamentos/meu_perfil.html', {'form': form, 'perfil': perfil})

@login_required
def meus_agendamentos(request):
    agendamentos = Agendamento.objects.filter(cliente=request.user).order_by('-data', '-hora')
    return render(request, 'agendamentos/meus_agendamentos.html', {'agendamentos': agendamentos})

@login_required
def agendar(request):
    if not hasattr(request.user, 'perfil'):
        messages.warning(request, 'Complete seu perfil antes de agendar.')
        return redirect('completar_perfil')
    
    if request.method == 'POST':
        # 1. Cria o formulário com os dados que o usuário enviou
        form = AgendamentoForm(request.POST)
        # 2. Verifica se os dados são válidos (aqui ele roda nosso método 'clean')
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.cliente = request.user
            agendamento.status = 'pendente'
            agendamento.save()
            
            messages.success(request, 'Agendamento realizado com sucesso!')
            return redirect('meus_agendamentos')
    else:
        # 3. Se não for um POST, cria um formulário vazio
        form = AgendamentoForm()
    
    # 4. Envia o formulário (preenchido com erros ou vazio) para o template
    return render(request, 'agendamentos/agendar.html', {'form': form})

def enviar_notificacao_agendamento(agendamento):
    # Email para o cliente
    send_mail(
        'Agendamento Confirmado - Barbearia',
        f'Seu agendamento de {agendamento.servico.nome} foi marcado para {agendamento.data} às {agendamento.hora}',
        'barbearia@exemplo.com',
        [agendamento.cliente.email],
    )
    
# Nova view para painel do barbeiro
@login_required
def painel_barbeiro(request):
    agendamentos_hoje = Agendamento.objects.filter(
        data=date.today(),
        status__in=['pendente', 'confirmado']
    ).order_by('hora')
    return render(request, 'agendamentos/painel_barbeiro.html', {
        'agendamentos': agendamentos_hoje
    })

@login_required 
def cancelar_agendamento(request, agendamento_id):
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, cliente=request.user)
    agendamento.status = 'cancelado'
    agendamento.save()
    messages.success(request, 'Agendamento cancelado com sucesso!')
    return redirect('meus_agendamentos')

def api_horarios_disponiveis(request):
    data_selecionada_str = request.GET.get('data')
    if not data_selecionada_str:
        return JsonResponse({'horarios': []})

    data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d').date()

    # Defina o horário de trabalho do barbeiro
    horario_inicio_trabalho = time(9, 0)   # 09:00
    horario_fim_trabalho = time(18, 0)    # 18:00
    intervalo_minutos = 30                # Intervalo de cada slot

    # Pega todos os agendamentos já existentes para o dia selecionado
    agendamentos_no_dia = Agendamento.objects.filter(data=data_selecionada)

    horarios_disponiveis = []

    # Começa no início do expediente
    slot_atual = datetime.combine(data_selecionada, horario_inicio_trabalho)

    # Itera de 30 em 30 minutos até o fim do expediente
    while slot_atual.time() < horario_fim_trabalho:
        horario_do_slot_str = slot_atual.strftime('%H:%M')

        slot_disponivel = True

        # Precisamos verificar a duração do serviço selecionado.
        # Por enquanto, vamos assumir uma duração padrão e checar conflito
        # (vamos refinar isso depois)

        # Lógica de verificação de conflito (simplificada para este passo)
        for agendamento in agendamentos_no_dia:
            inicio_existente = datetime.combine(data_selecionada, agendamento.hora)
            duracao_existente = timedelta(minutes=agendamento.servico.duracao)
            fim_existente = inicio_existente + duracao_existente

            # Verifica se o slot_atual está dentro de um agendamento existente
            if inicio_existente <= slot_atual < fim_existente:
                slot_disponivel = False
                break # Se encontrou conflito, não precisa checar outros

        if slot_disponivel:
            horarios_disponiveis.append(horario_do_slot_str)

        # Vai para o próximo slot
        slot_atual += timedelta(minutes=intervalo_minutos)

    return JsonResponse({'horarios': horarios_disponiveis})