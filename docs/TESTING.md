# Guia de Testes - Sistema de Agendamento de Barbearia

Este documento descreve a estratégia de testes implementada no sistema de agendamento de barbearia, incluindo configuração, execução e manutenção dos testes.

## 📋 Índice

- [Visão Geral](#visão-geral)
- [Configuração](#configuração)
- [Estrutura de Testes](#estrutura-de-testes)
- [Executando Testes](#executando-testes)
- [Cobertura de Código](#cobertura-de-código)
- [Tipos de Testes](#tipos-de-testes)
- [Boas Práticas](#boas-práticas)
- [Troubleshooting](#troubleshooting)

## 🎯 Visão Geral

O sistema implementa uma estratégia abrangente de testes que cobre:

- **Testes Unitários**: Funcionalidades individuais
- **Testes de Integração**: Fluxos completos do sistema
- **Testes de Performance**: Comportamento com grandes volumes de dados
- **Testes de API**: Integração com serviços externos (SMS)
- **Testes de Validação**: Formulários e modelos
- **Testes de Segurança**: Autenticação, autorização e proteções
- **Testes de Banco de Dados**: Integridade e concorrência
- **Testes de Interface**: Templates e renderização
- **Testes de Edge Cases**: Cenários extremos e casos especiais

## ⚙️ Configuração

### Dependências

As seguintes dependências são necessárias para executar os testes:

```bash
# Instalar dependências de teste
pip install -r requirements.txt
```

### Arquivos de Configuração

#### `.coveragerc`

Configuração do coverage.py para medição de cobertura:

```ini
[run]
source = agendamentos
omit =
    */migrations/*
    */venv/*
    */env/*
    */tests/*
    */test_*.py
    manage.py
    */settings/*
    */__pycache__/*

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
title = Cobertura de Testes - Sistema de Agendamento

[report]
fail_under = 80
show_missing = True
skip_covered = False
```

#### `pytest.ini`

Configuração do pytest para execução de testes:

```ini
[tool:pytest]
DJANGO_SETTINGS_MODULE = projeto_barbeiro.settings
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --cov=agendamentos
    --cov-report=html
    --cov-report=term
    --cov-report=xml
    -v
markers =
    integration: Testes de integração
    performance: Testes de performance
    api: Testes de API
    validation: Testes de validação
    security: Testes de segurança
    database: Testes de banco de dados
    ui: Testes de interface
    edge_cases: Testes de cenários extremos
```

## 📁 Estrutura de Testes

```
agendamentos/
├── tests.py                    # Testes básicos originais
├── test_integration.py         # Testes de integração
├── test_performance.py        # Testes de performance
├── test_sms_api.py           # Testes de API SMS
├── test_validation.py        # Testes de validação
├── test_security.py          # Testes de segurança
├── test_database.py          # Testes de banco de dados
├── test_ui.py                # Testes de interface
└── test_edge_cases.py        # Testes de edge cases

docs/
└── TESTING.md                # Esta documentação
```

## 🚀 Executando Testes

### Todos os Testes

```bash
# Executar todos os testes
python manage.py test

# Com cobertura
coverage run --source='.' manage.py test
coverage report
coverage html
```

### Testes Específicos

```bash
# Testes de integração
python manage.py test agendamentos.test_integration

# Testes de performance
python manage.py test agendamentos.test_performance

# Testes de segurança
python manage.py test agendamentos.test_security

# Testes de API
python manage.py test agendamentos.test_sms_api

# Testes de validação
python manage.py test agendamentos.test_validation

# Testes de banco de dados
python manage.py test agendamentos.test_database

# Testes de interface
python manage.py test agendamentos.test_ui

# Testes de edge cases
python manage.py test agendamentos.test_edge_cases
```

### Com Pytest

```bash
# Executar com pytest
pytest agendamentos/

# Com marcadores específicos
pytest -m integration
pytest -m performance
pytest -m security
```

## 📊 Cobertura de Código

### Gerando Relatório

```bash
# Executar testes com cobertura
coverage run --source='.' manage.py test

# Relatório no terminal
coverage report

# Relatório HTML
coverage html

# Abrir relatório HTML
start htmlcov/index.html  # Windows
open htmlcov/index.html   # macOS
xdg-open htmlcov/index.html  # Linux
```

### Interpretando Cobertura

- **80%+**: Excelente cobertura
- **70-79%**: Boa cobertura
- **60-69%**: Cobertura aceitável
- **<60%**: Cobertura insuficiente

### Arquivos com Baixa Cobertura

Os seguintes arquivos podem ter cobertura mais baixa:

- `migrations/`: Migrações do banco de dados
- `settings/`: Configurações específicas
- `manage.py`: Script de gerenciamento

## 🧪 Tipos de Testes

### 1. Testes de Integração (`test_integration.py`)

Testam fluxos completos do sistema:

- **Fluxo Cliente-Serviço-Agendamento-SMS**: Criação completa de agendamento
- **Fluxo de Pagamento**: Processamento de pagamentos
- **Fluxo de Relatórios**: Geração de relatórios financeiros
- **Fluxo de Confirmação**: Confirmação de agendamentos

```python
@pytest.mark.integration
class FluxoCompletoTest(TestCase):
    def test_fluxo_cliente_servico_agendamento_sms(self):
        """Testa fluxo completo de criação de agendamento"""
        # Implementação do teste
```

### 2. Testes de Performance (`test_performance.py`)

Testam performance com grandes volumes de dados:

- **Views com muitos dados**: 100-500 agendamentos
- **Operações de banco**: Consultas otimizadas
- **Uso de memória**: Monitoramento de recursos
- **Tempo de resposta**: Limites aceitáveis

```python
@pytest.mark.performance
class PerformanceTest(TestCase):
    def test_view_com_muitos_dados(self):
        """Testa performance de view com muitos dados"""
        # Implementação do teste
```

### 3. Testes de API (`test_sms_api.py`)

Testam integração com APIs externas:

- **Serviço SMS**: Envio de mensagens
- **Mocks realistas**: Simulação de respostas
- **Tratamento de erros**: Cenários de falha
- **Validação de dados**: Formato correto

```python
@pytest.mark.api
class SMSAPITest(TestCase):
    @patch('agendamentos.smsdev_service.SMSDevService')
    def test_envio_sms_sucesso(self, mock_service):
        """Testa envio de SMS com sucesso"""
        # Implementação do teste
```

### 4. Testes de Validação (`test_validation.py`)

Testam validações de formulários e modelos:

- **Dados inválidos**: Campos obrigatórios
- **Formatos incorretos**: Datas, telefones
- **Limites de caracteres**: Campos de texto
- **Validações customizadas**: Regras de negócio

```python
@pytest.mark.validation
class ValidationTest(TestCase):
    def test_formulario_cliente_dados_invalidos(self):
        """Testa validação de formulário de cliente"""
        # Implementação do teste
```

### 5. Testes de Segurança (`test_security.py`)

Testam aspectos de segurança:

- **Autenticação**: Login/logout
- **Autorização**: Controle de acesso
- **CSRF**: Proteção contra ataques
- **XSS**: Escape de HTML
- **SQL Injection**: Proteção contra injeção

```python
@pytest.mark.security
class SecurityTest(TestCase):
    def test_autenticacao_obrigatoria(self):
        """Testa se autenticação é obrigatória"""
        # Implementação do teste
```

### 6. Testes de Banco de Dados (`test_database.py`)

Testam integridade e operações de banco:

- **Constraints**: Chaves estrangeiras
- **Transações**: Atomicidade
- **Concorrência**: Operações simultâneas
- **Otimizações**: Consultas eficientes

```python
@pytest.mark.database
class DatabaseTest(TransactionTestCase):
    def test_constraint_foreign_key(self):
        """Testa constraint de chave estrangeira"""
        # Implementação do teste
```

### 7. Testes de Interface (`test_ui.py`)

Testam templates e renderização:

- **Renderização**: Templates corretos
- **Conteúdo**: Dados exibidos
- **Responsividade**: Layout adaptativo
- **Acessibilidade**: Elementos semânticos

```python
@pytest.mark.ui
class TemplateTest(TestCase):
    def test_template_renderiza_corretamente(self):
        """Testa renderização de template"""
        # Implementação do teste
```

### 8. Testes de Edge Cases (`test_edge_cases.py`)

Testam cenários extremos:

- **Dados extremos**: Valores limites
- **Concorrência**: Operações simultâneas
- **Erros**: Tratamento de exceções
- **Performance**: Limites de recursos

```python
@pytest.mark.edge_cases
class EdgeCasesTest(TestCase):
    def test_dados_extremos(self):
        """Testa dados extremos"""
        # Implementação do teste
```

## ✅ Boas Práticas

### 1. Nomenclatura

- **Classes**: `NomeDoTesteTest`
- **Métodos**: `test_acao_resultado_esperado`
- **Arquivos**: `test_modulo.py`

### 2. Estrutura de Testes

```python
class ExemploTest(TestCase):
    def setUp(self):
        """Configuração inicial"""
        self.user = User.objects.create_user(...)
        self.client.login(...)

    def test_exemplo(self):
        """Descrição do teste"""
        # Arrange (Preparar)
        dados = {...}

        # Act (Executar)
        response = self.client.post(...)

        # Assert (Verificar)
        self.assertEqual(response.status_code, 200)
```

### 3. Isolamento

- Cada teste deve ser independente
- Usar `setUp()` para configuração comum
- Limpar dados entre testes

### 4. Mocks

- Usar mocks para serviços externos
- Simular comportamentos específicos
- Verificar chamadas de métodos

### 5. Assertions

- Usar assertions específicas
- Verificar múltiplos aspectos
- Incluir mensagens descritivas

## 🔧 Troubleshooting

### Problemas Comuns

#### 1. Erro de CSRF Token

```python
# Solução: Incluir token CSRF
response = self.client.post(url, data, follow=True)
```

#### 2. Erro de Autenticação

```python
# Solução: Fazer login antes dos testes
self.client.login(username='user', password='pass')
```

#### 3. Erro de Banco de Dados

```python
# Solução: Usar TransactionTestCase para testes de banco
class DatabaseTest(TransactionTestCase):
    pass
```

#### 4. Erro de Concorrência

```python
# Solução: Simplificar testes de concorrência para SQLite
def test_concorrencia_simplificada(self):
    # Implementação simplificada
```

### Debugging

#### 1. Verbose Output

```bash
python manage.py test -v 2
```

#### 2. Debugging Específico

```python
def test_debug(self):
    response = self.client.get(url)
    print(f"Status: {response.status_code}")
    print(f"Content: {response.content}")
```

#### 3. Logs de Teste

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📈 Métricas de Qualidade

### Cobertura Mínima

- **Código**: 80%
- **Views**: 90%
- **Models**: 85%
- **Forms**: 90%

### Performance

- **Views**: < 2 segundos
- **Consultas**: < 10 queries por view
- **Memória**: < 100MB por teste

### Segurança

- **Autenticação**: 100% das views protegidas
- **CSRF**: 100% dos formulários protegidos
- **XSS**: 100% do conteúdo escapado

## 🔄 Manutenção

### Atualizações Regulares

1. **Executar testes**: Diariamente
2. **Verificar cobertura**: Semanalmente
3. **Atualizar dependências**: Mensalmente
4. **Revisar testes**: Trimestralmente

### Adicionando Novos Testes

1. **Identificar funcionalidade**: O que testar
2. **Escolher tipo**: Unitário, integração, etc.
3. **Implementar teste**: Seguir padrões
4. **Verificar cobertura**: Atingir metas
5. **Documentar**: Atualizar este guia

## 📚 Recursos Adicionais

### Documentação Django

- [Django Testing](https://docs.djangoproject.com/en/stable/topics/testing/)
- [Django Test Client](https://docs.djangoproject.com/en/stable/topics/testing/tools/#the-test-client)

### Ferramentas

- [Coverage.py](https://coverage.readthedocs.io/)
- [Pytest](https://docs.pytest.org/)
- [Factory Boy](https://factoryboy.readthedocs.io/)

### Boas Práticas

- [Testing Best Practices](https://docs.python.org/3/library/unittest.html)
- [Django Testing Best Practices](https://docs.djangoproject.com/en/stable/topics/testing/best-practices/)

---

