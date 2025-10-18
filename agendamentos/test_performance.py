"""
Testes de Performance - Projeto Barbearia

Este módulo contém testes que verificam a performance do sistema
com volume médio de dados (100-500 agendamentos).
"""

import pytest
import time
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth.models import User
from django.urls import reverse
from django.db import connection
from django.test.utils import override_settings
from datetime import date, time as dt_time, datetime, timedelta
from decimal import Decimal
from unittest.mock import patch

from .models import Cliente, Servico, Agendamento


@pytest.mark.performance
class PerformanceViewsTest(TestCase):
    """Testa performance das views principais com volume de dados"""
    
    def setUp(self):
        """Configuração inicial com dados de volume médio"""
        # Criar usuário para autenticação
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Cliente para testes HTTP
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Criar serviços
        self.servicos = []
        for i in range(5):
            servico = Servico.objects.create(
                nome=f"Serviço {i+1}",
                duracao=30 + (i * 10),
                preco=Decimal(f'{20 + (i * 5)}.00')
            )
            self.servicos.append(servico)
        
        # Criar clientes (300 clientes)
        self.clientes = []
        for i in range(300):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i+1:03d}",
                telefone=f"11999{i:05d}",
                endereco=f"Rua {i+1}, {100 + i}"
            )
            self.clientes.append(cliente)
    
    def test_painel_barbeiro_com_500_agendamentos(self):
        """Testa painel do barbeiro com 500 agendamentos"""
        # Criar 500 agendamentos para hoje
        hoje = date.today()
        agendamentos_criados = []
        
        for i in range(500):
            cliente = self.clientes[i % len(self.clientes)]
            servico = self.servicos[i % len(self.servicos)]
            
            # Distribuir horários ao longo do dia
            hora = dt_time(8 + (i % 12), (i * 5) % 60)
            
            agendamento = Agendamento.objects.create(
                cliente=cliente,
                servico=servico,
                data=hoje,
                hora=hora,
                status='confirmado' if i % 3 == 0 else 'concluido',
                status_pagamento='pago' if i % 2 == 0 else 'pendente'
            )
            agendamentos_criados.append(agendamento)
        
        # Medir tempo de resposta
        start_time = time.time()
        response = self.client.get(reverse('painel_barbeiro'))
        end_time = time.time()
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar performance (< 2 segundos)
        response_time = end_time - start_time
        self.assertLess(response_time, 2.0, f"Painel demorou {response_time:.2f}s, esperado < 2s")
        
        # Verificar se todos os agendamentos estão sendo exibidos
        self.assertContains(response, 'Cliente 001')
        self.assertContains(response, 'Cliente 100')
        
        print(f"OK Painel com 500 agendamentos: {response_time:.2f}s")
    
    def test_lista_clientes_com_300_clientes(self):
        """Testa lista de clientes com 300 clientes"""
        # Medir tempo de resposta
        start_time = time.time()
        response = self.client.get(reverse('lista_clientes'))
        end_time = time.time()
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar performance (< 1 segundo)
        response_time = end_time - start_time
        self.assertLess(response_time, 1.0, f"Lista clientes demorou {response_time:.2f}s, esperado < 1s")
        
        # Verificar se clientes estão sendo exibidos
        self.assertContains(response, 'Cliente 001')
        self.assertContains(response, 'Cliente 300')
        
        print(f"OK Lista com 300 clientes: {response_time:.2f}s")
    
    def test_relatorio_financeiro_mensal_performance(self):
        """Testa performance do relatório financeiro mensal"""
        # Criar agendamentos para o mês atual
        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        
        # Criar 200 agendamentos distribuídos pelo mês
        for i in range(200):
            cliente = self.clientes[i % len(self.clientes)]
            servico = self.servicos[i % len(self.servicos)]
            
            # Distribuir pelo mês
            dia = 1 + (i % 28)  # Evitar dias inválidos
            data_agendamento = inicio_mes.replace(day=dia)
            hora = dt_time(8 + (i % 12), (i * 5) % 60)
            
            Agendamento.objects.create(
                cliente=cliente,
                servico=servico,
                data=data_agendamento,
                hora=hora,
                status='concluido',
                status_pagamento='pago' if i % 2 == 0 else 'pendente'
            )
        
        # Medir tempo de resposta
        start_time = time.time()
        response = self.client.get(reverse('financeiro'))
        end_time = time.time()
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar performance (< 1 segundo)
        response_time = end_time - start_time
        self.assertLess(response_time, 1.0, f"Relatório financeiro demorou {response_time:.2f}s, esperado < 1s")
        
        # Verificar se dados estão sendo calculados
        self.assertIn('valor_recebido', response.context)
        self.assertIn('valor_pendente', response.context)
        
        print(f"OK Relatorio financeiro: {response_time:.2f}s")
    
    def test_agendamentos_mensais_performance(self):
        """Testa performance da view de agendamentos mensais"""
        # Criar agendamentos para diferentes meses
        hoje = date.today()
        
        # Criar 150 agendamentos distribuídos por 3 meses
        for i in range(150):
            cliente = self.clientes[i % len(self.clientes)]
            servico = self.servicos[i % len(self.servicos)]
            
            # Distribuir por meses
            mes_offset = i % 3
            data_agendamento = hoje.replace(day=1 + (i % 28))
            if mes_offset == 1:
                data_agendamento = data_agendamento.replace(month=data_agendamento.month - 1)
            elif mes_offset == 2:
                data_agendamento = data_agendamento.replace(month=data_agendamento.month + 1)
            
            hora = dt_time(8 + (i % 12), (i * 5) % 60)
            
            Agendamento.objects.create(
                cliente=cliente,
                servico=servico,
                data=data_agendamento,
                hora=hora,
                status='concluido'
            )
        
        # Medir tempo de resposta
        start_time = time.time()
        response = self.client.get(reverse('agendamentos_mensais'))
        end_time = time.time()
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar performance (< 1.5 segundos)
        response_time = end_time - start_time
        self.assertLess(response_time, 1.5, f"Agendamentos mensais demorou {response_time:.2f}s, esperado < 1.5s")
        
        # Verificar se dados estão sendo exibidos
        self.assertIn('agendamentos', response.context)
        self.assertIn('total_agendamentos', response.context)
        
        print(f"OK Agendamentos mensais: {response_time:.2f}s")


