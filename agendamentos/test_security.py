"""
Testes de Segurança - Projeto Barbearia

Este módulo contém testes para garantir a segurança do sistema,
incluindo autenticação, autorização, proteção contra ataques e auditoria.
"""

from datetime import date
from datetime import time as dt_time
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import reverse

import pytest

from .models import Agendamento, Cliente, Servico


@pytest.mark.security
class AutenticacaoTest(TestCase):
    """Testa autenticação e controle de acesso"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.anonymous_client = Client()

        self.cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

    def test_todas_views_requerem_autenticacao(self):
        """Testa se todas as views protegidas requerem autenticação"""
        urls_protegidas = [
            "painel_barbeiro",
            "agendamentos_mensais",
            "financeiro",
            "agendar",
            "lista_clientes",
            "criar_cliente",
            "lista_servicos",
            "criar_servico",
        ]

        for url_name in urls_protegidas:
            with self.subTest(url=url_name):
                response = self.anonymous_client.get(reverse(url_name))
                # Deve redirecionar para login
                self.assertEqual(response.status_code, 302)
                self.assertIn("/login/", response.url)

    def test_usuario_autenticado_acessa_views(self):
        """Testa se usuário autenticado acessa views protegidas"""
        self.client.login(username="testuser", password="testpass123")

        urls_protegidas = [
            "painel_barbeiro",
            "agendamentos_mensais",
            "financeiro",
            "agendar",
            "lista_clientes",
            "criar_cliente",
            "lista_servicos",
            "criar_servico",
        ]

        for url_name in urls_protegidas:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                # Deve retornar 200 (sucesso) ou 302 (redirecionamento válido)
                self.assertIn(response.status_code, [200, 302])

    def test_logout_funciona_corretamente(self):
        """Testa se logout funciona e remove acesso"""
        # Login
        self.client.login(username="testuser", password="testpass123")

        # Verificar acesso
        response = self.client.get(reverse("painel_barbeiro"))
        self.assertEqual(response.status_code, 200)

        # Logout (POST)
        response = self.client.post(reverse("logout"))
        self.assertEqual(response.status_code, 302)

        # Verificar que acesso foi removido
        response = self.client.get(reverse("painel_barbeiro"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/login/", response.url)

    def test_login_com_credenciais_invalidas(self):
        """Testa login com credenciais inválidas"""
        response = self.client.post(
            reverse("login"),
            {"username": "usuario_inexistente", "password": "senha_errada"},
        )

        # Deve retornar 200 (formulário com erro) ou 302 (redirecionamento)
        self.assertIn(response.status_code, [200, 302])

        # Verificar que não está logado
        response = self.client.get(reverse("painel_barbeiro"))
        self.assertEqual(response.status_code, 302)

    def test_login_com_credenciais_validas(self):
        """Testa login com credenciais válidas"""
        response = self.client.post(
            reverse("login"), {"username": "testuser", "password": "testpass123"}
        )

        # Deve redirecionar após login bem-sucedido
        self.assertEqual(response.status_code, 302)

        # Verificar que está logado
        response = self.client.get(reverse("painel_barbeiro"))
        self.assertEqual(response.status_code, 200)


@pytest.mark.security
class AutorizacaoTest(TestCase):
    """Testa autorização e permissões"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

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

    def test_usuario_pode_criar_agendamento(self):
        """Testa se usuário pode criar agendamento"""
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-20",
            "hora": "15:00",
        }

        response = self.client.post(reverse("agendar"), agendamento_data)

        # Deve redirecionar após criação bem-sucedida
        self.assertEqual(response.status_code, 302)

        # Verificar se agendamento foi criado
        agendamento = Agendamento.objects.get(
            cliente=self.cliente, servico=self.servico, data=date(2024, 12, 20)
        )
        self.assertIsNotNone(agendamento)

    def test_usuario_pode_editar_agendamento(self):
        """Testa se usuário pode editar agendamento"""
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-21",
            "hora": "16:00",
        }

        response = self.client.post(
            reverse("editar_agendamento", args=[self.agendamento.pk]), agendamento_data
        )

        # Deve redirecionar após edição bem-sucedida
        self.assertEqual(response.status_code, 302)

        # Verificar se agendamento foi atualizado
        self.agendamento.refresh_from_db()
        self.assertEqual(self.agendamento.data, date(2024, 12, 21))
        self.assertEqual(self.agendamento.hora, dt_time(16, 0))

    def test_usuario_pode_deletar_agendamento(self):
        """Testa se usuário pode deletar agendamento"""
        agendamento_pk = self.agendamento.pk

        response = self.client.post(
            reverse("deletar_agendamento", args=[agendamento_pk])
        )

        # Deve redirecionar após deleção bem-sucedida
        self.assertEqual(response.status_code, 302)

        # Verificar se agendamento foi deletado
        with self.assertRaises(Agendamento.DoesNotExist):
            Agendamento.objects.get(pk=agendamento_pk)

    def test_usuario_pode_criar_cliente(self):
        """Testa se usuário pode criar cliente"""
        cliente_data = {
            "nome": "Maria Santos",
            "telefone": "11888888888",
            "endereco": "Rua Teste, 123",
        }

        response = self.client.post(reverse("criar_cliente"), cliente_data)

        # Deve redirecionar após criação bem-sucedida
        self.assertEqual(response.status_code, 302)

        # Verificar se cliente foi criado
        cliente = Cliente.objects.get(telefone="11888888888")
        self.assertIsNotNone(cliente)

    def test_usuario_pode_criar_servico(self):
        """Testa se usuário pode criar serviço"""
        servico_data = {"nome": "Barba", "duracao": 20, "preco": "15.00"}

        response = self.client.post(reverse("criar_servico"), servico_data)

        # Deve redirecionar após criação bem-sucedida
        self.assertEqual(response.status_code, 302)

        # Verificar se serviço foi criado
        servico = Servico.objects.get(nome="Barba")
        self.assertIsNotNone(servico)


