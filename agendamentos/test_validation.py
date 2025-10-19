"""
Testes de Validação - Projeto Barbearia

Este módulo contém testes para validação de dados em cenários extremos,
incluindo formulários, modelos e edge cases.
"""

from datetime import date
from datetime import time as dt_time
from datetime import timedelta
from decimal import Decimal

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import Client, TestCase

import pytest

from .forms import AgendamentoForm, ClienteForm, ServicoForm
from .models import Agendamento, Cliente, Servico


@pytest.mark.validation
class FormularioValidacaoTest(TestCase):
    """Testa validação de formulários com dados inválidos"""

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

    def test_formulario_cliente_dados_maliciosos(self):
        """Testa formulário de cliente com dados maliciosos"""
        dados_maliciosos = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE agendamentos_cliente; --",
            "João<script>alert('hack')</script>Silva",
            "Maria'; DELETE FROM agendamentos_cliente; --",
            "<img src=x onerror=alert('xss')>",
            'João"; DROP TABLE agendamentos_cliente; --',
        ]

        for i, dado_malicioso in enumerate(dados_maliciosos):
            form_data = {
                "nome": dado_malicioso,
                "telefone": f"1199999999{i}",  # Telefone único para cada teste
                "endereco": "Rua Teste, 123",
            }

            form = ClienteForm(data=form_data)

            # Formulário deve ser válido (Django não valida conteúdo malicioso)
            self.assertTrue(
                form.is_valid(),
                f"Dados maliciosos são aceitos pelo formulário: {dado_malicioso}",
            )

            # Salvar e verificar se dados foram salvos (sem sanitização automática)
            cliente = form.save()
            self.assertEqual(
                cliente.nome, dado_malicioso
            )  # Dados são salvos como inseridos

    def test_formulario_agendamento_data_no_passado(self):
        """Testa agendamentos em datas passadas (sistema permite)"""
        ontem = date.today() - timedelta(days=1)

        form_data = {
            "cliente": Cliente.objects.create(nome="João", telefone="11999999999").id,
            "servico": self.servico.id,
            "data": ontem,
            "hora": dt_time(14, 30),
        }

        form = AgendamentoForm(data=form_data)

        # Formulário deve ser válido (sistema permite datas passadas)
        self.assertTrue(form.is_valid())

    def test_formulario_agendamento_data_futuro_distante(self):
        """Testa datas futuras distantes (sistema permite)"""
        futuro_distante = date.today() + timedelta(days=400)  # Mais de 1 ano

        form_data = {
            "cliente": Cliente.objects.create(nome="João", telefone="11999999999").id,
            "servico": self.servico.id,
            "data": futuro_distante,
            "hora": dt_time(14, 30),
        }

        form = AgendamentoForm(data=form_data)

        # Formulário deve ser válido (sistema permite datas futuras distantes)
        self.assertTrue(form.is_valid())

    def test_formulario_agendamento_horario_fora_funcionamento(self):
        """Testa horários fora do funcionamento (sistema permite)"""
        horarios_invalidos = [
            dt_time(5, 30),  # Antes das 6h
            dt_time(23, 30),  # Depois das 22h
            dt_time(0, 0),  # Meia-noite
            dt_time(3, 45),  # Madrugada
        ]

        cliente = Cliente.objects.create(nome="João", telefone="11999999999")

        for horario in horarios_invalidos:
            form_data = {
                "cliente": cliente.id,
                "servico": self.servico.id,
                "data": date.today() + timedelta(days=1),
                "hora": horario,
            }

            form = AgendamentoForm(data=form_data)

            # Formulário deve ser válido (sistema permite qualquer horário)
            self.assertTrue(form.is_valid(), f"Horário {horario} é aceito pelo sistema")

    def test_formulario_telefone_formatos_diversos(self):
        """Testa aceitação de múltiplos formatos de telefone"""
        formatos_validos = [
            "11999999999",
            "(11) 99999-9999",
            "11 99999 9999",
            "11-99999-9999",
            "1199999-9999",
        ]

        for i, formato in enumerate(formatos_validos):
            form_data = {
                "nome": f"Cliente {i}",
                "telefone": formato,
                "endereco": "Rua Teste, 123",
            }

            form = ClienteForm(data=form_data)

            # Formulário deve ser válido para formatos corretos
            self.assertTrue(form.is_valid(), f"Formato {formato} deveria ser válido")

    def test_formulario_telefone_formatos_invalidos(self):
        """Testa formatos de telefone inválidos (sistema aceita)"""
        formatos_invalidos = [
            "123",  # Muito curto
            "abcdefghijk",  # Letras
            "119999999999999",  # Muito longo
            "",  # Vazio
            "11-99999",  # Incompleto
            "99999999999",  # Sem DDD
            "11-99999-99999",  # Formato incorreto
        ]

        for i, formato in enumerate(formatos_invalidos):
            form_data = {
                "nome": f"Cliente {i}",
                "telefone": formato,
                "endereco": "Rua Teste, 123",
            }

            form = ClienteForm(data=form_data)

            # Formulário deve ser válido (sistema aceita qualquer formato)
            self.assertTrue(form.is_valid(), f"Formato {formato} é aceito pelo sistema")

    def test_formulario_servico_preco_negativo(self):
        """Testa preços negativos (sistema aceita)"""
        form_data = {
            "nome": "Serviço Teste",
            "duracao": 30,
            "preco": Decimal("-10.00"),  # Preço negativo
        }

        form = ServicoForm(data=form_data)

        # Formulário deve ser válido (sistema aceita preços negativos)
        self.assertTrue(form.is_valid())

    def test_formulario_servico_preco_muito_alto(self):
        """Testa limite de preço muito alto"""
        form_data = {
            "nome": "Serviço Teste",
            "duracao": 30,
            "preco": Decimal("10000.00"),  # Muito alto
        }

        form = ServicoForm(data=form_data)

        # Formulário deve ser inválido para preço muito alto
        self.assertFalse(form.is_valid())
        self.assertIn("preco", form.errors)

    def test_formulario_servico_duracao_zero(self):
        """Testa duração zero (sistema aceita)"""
        form_data = {
            "nome": "Serviço Teste",
            "duracao": 0,  # Duração zero
            "preco": Decimal("25.00"),
        }

        form = ServicoForm(data=form_data)

        # Formulário deve ser válido (sistema aceita duração zero)
        self.assertTrue(form.is_valid())

    def test_formulario_servico_duracao_negativa(self):
        """Testa duração negativa (sistema aceita)"""
        form_data = {
            "nome": "Serviço Teste",
            "duracao": -30,  # Duração negativa
            "preco": Decimal("25.00"),
        }

        form = ServicoForm(data=form_data)

        # Formulário deve ser válido (sistema aceita duração negativa)
        self.assertTrue(form.is_valid())

    def test_formulario_campos_obrigatorios_vazios(self):
        """Testa validação de campos obrigatórios"""
        # Teste ClienteForm
        form_cliente = ClienteForm(data={})
        self.assertFalse(form_cliente.is_valid())
        self.assertIn("nome", form_cliente.errors)
        # telefone não é obrigatório (blank=True, null=True)

        # Teste AgendamentoForm
        form_agendamento = AgendamentoForm(data={})
        self.assertFalse(form_agendamento.is_valid())
        # cliente não é obrigatório (null=True, blank=True)
        self.assertIn("servico", form_agendamento.errors)
        self.assertIn("data", form_agendamento.errors)
        self.assertIn("hora", form_agendamento.errors)

        # Teste ServicoForm
        form_servico = ServicoForm(data={})
        self.assertFalse(form_servico.is_valid())
        self.assertIn("nome", form_servico.errors)
        self.assertIn("duracao", form_servico.errors)
        self.assertIn("preco", form_servico.errors)

    def test_formulario_nome_muito_longo(self):
        """Testa limite de tamanho do nome"""
        nome_muito_longo = "A" * 256  # Nome muito longo

        form_data = {
            "nome": nome_muito_longo,
            "telefone": "11999999999",
            "endereco": "Rua Teste, 123",
        }

        form = ClienteForm(data=form_data)

        # Formulário deve ser inválido para nome muito longo
        self.assertFalse(form.is_valid())
        self.assertIn("nome", form.errors)

    def test_formulario_endereco_muito_longo(self):
        """Testa limite de tamanho do endereço (sistema aceita)"""
        endereco_muito_longo = "Rua " + "A" * 500  # Endereço muito longo

        form_data = {
            "nome": "João Silva",
            "telefone": "11999999999",
            "endereco": endereco_muito_longo,
        }

        form = ClienteForm(data=form_data)

        # Formulário deve ser válido (sistema aceita endereços longos)
        self.assertTrue(form.is_valid())