@pytest.mark.performance
class PerformanceQueriesTest(TestCase):
    """Testa otimização de queries e detecção de N+1"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Criar dados de teste
        self.servico = Servico.objects.create(
            nome="Corte Masculino",
            duracao=30,
            preco=Decimal('25.00')
        )
        
        # Criar 100 clientes com agendamentos
        self.clientes = []
        for i in range(100):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i+1:03d}",
                telefone=f"11999{i:05d}"
            )
            self.clientes.append(cliente)
            
            # Criar 2 agendamentos por cliente
            for j in range(2):
                Agendamento.objects.create(
                    cliente=cliente,
                    servico=self.servico,
                    data=date.today() + timedelta(days=j),
                    hora=dt_time(10 + j, 0),
                    status='concluido'
                )
    
    def test_queries_n_plus_1_painel_barbeiro(self):
        """Testa se há queries N+1 no painel do barbeiro"""
        # Contar queries antes da requisição
        initial_queries = len(connection.queries)
        
        # Fazer requisição
        response = self.client.get(reverse('painel_barbeiro'))
        
        # Contar queries após a requisição
        final_queries = len(connection.queries)
        queries_executed = final_queries - initial_queries
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se não há muitas queries (indicativo de N+1)
        # Com 200 agendamentos, esperamos no máximo 5-10 queries
        self.assertLess(queries_executed, 15, 
                       f"Muitas queries executadas: {queries_executed}. Possível N+1 problem.")
        
        print(f"OK Queries no painel: {queries_executed}")
    
    def test_queries_n_plus_1_lista_clientes(self):
        """Testa se há queries N+1 na lista de clientes"""
        # Contar queries antes da requisição
        initial_queries = len(connection.queries)
        
        # Fazer requisição
        response = self.client.get(reverse('lista_clientes'))
        
        # Contar queries após a requisição
        final_queries = len(connection.queries)
        queries_executed = final_queries - initial_queries
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se não há muitas queries
        self.assertLess(queries_executed, 5, 
                       f"Muitas queries executadas: {queries_executed}. Possível N+1 problem.")
        
        print(f"OK Queries na lista clientes: {queries_executed}")
    
    def test_queries_n_plus_1_financeiro(self):
        """Testa se há queries N+1 no relatório financeiro"""
        # Contar queries antes da requisição
        initial_queries = len(connection.queries)
        
        # Fazer requisição
        response = self.client.get(reverse('financeiro'))
        
        # Contar queries após a requisição
        final_queries = len(connection.queries)
        queries_executed = final_queries - initial_queries
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se não há muitas queries
        self.assertLess(queries_executed, 10, 
                       f"Muitas queries executadas: {queries_executed}. Possível N+1 problem.")
        
        print(f"OK Queries no financeiro: {queries_executed}")


@pytest.mark.performance
class PerformanceDatabaseTest(TransactionTestCase):
    """Testa performance de operações de banco de dados"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Criar serviços
        self.servicos = []
        for i in range(10):
            servico = Servico.objects.create(
                nome=f"Serviço {i+1}",
                duracao=30,
                preco=Decimal(f'{20 + i}.00')
            )
            self.servicos.append(servico)
    
    def test_criacao_massa_agendamentos(self):
        """Testa performance na criação de muitos agendamentos"""
        # Criar 500 clientes
        clientes = []
        for i in range(500):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i+1:03d}",
                telefone=f"11999{i:05d}"
            )
            clientes.append(cliente)
        
        # Medir tempo de criação de 1000 agendamentos
        start_time = time.time()
        
        agendamentos = []
        for i in range(1000):
            cliente = clientes[i % len(clientes)]
            servico = self.servicos[i % len(self.servicos)]
            
            agendamento = Agendamento(
                cliente=cliente,
                servico=servico,
                data=date.today() + timedelta(days=i % 30),
                hora=dt_time(8 + (i % 12), (i * 5) % 60),
                status='confirmado'
            )
            agendamentos.append(agendamento)
        
        # Criar em lote para melhor performance
        Agendamento.objects.bulk_create(agendamentos)
        
        end_time = time.time()
        creation_time = end_time - start_time
        
        # Verificar se todos foram criados
        total_agendamentos = Agendamento.objects.count()
        self.assertEqual(total_agendamentos, 1000)
        
        # Verificar performance (< 5 segundos para 1000 agendamentos)
        self.assertLess(creation_time, 5.0, 
                       f"Criação de 1000 agendamentos demorou {creation_time:.2f}s, esperado < 5s")
        
        print(f"OK Criacao de 1000 agendamentos: {creation_time:.2f}s")
    
    def test_busca_clientes_performance(self):
        """Testa performance de busca de clientes"""
        # Criar 1000 clientes
        clientes = []
        for i in range(1000):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i+1:04d}",
                telefone=f"11999{i:05d}",
                endereco=f"Rua {i+1}, {100 + i}"
            )
            clientes.append(cliente)
        
        # Testar busca por nome
        start_time = time.time()
        clientes_encontrados = Cliente.objects.filter(nome__icontains="Cliente 100").count()
        end_time = time.time()
        
        search_time = end_time - start_time
        
        # Verificar se encontrou clientes
        self.assertGreater(clientes_encontrados, 0)
        
        # Verificar performance (< 100ms)
        self.assertLess(search_time, 0.1, 
                       f"Busca por nome demorou {search_time:.3f}s, esperado < 0.1s")
        
        print(f"OK Busca por nome: {search_time:.3f}s")
    
    def test_agregacoes_performance(self):
        """Testa performance de agregações"""
        # Criar dados de teste
        servico = Servico.objects.create(
            nome="Corte",
            duracao=30,
            preco=Decimal('25.00')
        )
        
        # Criar 500 agendamentos com diferentes status
        for i in range(500):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i+1:03d}",
                telefone=f"11999{i:05d}"
            )
            
            Agendamento.objects.create(
                cliente=cliente,
                servico=servico,
                data=date.today() + timedelta(days=i % 30),
                hora=dt_time(8 + (i % 12), 0),
                status='concluido' if i % 2 == 0 else 'confirmado',
                status_pagamento='pago' if i % 3 == 0 else 'pendente'
            )
        
        # Testar agregação de receita
        start_time = time.time()
        
        from django.db.models import Sum, Count
        receita_total = Agendamento.objects.filter(
            status='concluido',
            status_pagamento='pago'
        ).aggregate(
            total=Sum('servico__preco'),
            count=Count('id')
        )
        
        end_time = time.time()
        aggregation_time = end_time - start_time
        
        # Verificar se cálculo está correto
        self.assertIsNotNone(receita_total['total'])
        self.assertGreater(receita_total['count'], 0)
        
        # Verificar performance (< 200ms)
        self.assertLess(aggregation_time, 0.2, 
                       f"Agregação demorou {aggregation_time:.3f}s, esperado < 0.2s")
        
        print(f"OK Agregacao de receita: {aggregation_time:.3f}s")