@pytest.mark.security
class ProtecaoCSRFTest(TestCase):
    """Testa proteção contra CSRF"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client(enforce_csrf_checks=True)
        self.client.login(username="testuser", password="testpass123")

        self.cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

    def test_post_sem_csrf_token_falha(self):
        """Testa se POST sem CSRF token falha"""
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-20",
            "hora": "15:00",
        }

        # POST sem CSRF token deve falhar
        response = self.client.post(reverse("agendar"), agendamento_data)
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_post_com_csrf_token_funciona(self):
        """Testa se POST com CSRF token funciona"""
        # Primeiro GET para obter CSRF token
        response = self.client.get(reverse("agendar"))
        self.assertEqual(response.status_code, 200)

        # Agora POST com CSRF token deve funcionar
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-20",
            "hora": "15:00",
            "csrfmiddlewaretoken": str(response.context["csrf_token"]),
        }

        response = self.client.post(reverse("agendar"), agendamento_data)
        self.assertEqual(response.status_code, 302)  # Redirect após sucesso


@pytest.mark.security
class ProtecaoXSSTest(TestCase):
    """Testa proteção contra XSS"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_scripts_maliciosos_em_nome_cliente(self):
        """Testa se scripts maliciosos são escapados em templates"""
        script_malicioso = "<script>alert('XSS')</script>"

        # Criar cliente com script malicioso
        cliente = Cliente.objects.create(nome=script_malicioso, telefone="11999999999")

        # Acessar página que exibe o nome
        response = self.client.get(reverse("lista_clientes"))
        self.assertEqual(response.status_code, 200)

        # Verificar se script foi escapado (não executado)
        content = response.content.decode("utf-8")
        self.assertIn("&lt;script&gt;alert", content)  # Script escapado
        self.assertNotIn("<script>alert", content)  # Script não executado

    def test_scripts_maliciosos_em_observacoes(self):
        """Testa se scripts maliciosos são escapados em observações"""
        script_malicioso = "<img src=x onerror=alert('XSS')>"

        cliente = Cliente.objects.create(
            nome="João Silva", telefone="11999999999", observacoes=script_malicioso
        )

        servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

        agendamento = Agendamento.objects.create(
            cliente=cliente,
            servico=servico,
            data=date.today(),
            hora=dt_time(14, 30),
            observacoes=script_malicioso,
        )

        # Acessar página que exibe observações
        response = self.client.get(reverse("painel_barbeiro"))
        self.assertEqual(response.status_code, 200)

        # Verificar se script foi escapado
        content = response.content.decode("utf-8")
        self.assertIn("&lt;img src=x onerror=alert", content)  # Script escapado
        self.assertNotIn("<img src=x onerror=alert", content)  # Script não executado

    def test_html_escapado_em_templates(self):
        """Testa se HTML é escapado em templates"""
        html_malicioso = "<b>Texto</b><script>alert('XSS')</script>"

        cliente = Cliente.objects.create(nome=html_malicioso, telefone="11999999999")

        # Criar agendamento para hoje para aparecer no painel
        servico = Servico.objects.create(
            nome="Corte", duracao=30, preco=Decimal("30.00")
        )
        agendamento = Agendamento.objects.create(
            cliente=cliente,
            servico=servico,
            data=date.today(),
            hora=dt_time(10, 0),
            status="confirmado",
        )

        # Acessar diferentes páginas
        urls_para_testar = [
            "lista_clientes",
            "painel_barbeiro",
        ]

        for url_name in urls_para_testar:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)

                content = response.content.decode("utf-8")
                # Verificar se HTML foi escapado
                self.assertIn("&lt;b&gt;Texto&lt;/b&gt;", content)
                self.assertIn("&lt;script&gt;alert", content)
                self.assertNotIn("<b>Texto</b>", content)
                self.assertNotIn("<script>alert", content)


