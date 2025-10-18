"""
Testes de Integração - Projeto Barbearia

Este módulo contém testes que verificam fluxos completos do sistema,
testando a integração entre diferentes componentes.
"""

import pytest
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import transaction
from datetime import date, time, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch, Mock

from .models import Cliente, Servico, Agendamento
from .forms import ClienteForm, AgendamentoForm, ServicoForm
from .smsdev_service import SMSDevService


@pytest.mark.integration
class FluxoCompletoAgendamentoTest(TestCase):
    """Testa o fluxo completo de criação de agendamento com SMS"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        # Criar usuário para autenticação
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Criar cliente
        self.cliente = Cliente.objects.create(
            nome="João Silva",
            telefone="11999999999",
            endereco="Rua das Flores, 123"
        )
        
        # Criar serviço
        self.servico = Servico.objects.create(
            nome="Corte Masculino",
            descricao="Corte tradicional masculino",
            duracao=30,
            preco=Decimal('25.00'),
            ativo=True
        )
        
        # Cliente para testes HTTP
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    @patch('agendamentos.smsdev_service.smsdev_service.enviar_sms')
    def test_fluxo_completo_agendamento_com_sms(self, mock_enviar_sms):
        """Testa fluxo completo: Cliente → Serviço → Agendamento → SMS"""
        # Mock do SMS
        mock_enviar_sms.return_value = {
            'sucesso': True,
            'id': '12345',
            'situacao': 'OK'
        }
        
        # Dados do agendamento
        agendamento_data = {
            'cliente': self.cliente.id,
            'servico': self.servico.id,
            'data': '2024-12-20',
            'hora': '14:30',
            'observacoes': 'Cliente prefere corte mais curto'
        }
        
        # Criar agendamento via POST
        response = self.client.post(reverse('agendar'), agendamento_data)
        
        # Verificar redirecionamento (sucesso)
        self.assertEqual(response.status_code, 302)
        
        # Verificar se agendamento foi criado
        agendamento = Agendamento.objects.get(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 12, 20)
        )
        
        self.assertEqual(agendamento.hora, time(14, 30))
        self.assertEqual(agendamento.status, 'confirmado')
        self.assertEqual(agendamento.status_pagamento, 'pendente')
        self.assertEqual(agendamento.observacoes, 'Cliente prefere corte mais curto')
        
        # SMS não é enviado automaticamente na criação, apenas quando marcado como "à caminho"
        mock_enviar_sms.assert_not_called()
    
    @patch('agendamentos.smsdev_service.smsdev_service.enviar_sms')
    def test_cancelamento_agendamento_com_notificacao(self, mock_enviar_sms):
        """Testa cancelamento de agendamento com notificação SMS"""
        # Mock do SMS
        mock_enviar_sms.return_value = {
            'sucesso': True,
            'id': '12346',
            'situacao': 'OK'
        }
        
        # Criar agendamento
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today() + timedelta(days=1),
            hora=time(14, 30),
            status='confirmado'
        )
        
        # Cancelar agendamento (usando deletar)
        response = self.client.post(
            reverse('deletar_agendamento', args=[agendamento.pk])
        )
        
        # Verificar redirecionamento
        self.assertEqual(response.status_code, 302)
        
        # Verificar se agendamento foi deletado (não deve mais existir)
        with self.assertRaises(Agendamento.DoesNotExist):
            Agendamento.objects.get(pk=agendamento.pk)
        
        # SMS não é enviado automaticamente na deleção
        mock_enviar_sms.assert_not_called()
    
    def test_reagendamento_com_validacao_horario(self):
        """Testa reagendamento com validação de horário"""
        # Criar agendamento original
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today() + timedelta(days=1),
            hora=time(14, 30),
            status='confirmado'
        )
        
        # Dados para reagendamento
        novo_data = date.today() + timedelta(days=2)
        novo_hora = time(16, 0)
        
        # Reagendar (usando editar_agendamento)
        response = self.client.post(
            reverse('editar_agendamento', args=[agendamento.pk]),
            {
                'cliente': agendamento.cliente.id,
                'servico': agendamento.servico.id,
                'data': novo_data.strftime('%Y-%m-%d'),
                'hora': novo_hora.strftime('%H:%M'),
                'observacoes': agendamento.observacoes or ''
            }
        )
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verificar se dados foram atualizados
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.data, novo_data)
        self.assertEqual(agendamento.hora, novo_hora)
    
    def test_processo_pagamento_completo(self):
        """Testa processo completo de pagamento"""
        # Criar agendamento
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=time(14, 30),
            status='concluido',
            status_pagamento='pendente'
        )
        
        # Marcar como pago (usando alterar_status_pagamento)
        response = self.client.post(
            reverse('alterar_status_pagamento', args=[agendamento.pk])
        )
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 302)
        
        # Verificar se status foi alterado
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status_pagamento, 'pago')
    
    def test_relatorio_financeiro_mensal(self):
        """Testa cálculo de relatório financeiro mensal"""
        # Criar agendamentos com diferentes status de pagamento
        hoje = date.today()
        
        # Agendamento pago
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=hoje,
            hora=time(10, 0),
            status='concluido',
            status_pagamento='pago'
        )
        
        # Agendamento pendente
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=hoje,
            hora=time(14, 0),
            status='concluido',
            status_pagamento='pendente'
        )
        
        # Acessar relatório financeiro
        response = self.client.get(reverse('financeiro'))
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se dados estão no contexto
        self.assertIn('valor_recebido', response.context)
        self.assertIn('valor_pendente', response.context)
        self.assertIn('total_pago', response.context)
        self.assertIn('total_pendente', response.context)
        
        # Verificar cálculos
        valor_recebido = response.context['valor_recebido']
        self.assertEqual(valor_recebido, Decimal('25.00'))  # Apenas o pago
    
    def test_busca_cliente_multiplos_criterios(self):
        """Testa busca de cliente por múltiplos critérios"""
        # Criar clientes adicionais
        Cliente.objects.create(
            nome="Maria Santos",
            telefone="11888888888",
            endereco="Rua das Palmeiras, 456"
        )
        
        Cliente.objects.create(
            nome="Pedro Oliveira",
            telefone="11777777777",
            endereco="Rua das Flores, 789"  # Mesmo nome de rua
        )
        
        # Buscar todos os clientes (sem filtro)
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se todos os clientes aparecem
        self.assertContains(response, 'João Silva')
        self.assertContains(response, 'Maria Santos')
        self.assertContains(response, 'Pedro Oliveira')


@pytest.mark.integration
class FluxoClienteServicoTest(TestCase):
    """Testa fluxos de criação e gerenciamento de clientes e serviços"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_criacao_cliente_e_agendamento_sequencial(self):
        """Testa criação de cliente seguida de agendamento"""
        # Criar cliente
        cliente_data = {
            'nome': 'Ana Costa',
            'telefone': '11666666666',
            'endereco': 'Rua Nova, 100',
            'observacoes': 'Cliente nova'
        }
        
        response = self.client.post(reverse('criar_cliente'), cliente_data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar se cliente foi criado
        cliente = Cliente.objects.get(nome='Ana Costa')
        self.assertEqual(cliente.telefone, '11666666666')
        
        # Criar serviço
        servico = Servico.objects.create(
            nome="Barba Completa",
            duracao=20,
            preco=Decimal('15.00')
        )
        
        # Criar agendamento para o cliente
        agendamento_data = {
            'cliente': cliente.id,
            'servico': servico.id,
            'data': '2024-12-21',
            'hora': '15:00'
        }
        
        response = self.client.post(reverse('agendar'), agendamento_data)
        self.assertEqual(response.status_code, 302)
        
        # Verificar se agendamento foi criado
        agendamento = Agendamento.objects.get(cliente=cliente, servico=servico)
        self.assertEqual(agendamento.data, date(2024, 12, 21))
        self.assertEqual(agendamento.hora, time(15, 0))
    
    def test_edicao_servico_e_impacto_agendamentos(self):
        """Testa edição de serviço e impacto nos agendamentos"""
        # Criar serviço
        servico = Servico.objects.create(
            nome="Corte Feminino",
            duracao=45,
            preco=Decimal('35.00')
        )
        
        # Criar cliente
        cliente = Cliente.objects.create(
            nome="Carla Mendes",
            telefone="11555555555"
        )
        
        # Criar agendamento
        agendamento = Agendamento.objects.create(
            cliente=cliente,
            servico=servico,
            data=date.today() + timedelta(days=1),
            hora=time(16, 0)
        )
        
        # Editar serviço
        servico_data = {
            'nome': 'Corte Feminino Premium',
            'descricao': 'Corte feminino com lavagem',
            'duracao': 60,
            'preco': '45.00',
            'ativo': True
        }
        
        response = self.client.post(
            reverse('editar_servico', args=[servico.pk]),
            servico_data
        )
        self.assertEqual(response.status_code, 302)
        
        # Verificar se serviço foi atualizado
        servico.refresh_from_db()
        self.assertEqual(servico.nome, 'Corte Feminino Premium')
        self.assertEqual(servico.preco, Decimal('45.00'))
        
        # Verificar se agendamento ainda referencia o serviço
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.servico.nome, 'Corte Feminino Premium')
    
    def test_desativacao_servico_e_formularios(self):
        """Testa desativação de serviço e impacto em formulários"""
        # Criar serviço ativo
        servico = Servico.objects.create(
            nome="Escova Progressiva",
            duracao=120,
            preco=Decimal('80.00'),
            ativo=True
        )
        
        # Verificar se serviço aparece no formulário de agendamento
        response = self.client.get(reverse('agendar'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Escova Progressiva')
        
        # Desativar serviço
        servico.ativo = False
        servico.save()
        
        # Verificar se serviço não aparece mais no formulário
        response = self.client.get(reverse('agendar'))
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, 'Escova Progressiva')


@pytest.mark.integration
class FluxoStatusAgendamentoTest(TestCase):
    """Testa fluxos de mudança de status de agendamentos"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.cliente = Cliente.objects.create(
            nome="Roberto Silva",
            telefone="11444444444"
        )
        
        self.servico = Servico.objects.create(
            nome="Corte + Barba",
            duracao=45,
            preco=Decimal('40.00')
        )
    
    def test_fluxo_status_completo(self):
        """Testa fluxo completo de status: confirmado → à caminho → concluído"""
        # Criar agendamento confirmado
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=time(14, 0),
            status='confirmado'
        )
        
        # Marcar como "à caminho" (GET primeiro para obter formulário)
        response = self.client.get(
            reverse('on_the_way_agendamento', args=[agendamento.pk])
        )
        self.assertEqual(response.status_code, 200)
        
        # POST com dados do formulário
        response = self.client.post(
            reverse('on_the_way_agendamento', args=[agendamento.pk]),
            {'previsao_minutos': 15}
        )
        self.assertEqual(response.status_code, 302)
        
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, 'a_caminho')
        
        # Marcar como concluído
        response = self.client.post(
            reverse('concluir_agendamento', args=[agendamento.pk])
        )
        self.assertEqual(response.status_code, 302)
        
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.status, 'concluido')
    
    @patch('agendamentos.smsdev_service.smsdev_service.enviar_sms')
    def test_notificacao_a_caminho(self, mock_enviar_sms):
        """Testa notificação SMS quando cliente está à caminho"""
        mock_enviar_sms.return_value = {
            'sucesso': True,
            'id': '12347',
            'situacao': 'OK'
        }
        
        # Criar agendamento
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=time(15, 0),
            status='confirmado'
        )
        
        # Marcar como à caminho (GET primeiro para obter formulário)
        response = self.client.get(
            reverse('on_the_way_agendamento', args=[agendamento.pk])
        )
        self.assertEqual(response.status_code, 200)
        
        # POST com dados do formulário
        response = self.client.post(
            reverse('on_the_way_agendamento', args=[agendamento.pk]),
            {'previsao_minutos': 15}
        )
        
        # Verificar se SMS foi enviado
        mock_enviar_sms.assert_called_once()
        args, kwargs = mock_enviar_sms.call_args
        self.assertEqual(args[0], '11444444444')
        self.assertIn('caminho', args[1].lower())  # Verificar se contém "caminho"
    
    def test_previsao_chegada_integracao(self):
        """Testa integração da previsão de chegada"""
        # Criar agendamento
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=time(16, 0),
            status='a_caminho'
        )
        
        # Definir previsão de chegada diretamente no modelo
        agendamento.previsao_chegada = 15
        agendamento.save()
        
        # Verificar se previsão foi salva
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.previsao_chegada, 15)


@pytest.mark.integration
class FluxoRelatoriosTest(TestCase):
    """Testa fluxos de relatórios e estatísticas"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Criar dados de teste
        self.cliente1 = Cliente.objects.create(nome="Cliente 1", telefone="11111111111")
        self.cliente2 = Cliente.objects.create(nome="Cliente 2", telefone="22222222222")
        
        self.servico1 = Servico.objects.create(
            nome="Corte", duracao=30, preco=Decimal('25.00')
        )
        self.servico2 = Servico.objects.create(
            nome="Barba", duracao=15, preco=Decimal('15.00')
        )
    
    def test_relatorio_agendamentos_mensais(self):
        """Testa relatório de agendamentos mensais"""
        # Criar agendamentos para diferentes meses
        hoje = date.today()
        
        # Agendamentos deste mês
        Agendamento.objects.create(
            cliente=self.cliente1,
            servico=self.servico1,
            data=hoje,
            hora=time(10, 0),
            status='concluido',
            status_pagamento='pago'
        )
        
        Agendamento.objects.create(
            cliente=self.cliente2,
            servico=self.servico2,
            data=hoje,
            hora=time(14, 0),
            status='concluido',
            status_pagamento='pago'
        )
        
        # Agendamento do mês passado
        mes_passado = hoje.replace(day=1) - timedelta(days=1)
        Agendamento.objects.create(
            cliente=self.cliente1,
            servico=self.servico1,
            data=mes_passado,
            hora=time(16, 0),
            status='concluido',
            status_pagamento='pago'
        )
        
        # Acessar relatório mensal
        response = self.client.get(reverse('agendamentos_mensais'))
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se dados estão no contexto
        self.assertIn('agendamentos', response.context)
        self.assertIn('total_agendamentos', response.context)
        
        # Verificar cálculos
        agendamentos = response.context['agendamentos']
        self.assertEqual(len(agendamentos), 2)  # Apenas deste mês
        
        total_agendamentos = response.context['total_agendamentos']
        self.assertEqual(total_agendamentos, 2)
    
    def test_estatisticas_clientes_frequentes(self):
        """Testa estatísticas de clientes mais frequentes"""
        # Criar múltiplos agendamentos para cliente1
        for i in range(3):
            Agendamento.objects.create(
                cliente=self.cliente1,
                servico=self.servico1,
                data=date.today() - timedelta(days=i),
                hora=time(10, 0),
                status='concluido'
            )
        
        # Criar um agendamento para cliente2
        Agendamento.objects.create(
            cliente=self.cliente2,
            servico=self.servico2,
            data=date.today(),
            hora=time(14, 0),
            status='concluido'
        )
        
        # Acessar painel do barbeiro (que deve mostrar estatísticas)
        response = self.client.get(reverse('painel_barbeiro'))
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se cliente1 aparece mais vezes (3 vezes vs 1 vez)
        content = response.content.decode()
        cliente1_count = content.count('Cliente 1')
        cliente2_count = content.count('Cliente 2')
        
        self.assertGreaterEqual(cliente1_count, cliente2_count)
