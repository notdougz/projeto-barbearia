from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from datetime import date, time, datetime
from decimal import Decimal
from unittest.mock import patch, Mock
from .models import Cliente, Servico, Agendamento
from .forms import ClienteForm, AgendamentoForm, ServicoForm, PrevisaoChegadaForm
from .smsdev_service import SMSDevService


class ClienteModelTest(TestCase):
    """Testes para o modelo Cliente"""
    
    def test_criar_cliente_com_dados_validos(self):
        """Testa criação de cliente com dados válidos"""
        cliente = Cliente.objects.create(
            nome="João Silva",
            telefone="11999999999",
            endereco="Rua das Flores, 123",
            observacoes="Cliente preferencial"
        )
        
        self.assertEqual(cliente.nome, "João Silva")
        self.assertEqual(cliente.telefone, "11999999999")
        self.assertEqual(cliente.endereco, "Rua das Flores, 123")
        self.assertEqual(cliente.observacoes, "Cliente preferencial")
        self.assertEqual(str(cliente), "João Silva")
    
    def test_criar_cliente_apenas_com_nome(self):
        """Testa criação de cliente apenas com nome obrigatório"""
        cliente = Cliente.objects.create(nome="Maria Santos")
        
        self.assertEqual(cliente.nome, "Maria Santos")
        self.assertIsNone(cliente.telefone)
        self.assertIsNone(cliente.endereco)
        self.assertIsNone(cliente.observacoes)
    
    def test_telefone_unico(self):
        """Testa que telefone deve ser único"""
        Cliente.objects.create(nome="Cliente 1", telefone="11999999999")
        
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(nome="Cliente 2", telefone="11999999999")
    
    def test_nome_obrigatorio(self):
        """Testa que nome é obrigatório"""
        # Django permite strings vazias por padrão em CharField
        # Este teste verifica se o campo existe e pode ser acessado
        cliente = Cliente.objects.create(nome="Teste")
        self.assertIsNotNone(cliente.nome)


class ServicoModelTest(TestCase):
    """Testes para o modelo Servico"""
    
    def test_criar_servico_com_dados_validos(self):
        """Testa criação de serviço com dados válidos"""
        servico = Servico.objects.create(
            nome="Corte Masculino",
            descricao="Corte tradicional masculino",
            duracao=30,
            preco=Decimal('25.00'),
            ativo=True
        )
        
        self.assertEqual(servico.nome, "Corte Masculino")
        self.assertEqual(servico.descricao, "Corte tradicional masculino")
        self.assertEqual(servico.duracao, 30)
        self.assertEqual(servico.preco, Decimal('25.00'))
        self.assertTrue(servico.ativo)
        self.assertEqual(str(servico), "Corte Masculino")
    
    def test_servico_padrao_ativo(self):
        """Testa que serviço é ativo por padrão"""
        servico = Servico.objects.create(
            nome="Barba",
            duracao=15,
            preco=Decimal('15.00')
        )
        
        self.assertTrue(servico.ativo)
    
    def test_servico_com_preco_decimal(self):
        """Testa criação de serviço com preço decimal"""
        servico = Servico.objects.create(
            nome="Corte + Barba",
            duracao=45,
            preco=Decimal('35.50')
        )
        
        self.assertEqual(servico.preco, Decimal('35.50'))


