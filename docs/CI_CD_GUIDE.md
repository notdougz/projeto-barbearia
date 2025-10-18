# 🚀 CI/CD - Guia Completo

## 📋 O que é CI/CD?

**CI/CD** significa **Continuous Integration** (Integração Contínua) e **Continuous Deployment** (Deploy Contínuo).

### 🔄 Como funciona:

1. **Você faz push** no código para o GitHub
2. **GitHub Actions executa** os testes automaticamente
3. **Se os testes passam**, faz deploy automático
4. **Se os testes falham**, você é notificado

## 🛠️ Arquivos Criados

### 📁 `.github/workflows/`

- `tests.yml` - Executa testes automaticamente
- `ci.yml` - CI completo com qualidade e segurança
- `deploy.yml` - Deploy automático para Railway

### 📄 Outros arquivos

- `pyproject.toml` - Configurações de qualidade do código
- `railway.toml` - Configuração do Railway
- `.gitignore` - Atualizado para CI/CD

## 🚀 Como Usar

### 1. **Configurar GitHub**

1. Vá para o seu repositório no GitHub
2. Clique em **Settings** → **Secrets and variables** → **Actions**
3. Adicione os seguintes secrets:

```
RAILWAY_TOKEN=seu_token_do_railway
RAILWAY_SERVICE_NAME=nome_do_servico
RAILWAY_DOMAIN=seu_dominio.railway.app
```

### 2. **Como obter o token do Railway**

```bash
# Instalar Railway CLI
npm install -g @railway/cli

# Login no Railway
railway login

# Obter token
railway auth
```

### 3. **Testar o CI/CD**

1. Faça uma pequena mudança no código
2. Faça commit e push:
   ```bash
   git add .
   git commit -m "teste: adicionando CI/CD"
   git push origin main
   ```
3. Vá para **Actions** no GitHub para ver o progresso

## 📊 O que cada workflow faz

### 🧪 `tests.yml` (Básico)

- ✅ Instala dependências
- ✅ Executa migrações
- ✅ Roda todos os testes
- ✅ Gera relatório de cobertura

### 🔍 `ci.yml` (Completo)

- ✅ Tudo do `tests.yml`
- ✅ Verifica formatação do código (Black)
- ✅ Verifica organização de imports (isort)
- ✅ Verifica linting (flake8)
- ✅ Verifica segurança (bandit)
- ✅ Verifica vulnerabilidades (safety)

### 🚀 `deploy.yml` (Deploy)

- ✅ Faz deploy para Railway
- ✅ Verifica se deploy funcionou
- ✅ Notifica resultado

## 🎯 Workflows Recomendados

### Para começar (Simples):

Use apenas `tests.yml` - executa testes básicos

### Para produção (Completo):

Use `ci.yml` + `deploy.yml` - qualidade completa + deploy

## 🔧 Comandos Úteis

### Executar testes localmente:

```bash
python -m pytest --cov=agendamentos --cov-report=html
```

### Formatar código:

```bash
black .
isort .
```

### Verificar qualidade:

```bash
flake8 .
bandit -r agendamentos/
```

## 📈 Monitoramento

### No GitHub:

- Vá para **Actions** para ver histórico
- Clique em um workflow para ver detalhes
- Baixe relatórios de cobertura

### No Railway:

- Veja logs de deploy
- Monitore performance
- Verifique se aplicação está funcionando

## 🚨 Troubleshooting

### ❌ Testes falhando

1. Execute localmente: `python -m pytest`
2. Verifique logs no GitHub Actions
3. Corrija erros e faça novo push

### ❌ Deploy falhando

1. Verifique secrets do GitHub
2. Confirme token do Railway
3. Veja logs no Railway dashboard

### ❌ Workflow não executa

1. Verifique se arquivo está em `.github/workflows/`
2. Confirme sintaxe YAML
3. Verifique branch (deve ser `main` ou `develop`)

## 🎉 Benefícios

✅ **Detecta bugs rapidamente**  
✅ **Deploy mais seguro**  
✅ **Qualidade consistente**  
✅ **Economiza tempo**  
✅ **Histórico de mudanças**  
✅ **Relatórios detalhados**

## 📚 Próximos Passos

1. **Configure os secrets** no GitHub
2. **Teste com uma mudança pequena**
3. **Monitore os resultados**
4. **Ajuste conforme necessário**

---

💡 **Dica**: Comece simples com `tests.yml` e vá adicionando mais funcionalidades conforme se sentir confortável!
