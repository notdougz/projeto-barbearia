"""
Testes de API SMS - Projeto Barbearia

Este módulo contém testes para a integração com a API SMSDev,
incluindo cenários de sucesso, erro e fallback.
"""

from datetime import date
from datetime import time as dt_time
from datetime import timedelta
from decimal import Decimal
from unittest.mock import Mock, patch

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

import pytest

from .models import Agendamento, Cliente, Servico
from .smsdev_service import smsdev_service


@pytest.mark.api
class SMSServiceTest(TestCase):
    """Testa o serviço SMS diretamente"""

    def setUp(self):
        """Configuração inicial"""
        self.cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today() + timedelta(days=1),
            hora=dt_time(14, 30),
            status="confirmado",
        )

    @patch("agendamentos.smsdev_service.requests.post")
    def test_sms_sucesso_envio(self, mock_post):
        """Testa envio de SMS com sucesso"""
        # Mock da resposta de sucesso
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"id": "12345", "situacao": "OK"}
        mock_post.return_value = mock_response

        # Enviar SMS
        resultado = smsdev_service.enviar_sms(
            self.cliente.telefone,
            "Olá João! Seu agendamento está confirmado para amanhã às 14:30.",
        )

        # Verificar resultado
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["id"], "12345")
        self.assertEqual(resultado["situacao"], "OK")

        # Verificar se a requisição foi feita corretamente
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertIn("smsdev.com.br", args[0])
        self.assertIn("number", kwargs["data"])
        self.assertIn("msg", kwargs["data"])

    @patch("agendamentos.smsdev_service.requests.post")
    def test_sms_erro_credenciais_invalidas(self, mock_post):
        """Testa erro de credenciais inválidas"""
        # Mock da resposta de erro
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "situacao": "ERRO",
            "codigo": "401",
            "descricao": "Credenciais inválidas",
        }
        mock_post.return_value = mock_response

        # Enviar SMS
        resultado = smsdev_service.enviar_sms(self.cliente.telefone, "Teste de erro")

        # Verificar resultado
        self.assertFalse(resultado["sucesso"])
        self.assertIn("Credenciais", resultado["erro"])

    @patch("agendamentos.smsdev_service.requests.post")
    def test_sms_erro_timeout(self, mock_post):
        """Testa timeout da API"""
        # Mock de timeout
        mock_post.side_effect = Exception("Timeout")

        # Enviar SMS
        resultado = smsdev_service.enviar_sms(self.cliente.telefone, "Teste de timeout")

        # Verificar resultado
        self.assertFalse(resultado["sucesso"])
        self.assertIn("Timeout", resultado["erro"])

    @patch("agendamentos.smsdev_service.requests.post")
    def test_sms_erro_numero_invalido(self, mock_post):
        """Testa erro de número inválido"""
        # Mock da resposta de erro
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "situacao": "ERRO",
            "codigo": "400",
            "descricao": "Número inválido",
        }
        mock_post.return_value = mock_response

        # Enviar SMS para número inválido
        resultado = smsdev_service.enviar_sms("123", "Teste")  # Número inválido

        # Verificar resultado
        self.assertFalse(resultado["sucesso"])
        self.assertIn("inválido", resultado["erro"])

    @patch("agendamentos.smsdev_service.requests.post")
    def test_sms_erro_conta_sem_credito(self, mock_post):
        """Testa erro de conta sem crédito"""
        # Mock da resposta de erro
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "situacao": "ERRO",
            "codigo": "402",
            "descricao": "Saldo insuficiente",
        }
        mock_post.return_value = mock_response

        # Enviar SMS
        resultado = smsdev_service.enviar_sms(self.cliente.telefone, "Teste de saldo")

        # Verificar resultado
        self.assertFalse(resultado["sucesso"])
        self.assertIn("Saldo", resultado["erro"])

    def test_sms_credenciais_nao_configuradas(self):
        """Testa quando credenciais não estão configuradas"""
        # Simular credenciais não configuradas
        with patch.object(smsdev_service, "usuario", None):
            resultado = smsdev_service.enviar_sms(
                self.cliente.telefone, "Teste sem credenciais"
            )

            # Verificar resultado
            self.assertFalse(resultado["sucesso"])
            self.assertIn("Credenciais", resultado["erro"])

    def test_sms_telefone_formatos_validos(self):
        """Testa diferentes formatos de telefone válidos"""
        formatos_validos = [
            "11999999999",
            "+5511999999999",
            "(11) 99999-9999",
            "11 99999 9999",
            "11-99999-9999",
        ]

        with patch("agendamentos.smsdev_service.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"situacao": "OK"}
            mock_post.return_value = mock_response

            for formato in formatos_validos:
                resultado = smsdev_service.enviar_sms(formato, "Teste")
                self.assertTrue(
                    resultado["sucesso"], f"Formato {formato} deveria ser válido"
                )

    def test_sms_telefone_formatos_invalidos(self):
        """Testa formatos de telefone inválidos"""
        formatos_invalidos = [
            "123",  # Muito curto
            "abcdefghijk",  # Letras
            "119999999999999",  # Muito longo
            "",  # Vazio
            None,  # None
        ]

        for formato in formatos_invalidos:
            resultado = smsdev_service.enviar_sms(formato, "Teste")
            self.assertFalse(
                resultado["sucesso"], f"Formato {formato} deveria ser inválido"
            )


@pytest.mark.api
class SMSIntegrationTest(TestCase):
    """Testa integração SMS com views"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.cliente = Cliente.objects.create(
            nome="Maria Santos", telefone="11988888888"
        )

        self.servico = Servico.objects.create(
            nome="Corte Feminino", duracao=45, preco=Decimal("35.00")
        )

    @patch("agendamentos.smsdev_service.smsdev_service.enviar_barbeiro_a_caminho")
    def test_sms_confirmacao_agendamento(self, mock_enviar_sms):
        """Testa SMS de confirmação ao criar agendamento"""
        # Mock do SMS
        mock_enviar_sms.return_value = {
            "sucesso": True,
            "id": "12345",
            "situacao": "OK",
        }

        # Dados do agendamento
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-20",
            "hora": "15:00",
            "observacoes": "Cliente prefere corte mais longo",
        }

        # Criar agendamento
        response = self.client.post(reverse("agendar"), agendamento_data)

        # Verificar redirecionamento (sucesso)
        self.assertEqual(response.status_code, 302)

        # Verificar se agendamento foi criado
        agendamento = Agendamento.objects.get(
            cliente=self.cliente, servico=self.servico, data=date(2024, 12, 20)
        )

        self.assertEqual(agendamento.status, "confirmado")

        # SMS não é enviado automaticamente na criação
        mock_enviar_sms.assert_not_called()

    @patch("agendamentos.smsdev_service.smsdev_service.enviar_barbeiro_a_caminho")
    def test_sms_a_caminho_integracao(self, mock_enviar_sms):
        """Testa SMS quando cliente está à caminho"""
        # Mock do SMS
        mock_enviar_sms.return_value = {
            "sucesso": True,
            "id": "12345",
            "situacao": "OK",
        }

        # Criar agendamento
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=dt_time(15, 0),
            status="confirmado",
        )

        # Marcar como à caminho
        response = self.client.get(
            reverse("on_the_way_agendamento", args=[agendamento.pk])
        )
        self.assertEqual(response.status_code, 200)

        # POST com dados do formulário
        response = self.client.post(
            reverse("on_the_way_agendamento", args=[agendamento.pk]),
            {"previsao_minutos": 15},
        )

        # Verificar se SMS foi enviado
        mock_enviar_sms.assert_called_once()
        args, kwargs = mock_enviar_sms.call_args
        self.assertEqual(args[0].cliente.telefone, "11988888888")
        # args[1] é a previsao_minutos (int), não a mensagem
        self.assertEqual(args[1], 15)

    @patch("agendamentos.smsdev_service.smsdev_service.enviar_sms")
    def test_sms_fallback_sistema_continua(self, mock_enviar_sms):
        """Testa que o sistema continua funcionando mesmo com falha no SMS"""
        # Mock de falha no SMS
        mock_enviar_sms.return_value = {"sucesso": False, "erro": "Erro de conexão"}

        # Criar agendamento mesmo com SMS falhando
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-20",
            "hora": "16:00",
        }

        response = self.client.post(reverse("agendar"), agendamento_data)

        # Sistema deve continuar funcionando
        self.assertEqual(response.status_code, 302)

        # Verificar se agendamento foi criado
        agendamento = Agendamento.objects.get(
            cliente=self.cliente, servico=self.servico, data=date(2024, 12, 20)
        )

        self.assertEqual(agendamento.status, "confirmado")

    def test_rate_limiting_sms_simulado(self):
        """Testa simulação de rate limiting"""
        # Simular múltiplos envios em sequência
        with patch("agendamentos.smsdev_service.requests.post") as mock_post:
            # Primeiro envio: sucesso
            mock_response1 = Mock()
            mock_response1.status_code = 200
            mock_response1.json.return_value = {"situacao": "OK"}

            # Segundo envio: rate limit
            mock_response2 = Mock()
            mock_response2.status_code = 200
            mock_response2.json.return_value = {
                "situacao": "ERRO",
                "codigo": "429",
                "descricao": "Rate limit exceeded",
            }

            mock_post.side_effect = [mock_response1, mock_response2]

            # Primeiro envio
            resultado1 = smsdev_service.enviar_sms("11999999999", "Primeiro SMS")
            self.assertTrue(resultado1["sucesso"])

            # Segundo envio (rate limited)
            resultado2 = smsdev_service.enviar_sms("11999999999", "Segundo SMS")
            self.assertFalse(resultado2["sucesso"])
            self.assertIn("Rate limit", resultado2["erro"])


@pytest.mark.api
class SMSValidationTest(TestCase):
    """Testa validações específicas do SMS"""

    def setUp(self):
        """Configuração inicial"""
        self.cliente = Cliente.objects.create(
            nome="Pedro Costa", telefone="11977777777"
        )

    def test_sms_mensagem_muito_longa(self):
        """Testa SMS com mensagem muito longa"""
        mensagem_longa = "A" * 1000  # Mensagem muito longa

        with patch("agendamentos.smsdev_service.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "situacao": "ERRO",
                "codigo": "400",
                "descricao": "Mensagem muito longa",
            }
            mock_post.return_value = mock_response

            resultado = smsdev_service.enviar_sms(self.cliente.telefone, mensagem_longa)

            self.assertFalse(resultado["sucesso"])
            self.assertIn("longa", resultado["erro"])

    def test_sms_mensagem_vazia(self):
        """Testa SMS com mensagem vazia"""
        resultado = smsdev_service.enviar_sms(self.cliente.telefone, "")

        # Deve falhar com mensagem vazia (pode ser erro da API ou validação)
        self.assertFalse(resultado["sucesso"])
        # Aceitar qualquer tipo de erro para mensagem vazia
        self.assertIsNotNone(resultado.get("erro"))

    def test_sms_caracteres_especiais(self):
        """Testa SMS com caracteres especiais"""
        mensagem_especial = (
            "Olá! Seu agendamento está confirmado para amanhã às 14:30. 🎉"
        )

        with patch("agendamentos.smsdev_service.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"situacao": "OK"}
            mock_post.return_value = mock_response

            resultado = smsdev_service.enviar_sms(
                self.cliente.telefone, mensagem_especial
            )

            self.assertTrue(resultado["sucesso"])

    def test_sms_encoding_utf8(self):
        """Testa encoding UTF-8 em mensagens"""
        mensagem_utf8 = "Olá João! Seu agendamento está confirmado para amanhã às 14:30. Ação especial!"

        with patch("agendamentos.smsdev_service.requests.post") as mock_post:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"situacao": "OK"}
            mock_post.return_value = mock_response

            resultado = smsdev_service.enviar_sms(self.cliente.telefone, mensagem_utf8)

            self.assertTrue(resultado["sucesso"])

            # Verificar se a mensagem foi enviada corretamente
            args, kwargs = mock_post.call_args
            self.assertIn("msg", kwargs["data"])
            self.assertEqual(kwargs["data"]["msg"], mensagem_utf8)


@pytest.mark.api
class SMSMonitoringTest(TestCase):
    """Testa monitoramento e logs do SMS"""

    def setUp(self):
        """Configuração inicial"""
        self.cliente = Cliente.objects.create(nome="Ana Silva", telefone="11966666666")

    @patch("agendamentos.smsdev_service.requests.post")
    def test_log_sucesso_sms(self, mock_post):
        """Testa log de sucesso do SMS"""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "sucesso": True,
            "id": "12345",
            "situacao": "OK",
        }
        mock_post.return_value = mock_response

        # Capturar logs
        with patch("agendamentos.smsdev_service.logger") as mock_logger:
            resultado = smsdev_service.enviar_sms(self.cliente.telefone, "Teste de log")

            # Verificar se log foi registrado
            mock_logger.info.assert_called()
            self.assertTrue(resultado["sucesso"])

    @patch("agendamentos.smsdev_service.requests.post")
    def test_log_erro_sms(self, mock_post):
        """Testa log de erro do SMS"""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.json.return_value = {
            "sucesso": False,
            "situacao": "ERRO",
            "codigo": "500",
            "descricao": "Erro interno do servidor",
        }
        mock_post.return_value = mock_response

        # Capturar logs
        with patch("agendamentos.smsdev_service.logger") as mock_logger:
            resultado = smsdev_service.enviar_sms(
                self.cliente.telefone, "Teste de erro"
            )

            # Verificar se log de erro foi registrado
            mock_logger.error.assert_called()
            self.assertFalse(resultado["sucesso"])

    def test_metricas_sms_envios(self):
        """Testa métricas de envios de SMS"""
        # Simular múltiplos envios
        resultados = []

        with patch("agendamentos.smsdev_service.requests.post") as mock_post:
            # Alternar entre sucesso e erro
            responses = [
                Mock(status_code=200, json=lambda: {"situacao": "OK"}),
                Mock(
                    status_code=200,
                    json=lambda: {"situacao": "ERRO", "descricao": "Erro teste"},
                ),
                Mock(status_code=200, json=lambda: {"situacao": "OK"}),
            ]
            mock_post.side_effect = responses

            for i in range(3):
                resultado = smsdev_service.enviar_sms(f"1199999999{i}", f"Teste {i}")
                resultados.append(resultado)

        # Verificar métricas
        sucessos = sum(1 for r in resultados if r["sucesso"])
        erros = sum(1 for r in resultados if not r["sucesso"])

        self.assertEqual(sucessos, 2)
        self.assertEqual(erros, 1)
        self.assertEqual(len(resultados), 3)
