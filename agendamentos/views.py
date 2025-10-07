from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.core.mail import send_mail
from django.http import JsonResponse
from datetime import date, datetime, time, timedelta
from .models import Servico, Agendamento, PerfilCliente
from .forms import RegistroComEmailForm, PerfilClienteForm, AgendamentoForm, UserForm

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
    try:
        perfil = request.user.perfil
    except PerfilCliente.DoesNotExist:
        return redirect('completar_perfil')

    if request.method == 'POST':
        user_form = UserForm(request.POST, instance=request.user)
        perfil_form = PerfilClienteForm(request.POST, instance=perfil)
        if user_form.is_valid() and perfil_form.is_valid():
            user_form.save()
            perfil_form.save()
            messages.success(request, 'Perfil atualizado com sucesso!')
            return redirect('meu_perfil')
    else:
        user_form = UserForm(instance=request.user)
        perfil_form = PerfilClienteForm(instance=perfil)
    context = {'user_form': user_form, 'perfil_form': perfil_form}
    return render(request, 'agendamentos/meu_perfil.html', context)

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
        form = AgendamentoForm(request.POST)
        if form.is_valid():
            agendamento = form.save(commit=False)
            agendamento.cliente = request.user
            agendamento.status = 'pendente'
            agendamento.save()
            messages.success(request, 'Agendamento realizado com sucesso!')
            return redirect('meus_agendamentos')
    else:
        form = AgendamentoForm()
    return render(request, 'agendamentos/agendar.html', {'form': form})

@login_required
def cancelar_agendamento(request, agendamento_id):
    agendamento = get_object_or_404(Agendamento, id=agendamento_id, cliente=request.user)
    agendamento.status = 'cancelado'
    agendamento.save()
    messages.success(request, 'Agendamento cancelado com sucesso!')
    return redirect('meus_agendamentos')

# --- PAINEL E CALENDÁRIO PARA O BARBEIRO ---

@staff_member_required(login_url='login')
def painel_barbeiro(request):
    data_selecionada_str = request.GET.get('data')
    if data_selecionada_str:
        data_selecionada = datetime.strptime(data_selecionada_str, '%Y-%m-%d').date()
    else:
        data_selecionada = date.today()
    agendamentos = Agendamento.objects.filter(
        data=data_selecionada,
        status__in=['pendente', 'confirmado']
    ).order_by('hora').select_related('cliente', 'servico', 'cliente__perfil')
    context = {'agendamentos': agendamentos, 'data_selecionada': data_selecionada}
    return render(request, 'agendamentos/painel_barbeiro.html', context)

@staff_member_required(login_url='login')
def calendario_view(request):
    return render(request, 'agendamentos/calendario.html')

@staff_member_required(login_url='login')
def confirmar_agendamento(request, agendamento_id):
    if request.method == 'POST':
        agendamento = get_object_or_404(Agendamento, id=agendamento_id)
        agendamento.status = 'confirmado'
        agendamento.save()
        messages.success(request, 'Agendamento confirmado!')
    return redirect('painel_barbeiro')

@staff_member_required(login_url='login')
def concluir_agendamento(request, agendamento_id):
    if request.method == 'POST':
        agendamento = get_object_or_404(Agendamento, id=agendamento_id)
        agendamento.status = 'concluido'
        agendamento.save()
        messages.success(request, 'Agendamento concluído!')
    return redirect('painel_barbeiro')

# --- APIs PARA O FRONT-END ---

def api_horarios_disponiveis(request):
    data_str = request.GET.get('data')
    servico_id = request.GET.get('servico_id')
    if not data_str or not servico_id:
        return JsonResponse({'horarios': []})
    try:
        servico = Servico.objects.get(id=servico_id)
        data = datetime.strptime(data_str, '%Y-%m-%d').date()
    except (Servico.DoesNotExist, ValueError):
        return JsonResponse({'horarios': []})
    # ... (resto da lógica da API de horários)
    horario_inicio_trabalho = time(9, 0)
    horario_fim_trabalho = time(18, 0)
    intervalo_minutos = 30
    agendamentos_no_dia = Agendamento.objects.filter(data=data).exclude(status='cancelado')
    horarios_disponiveis = []
    slot_atual = datetime.combine(data, horario_inicio_trabalho)
    duracao_servico = timedelta(minutes=servico.duracao)

    while slot_atual.time() < horario_fim_trabalho:
        slot_fim = slot_atual + duracao_servico
        if slot_fim.time() > horario_fim_trabalho and slot_fim.date() == slot_atual.date() :
            break

        slot_disponivel = True
        for agendamento_existente in agendamentos_no_dia:
            inicio_existente = datetime.combine(data, agendamento_existente.hora)
            duracao_existente = timedelta(minutes=agendamento_existente.servico.duracao)
            fim_existente = inicio_existente + duracao_existente
            if slot_atual < fim_existente and inicio_existente < slot_fim:
                slot_disponivel = False
                break
        if slot_disponivel:
            horarios_disponiveis.append(slot_atual.strftime('%H:%M'))
        slot_atual += timedelta(minutes=intervalo_minutos)
    return JsonResponse({'horarios': horarios_disponiveis})


def api_todos_agendamentos(request):
    todos_agendamentos = Agendamento.objects.exclude(status='cancelado').select_related('cliente', 'servico', 'cliente__perfil')
    eventos = []
    for agendamento in todos_agendamentos:
        inicio = datetime.combine(agendamento.data, agendamento.hora)
        fim = inicio + timedelta(minutes=agendamento.servico.duracao)
        nome_cliente = f"{agendamento.cliente.first_name} {agendamento.cliente.last_name}".strip() or agendamento.cliente.username

        try:
            perfil = agendamento.cliente.perfil
            endereco = f"{perfil.rua}, {perfil.numero} - {perfil.bairro}"
        except PerfilCliente.DoesNotExist:
            endereco = "Endereço não cadastrado."

        cor = '#5a5a5a'
        if agendamento.status == 'confirmado':
            cor = '#28a745'
        elif agendamento.status == 'concluido':
            cor = '#007bff'

        eventos.append({
            'title': f"{inicio.strftime('%H:%M')} - {fim.strftime('%H:%M')} / {nome_cliente}",
            'start': inicio.isoformat(),
            'end': fim.isoformat(),
            'color': cor,
            'extendedProps': {
                'servico_nome': agendamento.servico.nome,
                'servico_preco': f'R$ {agendamento.servico.preco}',
                'cliente_nome': nome_cliente,
                'observacoes': agendamento.observacoes or 'Nenhuma observação.',
                'endereco': endereco,
            }
        })
    return JsonResponse(eventos, safe=False)