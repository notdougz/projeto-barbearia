from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from django.contrib import messages
from .models import Servico, Agendamento, PerfilCliente
from .forms import RegistroComEmailForm, PerfilClienteForm

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
    
    servicos = Servico.objects.filter(ativo=True)
    
    if request.method == 'POST':
        servico = Servico.objects.get(id=request.POST['servico'])
        Agendamento.objects.create(
            cliente=request.user,
            servico=servico,
            data=request.POST['data'],
            hora=request.POST['hora'],
            status='pendente'
        )
        messages.success(request, 'Agendamento realizado com sucesso!')
        return redirect('meus_agendamentos')
    
    return render(request, 'agendamentos/agendar.html', {'servicos': servicos})