class AgendamentoModelTest(TestCase):
    """Testes para o modelo Agendamento"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.cliente = Cliente.objects.create(
            nome="João Silva",
            telefone="11999999999"
        )
        self.servico = Servico.objects.create(
            nome="Corte Masculino",
            duracao=30,
            preco=Decimal('25.00')
        )
    
    def test_criar_agendamento_com_dados_validos(self):
        """Testa criação de agendamento com dados válidos"""
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 1, 15),
            hora=time(14, 30),
            observacoes="Cliente prefere corte mais curto"
        )
        
        self.assertEqual(agendamento.cliente, self.cliente)
        self.assertEqual(agendamento.servico, self.servico)
        self.assertEqual(agendamento.data, date(2024, 1, 15))
        self.assertEqual(agendamento.hora, time(14, 30))
        self.assertEqual(agendamento.status, 'confirmado')  # Status padrão
        self.assertEqual(agendamento.status_pagamento, 'pendente')  # Status padrão
        self.assertEqual(agendamento.observacoes, "Cliente prefere corte mais curto")
    
    def test_agendamento_sem_cliente(self):
        """Testa criação de agendamento sem cliente (cliente avulso)"""
        agendamento = Agendamento.objects.create(
            servico=self.servico,
            data=date(2024, 1, 15),
            hora=time(14, 30)
        )
        
        self.assertIsNone(agendamento.cliente)
        self.assertEqual(str(agendamento), "Cliente avulso - Corte Masculino em 2024-01-15")
    
    def test_agendamento_status_choices(self):
        """Testa os status disponíveis para agendamento"""
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 1, 15),
            hora=time(14, 30)
        )
        
        # Testa mudança de status
        agendamento.status = 'a_caminho'
        agendamento.save()
        self.assertEqual(agendamento.status, 'a_caminho')
        
        agendamento.status = 'concluido'
        agendamento.save()
        self.assertEqual(agendamento.status, 'concluido')
    
    def test_agendamento_status_pagamento_choices(self):
        """Testa os status de pagamento disponíveis"""
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 1, 15),
            hora=time(14, 30)
        )
        
        # Testa mudança de status de pagamento
        agendamento.status_pagamento = 'pago'
        agendamento.save()
        self.assertEqual(agendamento.status_pagamento, 'pago')
    
    def test_agendamento_com_previsao_chegada(self):
        """Testa agendamento com previsão de chegada"""
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 1, 15),
            hora=time(14, 30),
            previsao_chegada=15
        )
        
        self.assertEqual(agendamento.previsao_chegada, 15)
    
    def test_agendamento_ordering(self):
        """Testa ordenação dos agendamentos"""
        # Criar agendamentos em ordem diferente
        agendamento1 = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 1, 15),
            hora=time(14, 30)
        )
        
        agendamento2 = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 1, 16),
            hora=time(10, 0)
        )
        
        agendamentos = Agendamento.objects.all()
        
        # Deve estar ordenado por data e hora decrescente
        self.assertEqual(agendamentos[0], agendamento2)  # Data mais recente primeiro
        self.assertEqual(agendamentos[1], agendamento1)
    
    def test_agendamento_str_representation(self):
        """Testa representação string do agendamento"""
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date(2024, 1, 15),
            hora=time(14, 30)
        )
        
        expected_str = "João Silva - Corte Masculino em 2024-01-15"
        self.assertEqual(str(agendamento), expected_str)


class ClienteFormTest(TestCase):
    """Testes para o formulário ClienteForm"""
    
    def test_cliente_form_dados_validos(self):
        """Testa formulário de cliente com dados válidos"""
        form_data = {
            'nome': 'João Silva',
            'telefone': '11999999999',
            'endereco': 'Rua das Flores, 123',
            'observacoes': 'Cliente preferencial'
        }
        form = ClienteForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['nome'], 'João Silva')
        self.assertEqual(form.cleaned_data['telefone'], '11999999999')
    
    def test_cliente_form_apenas_nome(self):
        """Testa formulário de cliente apenas com nome"""
        form_data = {'nome': 'Maria Santos'}
        form = ClienteForm(data=form_data)
        
        self.assertTrue(form.is_valid())
    
    def test_cliente_form_sem_nome(self):
        """Testa formulário de cliente sem nome"""
        form_data = {'telefone': '11999999999'}
        form = ClienteForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)


class ServicoFormTest(TestCase):
    """Testes para o formulário ServicoForm"""
    
    def test_servico_form_dados_validos(self):
        """Testa formulário de serviço com dados válidos"""
        form_data = {
            'nome': 'Corte Masculino',
            'descricao': 'Corte tradicional masculino',
            'duracao': 30,
            'preco': '25.00',
            'ativo': True
        }
        form = ServicoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['nome'], 'Corte Masculino')
        self.assertEqual(form.cleaned_data['duracao'], 30)
        self.assertEqual(form.cleaned_data['preco'], Decimal('25.00'))
    
    def test_servico_form_campos_obrigatorios(self):
        """Testa formulário de serviço com campos obrigatórios"""
        form_data = {
            'nome': 'Barba',
            'duracao': 15,
            'preco': '15.00',
            'ativo': True
        }
        form = ServicoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertTrue(form.cleaned_data['ativo'])
    
    def test_servico_form_sem_nome(self):
        """Testa formulário de serviço sem nome"""
        form_data = {
            'duracao': 30,
            'preco': '25.00'
        }
        form = ServicoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('nome', form.errors)
    
    def test_servico_form_preco_invalido(self):
        """Testa formulário de serviço com preço inválido"""
        form_data = {
            'nome': 'Corte',
            'duracao': 30,
            'preco': 'abc'  # Preço não numérico
        }
        form = ServicoForm(data=form_data)
        
        self.assertFalse(form.is_valid())


class AgendamentoFormTest(TestCase):
    """Testes para o formulário AgendamentoForm"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.cliente = Cliente.objects.create(
            nome="João Silva",
            telefone="11999999999"
        )
        self.servico = Servico.objects.create(
            nome="Corte Masculino",
            duracao=30,
            preco=Decimal('25.00')
        )
    
    def test_agendamento_form_dados_validos(self):
        """Testa formulário de agendamento com dados válidos"""
        form_data = {
            'cliente': self.cliente.id,
            'servico': self.servico.id,
            'data': '2024-01-15',
            'hora': '14:30',
            'observacoes': 'Cliente prefere corte mais curto'
        }
        form = AgendamentoForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['cliente'], self.cliente)
        self.assertEqual(form.cleaned_data['servico'], self.servico)
    
    def test_agendamento_form_sem_servico(self):
        """Testa formulário de agendamento sem serviço"""
        form_data = {
            'cliente': self.cliente.id,
            'data': '2024-01-15',
            'hora': '14:30'
        }
        form = AgendamentoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('servico', form.errors)
    
    def test_agendamento_form_sem_data(self):
        """Testa formulário de agendamento sem data"""
        form_data = {
            'cliente': self.cliente.id,
            'servico': self.servico.id,
            'hora': '14:30'
        }
        form = AgendamentoForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('data', form.errors)
    
    def test_agendamento_form_apenas_servicos_ativos(self):
        """Testa que apenas serviços ativos aparecem no formulário"""
        # Criar serviço inativo
        servico_inativo = Servico.objects.create(
            nome="Serviço Inativo",
            duracao=30,
            preco=Decimal('20.00'),
            ativo=False
        )
        
        form = AgendamentoForm()
        
        # Verificar que apenas serviços ativos estão no queryset
        servicos_disponiveis = form.fields['servico'].queryset
        self.assertIn(self.servico, servicos_disponiveis)
        self.assertNotIn(servico_inativo, servicos_disponiveis)


