# 🚀 Guia de Deploy - Sistema de Barbearia

## 📋 Checklist Pré-Deploy

### ✅ Segurança
- [x] Arquivo `.env` não está no repositório
- [x] Credenciais sensíveis removidas do código
- [x] `.gitignore` configurado corretamente
- [x] Chaves de API em variáveis de ambiente

### ✅ Código
- [x] Código limpo e documentado
- [x] Dependências no `requirements.txt`
- [x] Migrações aplicadas
- [x] Testes funcionando (se houver)

### ✅ Documentação
- [x] README.md completo
- [x] Licença MIT
- [x] Guia de instalação
- [x] Exemplo de configuração

## 🌐 Opções de Deploy

### 1. **Heroku** (Recomendado para iniciantes)
```bash
# Instalar Heroku CLI
# Criar app
heroku create seu-app-barbearia

# Configurar variáveis de ambiente
heroku config:set SMS_ENABLED=True
heroku config:set SMSDEV_USUARIO=seu_email@exemplo.com
heroku config:set SMSDEV_TOKEN=sua_chave_token
heroku config:set SECRET_KEY=sua_chave_secreta
heroku config:set DEBUG=False

# Deploy
git push heroku main
heroku run python manage.py migrate
heroku run python manage.py createsuperuser
```

### 2. **Railway**
```bash
# Conectar repositório GitHub
# Configurar variáveis de ambiente no painel
# Deploy automático
```

### 3. **DigitalOcean App Platform**
```bash
# Conectar repositório GitHub
# Configurar build e run commands
# Configurar variáveis de ambiente
```

### 4. **VPS (Ubuntu + Nginx + Gunicorn)**
```bash
# Instalar dependências
sudo apt update
sudo apt install python3-pip nginx postgresql

# Configurar aplicação
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic

# Configurar Gunicorn
gunicorn --bind 0.0.0.0:8000 barbearia.wsgi:application

# Configurar Nginx
# Configurar SSL com Let's Encrypt
```

## 🔧 Configurações de Produção

### Variáveis de Ambiente Obrigatórias
```env
# Django
SECRET_KEY=sua_chave_super_secreta_aqui
DEBUG=False
ALLOWED_HOSTS=seu-dominio.com,www.seu-dominio.com

# SMS
SMS_ENABLED=True
SMSDEV_USUARIO=seu_email@exemplo.com
SMSDEV_TOKEN=sua_chave_token

# Banco de Dados (se usar PostgreSQL)
DATABASE_URL=postgresql://usuario:senha@localhost:5432/barbearia

# Arquivos Estáticos
STATIC_URL=https://seu-dominio.com/static/
MEDIA_URL=https://seu-dominio.com/media/
```

### Configurações de Segurança
```python
# settings.py
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
```

## 📱 Configuração do SMSDev

### 1. **Cadastro**
- Acesse: https://app.smsdev.com.br
- Crie sua conta
- Faça o login

### 2. **Obter Credenciais**
- Vá em "API" ou "Configurações"
- Copie seu Token/Chave
- Anote seu email cadastrado

### 3. **Configurar no Deploy**
```bash
# Heroku
heroku config:set SMSDEV_USUARIO=seu_email@exemplo.com
heroku config:set SMSDEV_TOKEN=sua_chave_token

# Railway/DigitalOcean
# Configure no painel de variáveis de ambiente
```

### 4. **Testar**
- Acesse seu site em produção
- Crie um agendamento de teste
- Marque como "À caminho"
- Verifique se o SMS foi enviado

## 🔍 Monitoramento

### Logs
```bash
# Heroku
heroku logs --tail

# Railway
# Verifique no painel

# VPS
tail -f /var/log/nginx/access.log
tail -f /var/log/gunicorn/error.log
```

### Métricas
- Uptime do site
- Tempo de resposta
- Erros 500/404
- Uso de recursos

## 🚨 Troubleshooting

### Problemas Comuns

#### 1. **SMS não funciona**
```bash
# Verificar logs
heroku logs --tail | grep SMS

# Verificar variáveis
heroku config | grep SMS
```

#### 2. **Erro 500**
```bash
# Verificar logs detalhados
heroku logs --tail

# Verificar migrações
heroku run python manage.py migrate
```

#### 3. **Arquivos estáticos não carregam**
```bash
# Coletar arquivos estáticos
heroku run python manage.py collectstatic --noinput
```

#### 4. **Banco de dados**
```bash
# Resetar banco (CUIDADO!)
heroku pg:reset DATABASE_URL
heroku run python manage.py migrate
```

## 📊 Performance

### Otimizações
- [ ] Cache com Redis
- [ ] CDN para arquivos estáticos
- [ ] Compressão Gzip
- [ ] Otimização de queries
- [ ] Paginação de listas

### Monitoramento
- [ ] Google Analytics
- [ ] Sentry para erros
- [ ] Uptime monitoring
- [ ] Performance monitoring

## 🔐 Segurança

### Checklist
- [ ] HTTPS configurado
- [ ] Headers de segurança
- [ ] Rate limiting
- [ ] Backup automático
- [ ] Monitoramento de logs
- [ ] Atualizações de segurança

## 📞 Suporte

### Contatos
- **SMSDev:** suporte@smsdev.com.br
- **Heroku:** https://help.heroku.com
- **Django:** https://docs.djangoproject.com

### Recursos
- **Documentação Django:** https://docs.djangoproject.com
- **Deploy Django:** https://docs.djangoproject.com/en/stable/howto/deployment/
- **SMSDev Docs:** https://smsdev.com.br/docs

---

## 🎯 Próximos Passos

1. **Escolha uma plataforma de deploy**
2. **Configure as variáveis de ambiente**
3. **Faça o deploy**
4. **Teste todas as funcionalidades**
5. **Configure domínio personalizado**
6. **Configure SSL/HTTPS**
7. **Configure monitoramento**
8. **Faça backup regular**

**Boa sorte com seu projeto! 🚀**