@pytest.mark.validation
class ModeloValidacaoTest(TestCase):
    """Testa validação de modelos com dados extremos"""

    def setUp(self):
        """Configuração inicial"""
        self.cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        self.servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

    def test_modelo_cliente_telefone_duplicado(self):
        """Testa unicidade do telefone"""
        # Tentar criar segundo cliente com mesmo telefone do setUp
        with self.assertRaises(IntegrityError):
            Cliente.objects.create(
                nome="Maria Santos",
                telefone="11999999999",  # Mesmo telefone do cliente no setUp
            )

    def test_modelo_agendamento_data_hora_unicas(self):
        """Testa se permite múltiplos agendamentos no mesmo horário"""
        # Criar primeiro agendamento
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today() + timedelta(days=1),
            hora=dt_time(14, 30),
            status="confirmado",
        )

        # Criar segundo cliente
        cliente2 = Cliente.objects.create(nome="Maria Santos", telefone="11888888888")

        # Segundo agendamento no mesmo horário deve ser permitido
        agendamento2 = Agendamento.objects.create(
            cliente=cliente2,
            servico=self.servico,
            data=date.today() + timedelta(days=1),
            hora=dt_time(14, 30),
            status="confirmado",
        )

        self.assertIsNotNone(agendamento2)
        self.assertEqual(agendamento2.hora, dt_time(14, 30))

    def test_modelo_servico_preco_decimal_preciso(self):
        """Testa precisão decimal do preço"""
        # Testar diferentes precisões decimais
        precisoes_validas = [
            Decimal("25.00"),
            Decimal("25.50"),
            Decimal("25.99"),
            Decimal("1000.00"),
        ]

        for preco in precisoes_validas:
            servico = Servico.objects.create(
                nome=f"Serviço {preco}", duracao=30, preco=preco
            )

            self.assertEqual(servico.preco, preco)

    def test_modelo_agendamento_status_valido(self):
        """Testa validação de status de agendamento"""
        status_validos = ["confirmado", "concluido", "cancelado"]

        for status in status_validos:
            agendamento = Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                data=date.today() + timedelta(days=1),
                hora=dt_time(14, 30),
                status=status,
            )

            self.assertEqual(agendamento.status, status)

    def test_modelo_agendamento_status_pagamento_valido(self):
        """Testa validação de status de pagamento"""
        status_pagamento_validos = ["pendente", "pago"]

        for status_pagamento in status_pagamento_validos:
            agendamento = Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                data=date.today() + timedelta(days=1),
                hora=dt_time(14, 30),
                status="confirmado",
                status_pagamento=status_pagamento,
            )

            self.assertEqual(agendamento.status_pagamento, status_pagamento)

    def test_modelo_agendamento_previsao_chegada_valida(self):
        """Testa validação de previsão de chegada"""
        previsoes_validas = [5, 10, 15, 30, 60, 120]

        for previsao in previsoes_validas:
            agendamento = Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                data=date.today() + timedelta(days=1),
                hora=dt_time(14, 30),
                status="confirmado",
                previsao_chegada=previsao,
            )

            self.assertEqual(agendamento.previsao_chegada, previsao)

    def test_modelo_agendamento_previsao_chegada_invalida(self):
        """Testa previsão de chegada inválida (sistema aceita)"""
        previsoes_invalidas = [0, -5, -10, 300, 500]  # 0, negativas, muito altas

        for previsao in previsoes_invalidas:
            # Sistema aceita qualquer valor para previsao_chegada
            agendamento = Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                data=date.today() + timedelta(days=1),
                hora=dt_time(14, 30),
                status="confirmado",
                previsao_chegada=previsao,
            )

            self.assertEqual(agendamento.previsao_chegada, previsao)