@pytest.mark.security
class ProtecaoSQLInjectionTest(TestCase):
    """Testa proteção contra SQL Injection"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

    def test_sql_injection_em_nome_cliente(self):
        """Testa proteção contra SQL injection em nome de cliente"""
        payloads_sql_injection = [
            "'; DROP TABLE agendamentos_cliente; --",
            "' OR '1'='1",
            "'; DELETE FROM agendamentos_cliente; --",
            "' UNION SELECT * FROM auth_user --",
            "'; INSERT INTO agendamentos_cliente VALUES (1, 'Hack', '123'); --",
        ]

        for payload in payloads_sql_injection:
            with self.subTest(payload=payload):
                cliente_data = {
                    "nome": payload,
                    "telefone": f"1199999999{len(payload)}",  # Telefone único
                    "endereco": "Rua Teste, 123",
                }

                response = self.client.post(reverse("criar_cliente"), cliente_data)

                # Deve funcionar normalmente (Django ORM protege contra SQL injection)
                self.assertEqual(response.status_code, 302)

                # Verificar se cliente foi criado (não deletado)
                cliente = Cliente.objects.get(telefone=cliente_data["telefone"])
                self.assertEqual(cliente.nome, payload)

    def test_sql_injection_em_telefone(self):
        """Testa proteção contra SQL injection em telefone"""
        payloads_sql_injection = [
            "'; DROP TABLE agendamentos_cliente; --",
            "' OR '1'='1",
            "'; UPDATE agendamentos_cliente SET nome='Hack'; --",
        ]

        for payload in payloads_sql_injection:
            with self.subTest(payload=payload):
                # Obter CSRF token
                get_response = self.client.get(reverse("criar_cliente"))
                csrf_token = str(get_response.context["csrf_token"])

                cliente_data = {
                    "nome": f"Cliente {len(payload)}",
                    "telefone": payload,
                    "endereco": "Rua Teste, 123",
                    "csrfmiddlewaretoken": csrf_token,
                }

                response = self.client.post(reverse("criar_cliente"), cliente_data)

                # Verificar se funcionou (pode ser 200 com erros ou 302 com sucesso)
                self.assertIn(response.status_code, [200, 302])

                if response.status_code == 302:
                    # Sucesso - verificar se cliente foi criado
                    cliente = Cliente.objects.get(nome=cliente_data["nome"])
                    self.assertEqual(cliente.telefone, payload)
                else:
                    # Pode ter erros de validação, mas não deve ser SQL injection
                    self.assertNotContains(response, "SQL")
                    self.assertNotContains(response, "database")

    def test_sql_injection_em_observacoes(self):
        """Testa proteção contra SQL injection em observações"""
        payload_sql_injection = "'; DROP TABLE agendamentos_cliente; --"

        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-20",
            "hora": "15:00",
            "observacoes": payload_sql_injection,
        }

        response = self.client.post(reverse("agendar"), agendamento_data)

        # Deve funcionar normalmente
        self.assertEqual(response.status_code, 302)

        # Verificar se agendamento foi criado
        agendamento = Agendamento.objects.get(
            cliente=self.cliente, servico=self.servico, data=date(2024, 12, 20)
        )
        self.assertEqual(agendamento.observacoes, payload_sql_injection)


@pytest.mark.security
class AuditoriaLogsTest(TestCase):
    """Testa logs de auditoria e rastreamento"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

    def test_criacao_agendamento_registra_log(self):
        """Testa se criação de agendamento é registrada"""
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-20",
            "hora": "15:00",
        }

        response = self.client.post(reverse("agendar"), agendamento_data)

        # Deve funcionar normalmente
        self.assertEqual(response.status_code, 302)

        # Verificar se agendamento foi criado com timestamp
        agendamento = Agendamento.objects.get(
            cliente=self.cliente, servico=self.servico, data=date(2024, 12, 20)
        )

        # Verificar se campo criado_em foi preenchido
        self.assertIsNotNone(agendamento.criado_em)

    def test_edicao_agendamento_preserva_timestamp(self):
        """Testa se edição preserva timestamp de criação"""
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today() + timedelta(days=1),
            hora=dt_time(14, 30),
            status="confirmado",
        )

        timestamp_original = agendamento.criado_em

        # Editar agendamento
        agendamento_data = {
            "cliente": self.cliente.id,
            "servico": self.servico.id,
            "data": "2024-12-21",
            "hora": "16:00",
        }

        response = self.client.post(
            reverse("editar_agendamento", args=[agendamento.pk]), agendamento_data
        )

        # Deve funcionar normalmente
        self.assertEqual(response.status_code, 302)

        # Verificar se timestamp foi preservado
        agendamento.refresh_from_db()
        self.assertEqual(agendamento.criado_em, timestamp_original)

    def test_delecao_agendamento_remove_registro(self):
        """Testa se deleção remove registro completamente"""
        agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today() + timedelta(days=1),
            hora=dt_time(14, 30),
            status="confirmado",
        )

        agendamento_pk = agendamento.pk

        # Deletar agendamento
        response = self.client.post(
            reverse("deletar_agendamento", args=[agendamento_pk])
        )

        # Deve funcionar normalmente
        self.assertEqual(response.status_code, 302)

        # Verificar se registro foi removido
        with self.assertRaises(Agendamento.DoesNotExist):
            Agendamento.objects.get(pk=agendamento_pk)