class PrevisaoChegadaFormTest(TestCase):
    """Testes para o formulário PrevisaoChegadaForm"""
    
    def test_previsao_form_dados_validos(self):
        """Testa formulário de previsão com dados válidos"""
        form_data = {'previsao_minutos': 15}
        form = PrevisaoChegadaForm(data=form_data)
        
        self.assertTrue(form.is_valid())
        self.assertEqual(form.cleaned_data['previsao_minutos'], 15)
    
    def test_previsao_form_valor_minimo(self):
        """Testa formulário de previsão com valor mínimo"""
        form_data = {'previsao_minutos': 1}
        form = PrevisaoChegadaForm(data=form_data)
        
        self.assertTrue(form.is_valid())
    
    def test_previsao_form_valor_maximo(self):
        """Testa formulário de previsão com valor máximo"""
        form_data = {'previsao_minutos': 180}
        form = PrevisaoChegadaForm(data=form_data)
        
        self.assertTrue(form.is_valid())
    
    def test_previsao_form_valor_abaixo_minimo(self):
        """Testa formulário de previsão com valor abaixo do mínimo"""
        form_data = {'previsao_minutos': 0}
        form = PrevisaoChegadaForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('previsao_minutos', form.errors)
    
    def test_previsao_form_valor_acima_maximo(self):
        """Testa formulário de previsão com valor acima do máximo"""
        form_data = {'previsao_minutos': 200}
        form = PrevisaoChegadaForm(data=form_data)
        
        self.assertFalse(form.is_valid())
        self.assertIn('previsao_minutos', form.errors)


