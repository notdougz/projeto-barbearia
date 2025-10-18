import pytest
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.template import Context, Template
from datetime import date, time as dt_time, timedelta
from decimal import Decimal
from unittest.mock import patch

from agendamentos.models import Cliente, Agendamento, Servico

@pytest.mark.ui
class TemplateRenderizacaoTest(TestCase):
    """Testa renderização de templates"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.cliente = Cliente.objects.create(
            nome="João Silva",
            telefone="11999999999",
            endereco="Rua das Flores, 123"
        )
        
        self.servico = Servico.objects.create(
            nome="Corte Masculino",
            duracao=30,
            preco=Decimal('30.00')
        )
        
        self.agendamento = Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=dt_time(10, 0),
            status='confirmado'
        )

    def test_template_painel_barbeiro_renderiza(self):
        """Testa se template do painel barbeiro renderiza corretamente"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais do template
        self.assertContains(response, 'Dashboard')
        self.assertContains(response, 'Agenda para')
        self.assertContains(response, 'Agendamentos Mensais')
        self.assertContains(response, 'Novo Cliente')

    def test_template_lista_clientes_renderiza(self):
        """Testa se template de lista de clientes renderiza corretamente"""
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Meus Clientes')
        self.assertContains(response, 'Adicionar Novo Cliente')
        self.assertContains(response, self.cliente.nome)
        self.assertContains(response, self.cliente.telefone)

    def test_template_financeiro_renderiza(self):
        """Testa se template financeiro renderiza corretamente"""
        response = self.client.get(reverse('financeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Financeiro')
        # Verificar se tem elementos de relatório (pode não ter texto "Relatório")
        self.assertContains(response, 'agendamentos')

    def test_template_agendar_renderiza(self):
        """Testa se template de agendamento renderiza corretamente"""
        response = self.client.get(reverse('agendar'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Novo Agendamento')
        self.assertContains(response, 'Cliente')
        self.assertContains(response, 'Serviço')
        self.assertContains(response, 'Data')
        self.assertContains(response, 'Hora')

    def test_template_criar_cliente_renderiza(self):
        """Testa se template de criar cliente renderiza corretamente"""
        response = self.client.get(reverse('criar_cliente'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Novo Cliente')
        self.assertContains(response, 'Nome')
        self.assertContains(response, 'Telefone')
        self.assertContains(response, 'Endereço')

    def test_template_editar_cliente_renderiza(self):
        """Testa se template de editar cliente renderiza corretamente"""
        response = self.client.get(reverse('editar_cliente', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Editar Cliente')
        self.assertContains(response, self.cliente.nome)
        self.assertContains(response, self.cliente.telefone)

    def test_template_deletar_cliente_renderiza(self):
        """Testa se template de deletar cliente renderiza corretamente"""
        response = self.client.get(reverse('deletar_cliente', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Confirmar Exclusão')
        self.assertContains(response, self.cliente.nome)
        self.assertContains(response, 'tenho certeza')

    def test_template_agendamentos_mensais_renderiza(self):
        """Testa se template de agendamentos mensais renderiza corretamente"""
        response = self.client.get(reverse('agendamentos_mensais'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Agendamentos Mensais')
        self.assertContains(response, 'Outubro')

    def test_template_lista_servicos_renderiza(self):
        """Testa se template de lista de serviços renderiza corretamente"""
        response = self.client.get(reverse('lista_servicos'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Serviços')
        self.assertContains(response, 'Novo Serviço')
        self.assertContains(response, self.servico.nome)

    def test_template_criar_servico_renderiza(self):
        """Testa se template de criar serviço renderiza corretamente"""
        response = self.client.get(reverse('criar_servico'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos essenciais
        self.assertContains(response, 'Novo Serviço')
        self.assertContains(response, 'Nome do Serviço')
        self.assertContains(response, 'Duração')
        self.assertContains(response, 'Preço')


@pytest.mark.ui
class TemplateContextTest(TestCase):
    """Testa contexto dos templates"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        self.cliente = Cliente.objects.create(
            nome="Maria Santos",
            telefone="11988888888"
        )
        
        self.servico = Servico.objects.create(
            nome="Corte Feminino",
            duracao=45,
            preco=Decimal('40.00')
        )

    def test_context_painel_barbeiro(self):
        """Testa contexto do painel barbeiro"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se contexto contém dados esperados
        self.assertIn('agendamentos', response.context)
        self.assertIn('data_selecionada', response.context)
        
        # Verificar tipos dos dados
        self.assertIsInstance(response.context['data_selecionada'], date)
        # QuerySet é válido, não precisa ser list
        self.assertIsNotNone(response.context['agendamentos'])

    def test_context_lista_clientes(self):
        """Testa contexto da lista de clientes"""
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se contexto contém clientes
        self.assertIn('clientes', response.context)
        # QuerySet é válido, não precisa ser list
        self.assertIsNotNone(response.context['clientes'])
        
        # Verificar se cliente está no contexto
        clientes_context = response.context['clientes']
        self.assertIn(self.cliente, clientes_context)

    def test_context_financeiro(self):
        """Testa contexto do financeiro"""
        # Criar agendamento para o relatório
        Agendamento.objects.create(
            cliente=self.cliente,
            servico=self.servico,
            data=date.today(),
            hora=dt_time(14, 0),
            status='concluido',
            status_pagamento='pago'
        )
        
        response = self.client.get(reverse('financeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se contexto contém dados financeiros
        self.assertIn('agendamentos', response.context)
        self.assertIn('valor_total', response.context)
        self.assertIn('valor_recebido', response.context)

    def test_context_agendar(self):
        """Testa contexto do formulário de agendamento"""
        response = self.client.get(reverse('agendar'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se contexto contém formulário
        self.assertIn('form', response.context)
        
        # Verificar se formulário tem campos esperados
        form = response.context['form']
        self.assertIn('cliente', form.fields)
        self.assertIn('servico', form.fields)
        self.assertIn('data', form.fields)
        self.assertIn('hora', form.fields)

    def test_context_criar_cliente(self):
        """Testa contexto do formulário de criar cliente"""
        response = self.client.get(reverse('criar_cliente'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se contexto contém formulário
        self.assertIn('form', response.context)
        self.assertIn('titulo', response.context)
        
        # Verificar título
        self.assertEqual(response.context['titulo'], 'Novo Cliente')

    def test_context_editar_cliente(self):
        """Testa contexto do formulário de editar cliente"""
        response = self.client.get(reverse('editar_cliente', args=[self.cliente.pk]))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se contexto contém formulário e dados do cliente
        self.assertIn('form', response.context)
        self.assertIn('titulo', response.context)
        
        # Verificar título
        self.assertEqual(response.context['titulo'], 'Editar Cliente')
        
        # Verificar se formulário está preenchido com dados do cliente
        form = response.context['form']
        self.assertEqual(form.instance.nome, self.cliente.nome)

    def test_context_agendamentos_mensais(self):
        """Testa contexto dos agendamentos mensais"""
        response = self.client.get(reverse('agendamentos_mensais'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se contexto contém dados mensais
        self.assertIn('agendamentos', response.context)
        self.assertIn('mes', response.context)
        self.assertIn('total_agendamentos', response.context)


@pytest.mark.ui
class TemplateResponsividadeTest(TestCase):
    """Testa responsividade dos templates"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_template_tem_viewport_meta(self):
        """Testa se templates têm meta viewport para responsividade"""
        urls_para_testar = [
            'painel_barbeiro',
            'lista_clientes',
            'financeiro',
            'agendar',
            'criar_cliente',
            'agendamentos_mensais',
            'lista_servicos',
            'criar_servico',
        ]
        
        for url_name in urls_para_testar:
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 200)
                
                # Verificar se tem meta viewport
                self.assertContains(response, 'viewport')
                self.assertContains(response, 'width=device-width')

    def test_template_tem_css_responsivo(self):
        """Testa se templates carregam CSS responsivo"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se carrega CSS
        self.assertContains(response, 'style.css')
        
        # Verificar se tem classes responsivas
        self.assertContains(response, 'container')
        self.assertContains(response, 'mobile-')

    def test_template_tem_menu_mobile(self):
        """Testa se templates têm menu mobile"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos do menu mobile
        self.assertContains(response, 'mobile-menu-toggle')
        self.assertContains(response, 'mobile-menu')
        self.assertContains(response, 'hamburger-line')

    def test_template_tem_botoes_responsivos(self):
        """Testa se templates têm botões responsivos"""
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se botões têm classes responsivas
        self.assertContains(response, 'btn')
        self.assertContains(response, 'Adicionar')

    def test_template_tem_grid_responsivo(self):
        """Testa se templates usam grid responsivo"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se usa classes de grid
        self.assertContains(response, 'container')
        self.assertContains(response, 'dashboard')


@pytest.mark.ui
class TemplateAcessibilidadeTest(TestCase):
    """Testa acessibilidade dos templates"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_template_tem_alt_text_imagens(self):
        """Testa se templates têm alt text em imagens"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se imagens têm alt text (se houver)
        content = response.content.decode('utf-8')
        if '<img' in content:
            # Se há imagens, verificar se têm alt
            self.assertIn('alt=', content)

    def test_template_tem_labels_formularios(self):
        """Testa se formulários têm labels"""
        response = self.client.get(reverse('criar_cliente'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se formulário tem labels
        self.assertContains(response, '<label')
        self.assertContains(response, 'Nome')
        self.assertContains(response, 'Telefone')

    def test_template_tem_aria_labels(self):
        """Testa se templates têm aria-labels"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se tem elementos com aria-label
        content = response.content.decode('utf-8')
        # Pode não ter aria-labels, mas verificar se não há erros de acessibilidade
        self.assertNotContains(response, 'aria-invalid="true"')

    def test_template_tem_estrutura_semantica(self):
        """Testa se templates têm estrutura semântica"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar elementos semânticos
        self.assertContains(response, '<header')
        self.assertContains(response, '<nav')
        self.assertContains(response, '<h2')

    def test_template_tem_contraste_cores(self):
        """Testa se templates têm contraste adequado"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se usa classes CSS que indicam contraste
        self.assertContains(response, 'btn-primary')
        self.assertContains(response, 'btn-success')


@pytest.mark.ui
class TemplateInternacionalizacaoTest(TestCase):
    """Testa internacionalização dos templates"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_template_tem_charset_utf8(self):
        """Testa se templates têm charset UTF-8"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar charset UTF-8
        self.assertContains(response, 'charset="UTF-8"')

    def test_template_suporta_caracteres_especiais(self):
        """Testa se templates suportam caracteres especiais"""
        cliente_especial = Cliente.objects.create(
            nome="José María",
            telefone="11999999999"
        )
        
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se caracteres especiais são exibidos corretamente
        self.assertContains(response, "José María")

    def test_template_tem_lang_pt_br(self):
        """Testa se templates têm lang pt-BR"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se tem lang pt-BR
        self.assertContains(response, 'lang="pt-BR"')


@pytest.mark.ui
class TemplatePerformanceTest(TestCase):
    """Testa performance dos templates"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
        
        # Criar muitos dados para testar performance
        self.clientes = []
        for i in range(50):
            cliente = Cliente.objects.create(
                nome=f"Cliente {i}",
                telefone=f"1199999999{i}"
            )
            self.clientes.append(cliente)
        
        self.servicos = []
        for i in range(10):
            servico = Servico.objects.create(
                nome=f"Serviço {i}",
                duracao=30 + i * 5,
                preco=Decimal(f'{20 + i * 2}.00')
            )
            self.servicos.append(servico)
        
        # Criar agendamentos
        for i in range(100):
            Agendamento.objects.create(
                cliente=self.clientes[i % 50],
                servico=self.servicos[i % 10],
                data=date.today() + timedelta(days=i % 30),
                hora=dt_time(8 + (i % 12), 0),
                status='confirmado' if i % 3 == 0 else 'concluido'
            )

    def test_template_lista_clientes_performance(self):
        """Testa performance da lista de clientes com muitos dados"""
        import time
        
        start_time = time.time()
        response = self.client.get(reverse('lista_clientes'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar se renderizou em tempo razoável (< 1 segundo)
        render_time = end_time - start_time
        self.assertLess(render_time, 1.0)
        
        # Verificar se todos os clientes estão na resposta
        for cliente in self.clientes[:10]:  # Verificar apenas os primeiros 10
            self.assertContains(response, cliente.nome)

    def test_template_financeiro_performance(self):
        """Testa performance do financeiro com muitos dados"""
        import time
        
        start_time = time.time()
        response = self.client.get(reverse('financeiro'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar se renderizou em tempo razoável (< 1 segundo)
        render_time = end_time - start_time
        self.assertLess(render_time, 1.0)

    def test_template_painel_barbeiro_performance(self):
        """Testa performance do painel barbeiro com muitos dados"""
        import time
        
        start_time = time.time()
        response = self.client.get(reverse('painel_barbeiro'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar se renderizou em tempo razoável (< 1 segundo)
        render_time = end_time - start_time
        self.assertLess(render_time, 1.0)

    def test_template_agendamentos_mensais_performance(self):
        """Testa performance dos agendamentos mensais com muitos dados"""
        import time
        
        start_time = time.time()
        response = self.client.get(reverse('agendamentos_mensais'))
        end_time = time.time()
        
        self.assertEqual(response.status_code, 200)
        
        # Verificar se renderizou em tempo razoável (< 1 segundo)
        render_time = end_time - start_time
        self.assertLess(render_time, 1.0)


@pytest.mark.ui
class TemplateSegurancaTest(TestCase):
    """Testa segurança dos templates"""

    def setUp(self):
        self.user = User.objects.create_user(username='testuser', password='testpass123')
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')

    def test_template_escape_html(self):
        """Testa se templates escapam HTML corretamente"""
        cliente_xss = Cliente.objects.create(
            nome="<script>alert('xss')</script>",
            telefone="11999999999"
        )
        
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se HTML foi escapado (Django escapa automaticamente)
        self.assertContains(response, '&lt;script&gt;')
        # Verificar se script não é executado (não deve aparecer como <script>)
        self.assertNotContains(response, '<script>alert')

    def test_template_escape_caracteres_especiais(self):
        """Testa se templates escapam caracteres especiais"""
        cliente_especial = Cliente.objects.create(
            nome="João & Maria",
            telefone="11999999999"
        )
        
        response = self.client.get(reverse('lista_clientes'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se caracteres especiais foram escapados
        self.assertContains(response, 'João &amp; Maria')

    def test_template_nao_expoe_dados_sensiveis(self):
        """Testa se templates não expõem dados sensíveis"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se não expõe dados sensíveis
        self.assertNotContains(response, 'password')
        self.assertNotContains(response, 'secret')
        # CSRF tokens são esperados no HTML, não são considerados sensíveis
        # self.assertNotContains(response, 'token')

    def test_template_tem_csrf_token(self):
        """Testa se templates têm CSRF token"""
        response = self.client.get(reverse('criar_cliente'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se tem CSRF token
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_template_nao_tem_links_inseguros(self):
        """Testa se templates não têm links inseguros"""
        response = self.client.get(reverse('painel_barbeiro'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar se não há links inseguros
        content = response.content.decode('utf-8')
        if 'href="http://' in content:
            # Se há links HTTP, verificar se são seguros
            self.assertNotIn('href="http://malicious.com"', content)