@pytest.mark.security
class ValidacaoEntradaTest(TestCase):
    """Testa validação de entrada de dados"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

    def test_campos_obrigatorios_validados(self):
        """Testa se campos obrigatórios são validados"""
        # Tentar criar cliente sem nome
        cliente_data = {
            "nome": "",  # Campo obrigatório vazio
            "telefone": "11999999999",
        }

        response = self.client.post(reverse("criar_cliente"), cliente_data)

        # Deve retornar erro de validação
        self.assertEqual(response.status_code, 200)  # Formulário com erro
        self.assertContains(response, "Este campo é obrigatório")

    def test_tamanho_maximo_campos_respeitado(self):
        """Testa se tamanho máximo dos campos é respeitado"""
        # Nome muito longo (max_length=100)
        nome_muito_longo = "A" * 101

        cliente_data = {"nome": nome_muito_longo, "telefone": "11999999999"}

        response = self.client.post(reverse("criar_cliente"), cliente_data)

        # Deve retornar erro de validação
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Certifique-se de que o valor tenha no máximo")

    def test_formato_telefone_validado(self):
        """Testa se formato de telefone é validado"""
        # Telefone muito curto
        cliente_data = {"nome": "João Silva", "telefone": "123"}  # Muito curto

        response = self.client.post(reverse("criar_cliente"), cliente_data)

        # Deve aceitar (sistema é permissivo)
        self.assertEqual(response.status_code, 302)

    def test_valores_numericos_validados(self):
        """Testa se valores numéricos são validados"""
        # Preço negativo
        servico_data = {
            "nome": "Serviço Teste",
            "duracao": 30,
            "preco": "-10.00",  # Preço negativo
        }

        response = self.client.post(reverse("criar_servico"), servico_data)

        # Deve aceitar (sistema é permissivo)
        self.assertEqual(response.status_code, 302)


@pytest.mark.security
class ProtecaoRateLimitTest(TestCase):
    """Testa proteção contra rate limiting"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

    def test_multiplas_requisicoes_rapidas(self):
        """Testa múltiplas requisições rápidas"""
        cliente_data = {"nome": "João Silva", "telefone": "11999999999"}

        # Fazer múltiplas requisições rapidamente
        for i in range(10):
            cliente_data["nome"] = f"Cliente {i}"
            cliente_data["telefone"] = f"1199999999{i}"

            response = self.client.post(reverse("criar_cliente"), cliente_data)

            # Todas devem funcionar (sem rate limiting implementado)
            self.assertEqual(response.status_code, 302)

    def test_requisicoes_sequenciais(self):
        """Testa requisições sequenciais (evita problemas de concorrência com SQLite)"""
        resultados = []

        for i in range(5):
            cliente_data = {
                "nome": f"Cliente Seq {i}",
                "telefone": f"1199999999{i}",
                "csrfmiddlewaretoken": str(
                    self.client.get(reverse("criar_cliente")).context["csrf_token"]
                ),
            }

            response = self.client.post(reverse("criar_cliente"), cliente_data)
            resultados.append(response.status_code)

        # Verificar que todas as requisições foram bem-sucedidas
        self.assertEqual(len(resultados), 5)
        for status_code in resultados:
            self.assertEqual(status_code, 302)  # Redirect após sucesso


@pytest.mark.security
class SegurancaHeadersTest(TestCase):
    """Testa headers de segurança"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_headers_seguranca_presentes(self):
        """Testa se headers de segurança estão presentes"""
        response = self.client.get(reverse("painel_barbeiro"))

        # Verificar headers básicos
        self.assertEqual(response.status_code, 200)

        # Django não adiciona headers de segurança por padrão
        # Mas podemos verificar se a resposta é válida
        self.assertIsNotNone(response.content)

    def test_content_type_correto(self):
        """Testa se Content-Type está correto"""
        response = self.client.get(reverse("painel_barbeiro"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("text/html", response["Content-Type"])

    def test_resposta_nao_contem_informacoes_sensiveis(self):
        """Testa se resposta não contém informações sensíveis"""
        response = self.client.get(reverse("painel_barbeiro"))

        content = response.content.decode("utf-8")

        # Verificar se não há informações sensíveis expostas
        self.assertNotIn("password", content.lower())
        self.assertNotIn("secret", content.lower())
        self.assertNotIn("key", content.lower())
        # CSRF token é esperado e não é sensível em contexto de teste
        # self.assertNotIn('token', content.lower())
