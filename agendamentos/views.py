from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
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
    # Busca o agendamento ou retorna um erro 404 se não existir.
    # A busca exige que o agendamento pertença ao usuário logado (request.user),
    # isso impede que um usuário cancele o agendamento de outro.
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, cliente=request.user)

    # Muda o status do agendamento para 'cancelado'
    agendamento.status = 'cancelado'
    agendamento.save()

    # Envia uma mensagem de sucesso para o usuário
    messages.success(request, 'Agendamento cancelado com sucesso!')

    # Redireciona o usuário de volta para a lista de agendamentos
    return redirect('meus_agendamentos')

def api_horarios_disponiveis(request):
    data_str = request.GET.get('data')
    servico_id = request.GET.get('servico_id')

    # Se não tiver data ou serviço, retorna lista vazia
    if not data_str or not servico_id:
        return JsonResponse({'horarios': []})

    try:
        servico = Servico.objects.get(id=servico_id)
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (Servico.DoesNotExist, ValueError):
        return JsonResponse({'horarios': []})

    # Definições de expediente
    horario_inicio_trabalho = time(9, 0)
    horario_fim_trabalho = time(18, 0)
    intervalo_minutos = 30 # Nosso passo para verificar os slots

    agendamentos_no_dia = Agendamento.objects.filter(data=data)
    horarios_disponiveis = []

    slot_atual = datetime.combine(data, horario_inicio_trabalho)
    duracao_servico = timedelta(minutes=servico.duracao)

    while slot_atual.time() < horario_fim_trabalho:
        slot_fim = slot_atual + duracao_servico

        # O slot só é válido se terminar dentro do expediente
        if slot_fim.time() > horario_fim_trabalho:
            break

        slot_disponivel = True

        # Itera nos agendamentos existentes para checar conflito
        for agendamento_existente in agendamentos_no_dia:
            inicio_existente = datetime.combine(data, agendamento_existente.hora)
            duracao_existente = timedelta(minutes=agendamento_existente.servico.duracao)
            fim_existente = inicio_existente + duracao_existente

            # Verifica sobreposição (se o início de um é antes do fim do outro, E vice-versa)
            if slot_atual < fim_existente and inicio_existente < slot_fim:
                slot_disponivel = False
                break

        if slot_disponivel:
            horarios_disponiveis.append(slot_atual.strftime('%H:%M'))

        slot_atual += timedelta(minutes=intervalo_minutos)

    return JsonResponse({'horarios': horarios_disponiveis})

@staff_member_required(login_url='login')
def painel_barbeiro(request):
    hoje = date.today()

    # Busca agendamentos de hoje que NÃO estejam cancelados ou concluídos
    agendamentos_de_hoje = Agendamento.objects.filter(
        data=hoje,
        status__in=['pendente', 'confirmado']
    ).order_by('hora')

    context = {
        'agendamentos': agendamentos_de_hoje,
        'hoje': hoje,
    }
    return render(request, 'agendamentos/painel_barbeiro.html', context)