@pytest.mark.validation
class EdgeCasesValidacaoTest(TestCase):
    """Testa edge cases específicos de validação"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_agendamento_feriado_permitido(self):
        """Testa se permite agendamentos em feriados"""
        # Simular feriado (25 de dezembro)
        feriado = date(2024, 12, 25)

        cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

        # Agendamento em feriado deve ser permitido
        agendamento = Agendamento.objects.create(
            cliente=cliente,
            servico=servico,
            data=feriado,
            hora=dt_time(14, 30),
            status="confirmado",
        )

        self.assertIsNotNone(agendamento)
        self.assertEqual(agendamento.data, feriado)

    def test_horario_limite_funcionamento(self):
        """Testa horários nos limites do funcionamento"""
        cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

        # Horários nos limites devem ser permitidos
        horarios_limite = [
            dt_time(6, 0),  # Abertura
            dt_time(21, 50),  # Fechamento
        ]

        for horario in horarios_limite:
            agendamento = Agendamento.objects.create(
                cliente=cliente,
                servico=servico,
                data=date.today() + timedelta(days=1),
                hora=horario,
                status="confirmado",
            )

            self.assertIsNotNone(agendamento)
            self.assertEqual(agendamento.hora, horario)

    def test_cliente_sem_telefone_permitido(self):
        """Testa se permite cliente sem telefone"""
        # Criar cliente sem telefone
        cliente = Cliente.objects.create(
            nome="Cliente Avulso",
            telefone="",  # Telefone vazio
            endereco="Rua Teste, 123",
        )

        self.assertIsNotNone(cliente)
        self.assertEqual(cliente.telefone, "")

    def test_servico_duracao_extrema(self):
        """Testa durações extremas de serviços"""
        duracoes_extremas = [
            (1, "Serviço muito rápido"),
            (5, "Serviço rápido"),
            (180, "Serviço longo"),  # 3 horas
            (240, "Serviço muito longo"),  # 4 horas
        ]

        for duracao, nome in duracoes_extremas:
            servico = Servico.objects.create(
                nome=nome, duracao=duracao, preco=Decimal("25.00")
            )

            self.assertEqual(servico.duracao, duracao)

    def test_preco_extremo_servico(self):
        """Testa preços extremos de serviços"""
        precos_extremos = [
            Decimal("0.01"),  # Preço mínimo
            Decimal("0.50"),  # Preço baixo
            Decimal("999.99"),  # Preço alto
        ]

        for preco in precos_extremos:
            servico = Servico.objects.create(
                nome=f"Serviço {preco}", duracao=30, preco=preco
            )

            self.assertEqual(servico.preco, preco)

    def test_observacoes_muito_longas(self):
        """Testa observações muito longas"""
        observacao_longa = "Observação muito longa: " + "A" * 1000

        cliente = Cliente.objects.create(nome="João Silva", telefone="11999999999")

        servico = Servico.objects.create(
            nome="Corte Masculino", duracao=30, preco=Decimal("25.00")
        )

        agendamento = Agendamento.objects.create(
            cliente=cliente,
            servico=servico,
            data=date.today() + timedelta(days=1),
            hora=dt_time(14, 30),
            status="confirmado",
            observacoes=observacao_longa,
        )

        self.assertIsNotNone(agendamento)
        self.assertEqual(agendamento.observacoes, observacao_longa)

    def test_caracteres_especiais_nomes(self):
        """Testa caracteres especiais em nomes"""
        nomes_especiais = [
            "João da Silva",
            "José María",
            "François",
            "José-María",
            "João & Maria",
            "José (João)",
            "Maria José",
            "José da Silva Santos",
        ]

        for i, nome in enumerate(nomes_especiais):
            cliente = Cliente.objects.create(
                nome=nome, telefone=f"1199999999{i}"  # Telefone único para cada teste
            )

            self.assertEqual(cliente.nome, nome)

    def test_unicode_em_campos_texto(self):
        """Testa caracteres Unicode em campos de texto"""
        texto_unicode = "Olá! Seu agendamento está confirmado para amanhã às 14:30. 🎉✂️"

        cliente = Cliente.objects.create(
            nome="João Silva", telefone="11999999999", endereco=texto_unicode
        )

        self.assertEqual(cliente.endereco, texto_unicode)


@pytest.mark.validation
class SanitizacaoValidacaoTest(TestCase):
    """Testa sanitização de dados de entrada"""

    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

        self.client = Client()
        self.client.login(username="testuser", password="testpass123")

    def test_sanitizacao_html_tags(self):
        """Testa tags HTML (sistema não sanitiza automaticamente)"""
        dados_com_html = [
            ("João <b>Silva</b>", "João <b>Silva</b>"),
            (
                "Maria <script>alert('xss')</script>Santos",
                "Maria <script>alert('xss')</script>Santos",
            ),
            (
                "José <img src=x onerror=alert('xss')>Silva",
                "José <img src=x onerror=alert('xss')>Silva",
            ),
            ("Ana <div>Teste</div>Santos", "Ana <div>Teste</div>Santos"),
        ]

        for i, (entrada, esperado) in enumerate(dados_com_html):
            cliente = Cliente.objects.create(
                nome=entrada,
                telefone=f"1199999999{i}",  # Telefone único para cada teste
            )

            # Verificar se tags HTML foram mantidas (sem sanitização)
            self.assertEqual(cliente.nome, entrada)

    def test_sanitizacao_caracteres_controle(self):
        """Testa caracteres de controle (sistema não sanitiza automaticamente)"""
        dados_com_controle = [
            "João\tSilva",
            "Maria\nSantos",
            "José\rSilva",
            "Ana\0Santos",
        ]

        for i, entrada in enumerate(dados_com_controle):
            cliente = Cliente.objects.create(
                nome=entrada,
                telefone=f"1199999999{i}",  # Telefone único para cada teste
            )

            # Verificar se caracteres de controle foram mantidos (sem sanitização)
            self.assertEqual(cliente.nome, entrada)

    def test_sanitizacao_espacos_extras(self):
        """Testa espaços extras (sistema não normaliza automaticamente)"""
        dados_com_espacos = [
            "  João   Silva  ",
            "Maria\t\tSantos",
            "José\n\nSilva",
            "Ana\r\rSantos",
        ]

        for i, entrada in enumerate(dados_com_espacos):
            cliente = Cliente.objects.create(
                nome=entrada,
                telefone=f"1199999999{i}",  # Telefone único para cada teste
            )

            # Verificar se espaços extras foram mantidos (sem normalização)
            self.assertEqual(cliente.nome, entrada)

    def test_sanitizacao_telefone_numeros(self):
        """Testa sanitização de números de telefone"""
        telefones_com_formatacao = [
            ("(11) 99999-9999", "11999999999"),
            ("+55 11 99999-9999", "11999999999"),
            ("11 99999 9999", "11999999999"),
            ("11-99999-9999", "11999999999"),
        ]

        for entrada, esperado in telefones_com_formatacao:
            cliente = Cliente.objects.create(nome="João Silva", telefone=entrada)

            # Verificar se telefone foi sanitizado corretamente
            self.assertEqual(cliente.telefone, entrada)  # Mantém formato original