@pytest.mark.performance
class PerformanceConcurrencyTest(TransactionTestCase):
    """Testa performance em cenários de concorrência"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.cliente = Cliente.objects.create(
            nome="Cliente Teste",
            telefone="11999999999"
        )
        
        self.servico = Servico.objects.create(
            nome="Corte",
            duracao=30,
            preco=Decimal('25.00')
        )
    
    def test_criacao_sequencial_agendamentos(self):
        """Testa performance com criação sequencial de agendamentos"""
        # Medir tempo de criação de 150 agendamentos sequencialmente
        start_time = time.time()
        
        for i in range(150):
            Agendamento.objects.create(
                cliente=self.cliente,
                servico=self.servico,
                data=date.today() + timedelta(days=i % 7),
                hora=dt_time(8 + (i % 12), 0),
                status='confirmado'
            )
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Verificar se todos os agendamentos foram criados
        total_agendamentos = Agendamento.objects.count()
        self.assertEqual(total_agendamentos, 150)
        
        # Verificar performance (< 3 segundos)
        self.assertLess(total_time, 3.0, 
                       f"Criação sequencial demorou {total_time:.2f}s, esperado < 3s")
        
        print(f"OK Criacao sequencial (150 agendamentos): {total_time:.2f}s")


@pytest.mark.performance
class PerformanceMemoryTest(TestCase):
    """Testa uso de memória em operações com muitos dados"""
    
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_memoria_lista_grande_clientes(self):
        """Testa uso de memória ao listar muitos clientes"""
        import psutil
        import os
        
        # Obter processo atual
        process = psutil.Process(os.getpid())
        
        # Medir memória antes
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Criar 1000 clientes
        clientes = []
        for i in range(1000):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i+1:04d}",
                telefone=f"11999{i:05d}"
            )
            clientes.append(cliente)
        
        # Medir memória após criação
        memory_after_creation = process.memory_info().rss / 1024 / 1024  # MB
        
        # Fazer requisição para lista de clientes
        response = self.client.get(reverse('lista_clientes'))
        
        # Medir memória após requisição
        memory_after_request = process.memory_info().rss / 1024 / 1024  # MB
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se uso de memória não é excessivo
        memory_increase = memory_after_request - memory_before
        self.assertLess(memory_increase, 100,  # < 100MB de aumento
                       f"Aumento de memória: {memory_increase:.1f}MB, esperado < 100MB")
        
        print(f"OK Uso de memoria: {memory_increase:.1f}MB")
    
    def test_memoria_relatorio_complexo(self):
        """Testa uso de memória em relatório complexo"""
        import psutil
        import os
        
        # Obter processo atual
        process = psutil.Process(os.getpid())
        
        # Medir memória antes
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        # Criar dados complexos
        servico = Servico.objects.create(
            nome="Corte",
            duracao=30,
            preco=Decimal('25.00')
        )
        
        # Criar 500 agendamentos com clientes
        for i in range(500):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i+1:03d}",
                telefone=f"11999{i:05d}"
            )
            
            Agendamento.objects.create(
                cliente=cliente,
                servico=servico,
                data=date.today() + timedelta(days=i % 30),
                hora=dt_time(8 + (i % 12), 0),
                status='concluido',
                status_pagamento='pago' if i % 2 == 0 else 'pendente'
            )
        
        # Fazer requisição para relatório financeiro
        response = self.client.get(reverse('financeiro'))
        
        # Medir memória após requisição
        memory_after = process.memory_info().rss / 1024 / 1024  # MB
        
        # Verificar sucesso
        self.assertEqual(response.status_code, 200)
        
        # Verificar se uso de memória não é excessivo
        memory_increase = memory_after - memory_before
        self.assertLess(memory_increase, 50,  # < 50MB de aumento
                       f"Aumento de memória: {memory_increase:.1f}MB, esperado < 50MB")
        
        print(f"OK Uso de memoria relatorio: {memory_increase:.1f}MB")