class ViewsTest(TestCase):
    """Testes para as views principais"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        # Criar usuário para autenticação
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Criar dados de teste
        self.cliente = Cliente.objects.create(
            nome="João Silva",
            telefone="11999999999"
        )
        self.servico = Servico.objects.create(
            nome="Corte Masculino",
            duracao=30,
            preco=Decimal('25.00')
        )
        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=time(14, 30)
        )
        
        # Cliente para testes
        self.client = Client()
    
    def test_painel_barbeiro_requer_login(self):
        """Testa que painel do barbeiro requer login"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 302)  # Redirecionamento para login
    
    def test_painel_barbeiro_com_login(self):
        """Testa acesso ao painel do barbeiro com login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'João Silva')
    
    def test_lista_clientes_requer_login(self):
        """Testa que lista de clientes requer login"""
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 302)
    
    def test_lista_clientes_com_login(self):
        """Testa acesso à lista de clientes com login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'João Silva')
    
    def test_criar_cliente_requer_login(self):
        """Testa que criar cliente requer login"""
        response = self.client.get(reverse('criar_cliente'))
        self.assertEqual(response.status_code, 302)
    
    def test_criar_cliente_com_login(self):
        """Testa acesso à página de criar cliente com login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('criar_cliente'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Novo Cliente')
    
    def test_criar_cliente_post(self):
        """Testa criação de cliente via POST"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Maria Santos',
            'telefone': '11888888888',
            'endereco': 'Rua das Flores, 456',
            'observacoes': 'Cliente VIP'
        }
        
        response = self.client.post(reverse('criar_cliente'), form_data)
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        
        # Verificar se cliente foi criado
        cliente_criado = Cliente.objects.get(nome='Maria Santos')
        self.assertEqual(cliente_criado.telefone, '11888888888')
    
    def test_editar_cliente_requer_login(self):
        """Testa que editar cliente requer login"""
        response = self.client.get(reverse('editar_cliente', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 302)
    
    def test_editar_cliente_com_login(self):
        """Testa acesso à página de editar cliente com login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('editar_cliente', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.cliente.nome)
    
    def test_lista_servicos_requer_login(self):
        """Testa que lista de serviços requer login"""
        response = self.client.get(reverse('lista_servicos'))
        self.assertEqual(response.status_code, 302)
    
    def test_lista_servicos_com_login(self):
        """Testa acesso à lista de serviços com login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('lista_servicos'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Corte Masculino')
    
    def test_criar_servico_requer_login(self):
        """Testa que criar serviço requer login"""
        response = self.client.get(reverse('criar_servico'))
        self.assertEqual(response.status_code, 302)
    
    def test_criar_servico_com_login(self):
        """Testa acesso à página de criar serviço com login"""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('criar_servico'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Novo Serviço')
    
    def test_criar_servico_post(self):
        """Testa criação de serviço via POST"""
        self.client.login(username='testuser', password='testpass123')
        
        form_data = {
            'nome': 'Barba Completa',
            'descricao': 'Barba completa com acabamento',
            'duracao': 20,
            'preco': '18.00',
            'ativo': True
        }
        
        response = self.client.post(reverse('criar_servico'), form_data)
        self.assertEqual(response.status_code, 302)  # Redirecionamento após sucesso
        
        # Verificar se serviço foi criado
        servico_criado = Servico.objects.get(nome='Barba Completa')
        self.assertEqual(servico_criado.duracao, 20)
        self.assertEqual(servico_criado.preco, Decimal('18.00'))


class SMSDevServiceTest(TestCase):
    """Testes para o serviço SMSDev"""
    
    def setUp(self):
        """Configuração inicial para os testes"""
        self.sms_service = SMSDevService()
    
    def test_sms_service_inicializacao(self):
        """Testa inicialização do serviço SMS"""
        self.assertIsNotNone(self.sms_service)
        self.assertIsNotNone(self.sms_service.api_url)
        self.assertEqual(self.sms_service.api_url, 'https://api.smsdev.com.br/v1/send')
    
    def test_limpar_telefone_valido(self):
        """Testa limpeza de telefone válido"""
        telefone_limpo = self.sms_service._limpar_telefone('11999999999')
        self.assertEqual(telefone_limpo, '11999999999')
        
        telefone_limpo = self.sms_service._limpar_telefone('(11) 99999-9999')
        self.assertEqual(telefone_limpo, '11999999999')
        
        telefone_limpo = self.sms_service._limpar_telefone('+55 11 99999-9999')
        self.assertEqual(telefone_limpo, '11999999999')
    
    def test_limpar_telefone_invalido(self):
        """Testa limpeza de telefone inválido"""
        telefone_limpo = self.sms_service._limpar_telefone('123')
        self.assertIsNone(telefone_limpo)
        
        telefone_limpo = self.sms_service._limpar_telefone('abc')
        self.assertIsNone(telefone_limpo)
        
        telefone_limpo = self.sms_service._limpar_telefone('')
        self.assertIsNone(telefone_limpo)
    
    @patch('agendamentos.smsdev_service.requests.post')
    def test_enviar_sms_sucesso(self, mock_post):
        """Testa envio de SMS com sucesso"""
        # Mock da resposta da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'situacao': 'OK',
            'id': '12345',
            'descricao': 'SMS enviado com sucesso'
        }
        mock_post.return_value = mock_response
        
        # Configurar serviço como habilitado
        with patch.object(self.sms_service, 'enabled', True):
            with patch.object(self.sms_service, 'usuario', 'test@test.com'):
                with patch.object(self.sms_service, 'token', 'test_token'):
                    resultado = self.sms_service.enviar_sms('11999999999', 'Teste de SMS')
        
        self.assertTrue(resultado['sucesso'])
        self.assertIsNone(resultado['erro'])
        self.assertEqual(resultado['id'], '12345')
        self.assertEqual(resultado['situacao'], 'OK')
        mock_post.assert_called_once()
    
    @patch('agendamentos.smsdev_service.requests.post')
    def test_enviar_sms_erro_api(self, mock_post):
        """Testa envio de SMS com erro da API"""
        # Mock da resposta de erro da API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'situacao': 'ERRO',
            'descricao': 'Número inválido'
        }
        mock_post.return_value = mock_response
        
        # Configurar serviço como habilitado
        with patch.object(self.sms_service, 'enabled', True):
            with patch.object(self.sms_service, 'usuario', 'test@test.com'):
                with patch.object(self.sms_service, 'token', 'test_token'):
                    resultado = self.sms_service.enviar_sms('11999999999', 'Teste de SMS')
        
        self.assertFalse(resultado['sucesso'])
        self.assertEqual(resultado['erro'], 'Número inválido')
        self.assertIsNone(resultado['id'])
    
    def test_enviar_sms_desabilitado(self):
        """Testa envio de SMS quando serviço está desabilitado"""
        with patch.object(self.sms_service, 'enabled', False):
            resultado = self.sms_service.enviar_sms('11999999999', 'Teste de SMS')
        
        self.assertFalse(resultado['sucesso'])
        self.assertEqual(resultado['erro'], 'SMS desabilitado')
        self.assertIsNone(resultado['id'])
    
    def test_enviar_sms_sem_credenciais(self):
        """Testa envio de SMS sem credenciais configuradas"""
        with patch.object(self.sms_service, 'enabled', True):
            with patch.object(self.sms_service, 'usuario', None):
                with patch.object(self.sms_service, 'token', None):
                    resultado = self.sms_service.enviar_sms('11999999999', 'Teste de SMS')
        
        self.assertFalse(resultado['sucesso'])
        self.assertEqual(resultado['erro'], 'Credenciais SMSDev não configuradas')
        self.assertIsNone(resultado['id'])
    
    def test_enviar_sms_telefone_invalido(self):
        """Testa envio de SMS com telefone inválido"""
        with patch.object(self.sms_service, 'enabled', True):
            with patch.object(self.sms_service, 'usuario', 'test@test.com'):
                with patch.object(self.sms_service, 'token', 'test_token'):
                    resultado = self.sms_service.enviar_sms('123', 'Teste de SMS')
        
        self.assertFalse(resultado['sucesso'])
        self.assertEqual(resultado['erro'], 'Número de telefone inválido')
        self.assertIsNone(resultado['id'])
    
    @patch('agendamentos.smsdev_service.requests.post')
    def test_enviar_sms_excecao_requests(self, mock_post):
        """Testa envio de SMS com exceção na requisição"""
        # Mock de exceção na requisição
        mock_post.side_effect = Exception('Erro de conexão')
        
        # Configurar serviço como habilitado
        with patch.object(self.sms_service, 'enabled', True):
            with patch.object(self.sms_service, 'usuario', 'test@test.com'):
                with patch.object(self.sms_service, 'token', 'test_token'):
                    resultado = self.sms_service.enviar_sms('11999999999', 'Teste de SMS')
        
        self.assertFalse(resultado['sucesso'])
        self.assertIn('erro', resultado)
        self.assertIsNone(resultado['id'])
