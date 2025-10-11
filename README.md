# 💇‍♂️ Sistema de Agendamento para Barbearia

![Django](https://img.shields.io/badge/Django-5.2.7-green)
![Python](https://img.shields.io/badge/Python-3.12-blue)
![SMS](https://img.shields.io/badge/SMS-SMSDev-orange)
![Status](https://img.shields.io/badge/Status-Produção-brightgreen)

## 📋 Sobre o Projeto

Sistema completo de agendamento para barbearia desenvolvido em Django, com funcionalidades avançadas de gestão de clientes, serviços, agendamentos e notificações por SMS. Ideal para barbearias que desejam modernizar seu atendimento e melhorar a experiência do cliente.

## ✨ Funcionalidades

### 🎯 Gestão de Agendamentos
- ✅ Cadastro e edição de agendamentos
- ✅ Visualização por data com calendário
- ✅ Status em tempo real (Agendado, Confirmado, À caminho, Concluído)
- ✅ Previsão de chegada do barbeiro
- ✅ Histórico completo de atendimentos

### 👥 Gestão de Clientes
- ✅ Cadastro completo de clientes
- ✅ Informações de contato e endereço
- ✅ Histórico de serviços realizados
- ✅ Busca e filtros avançados

### 💼 Gestão de Serviços
- ✅ Cadastro de serviços oferecidos
- ✅ Definição de preços
- ✅ Tempo estimado por serviço
- ✅ Categorização de serviços

### 📱 Notificações por SMS
- ✅ Integração com SMSDev (API brasileira)
- ✅ Notificação automática "barbeiro a caminho"
- ✅ Previsão de chegada personalizada
- ✅ Logs detalhados de envio

### 📊 Relatórios Financeiros
- ✅ Relatório mensal de faturamento
- ✅ Análise por serviço
- ✅ Controle de pagamentos
- ✅ Exportação de dados

### 🔐 Sistema de Autenticação
- ✅ Login seguro para barbeiros
- ✅ Controle de acesso
- ✅ Sessões seguras

## 🚀 Tecnologias Utilizadas

- **Backend:** Django, Python
- **Frontend:** HTML5, CSS3, JavaScript
- **Banco de Dados:** SQLite (desenvolvimento) / PostgreSQL (produção)
- **SMS:** SMSDev API
- **Autenticação:** Django Auth System
- **Deploy:** Configurado para produção

## 📦 Instalação

### Pré-requisitos
- Python 3.8+
- pip
- Git

### Passo a Passo

1. **Clone o repositório**
```bash
git clone https://github.com/notdougz/projeto-barbeiro.git
cd projeto-barbeiro
```

2. **Crie e ative o ambiente virtual**
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instale as dependências**
```bash
pip install -r requirements.txt
```

4. **Configure as variáveis de ambiente**
```bash
cp env_example.txt .env
# Edite o arquivo .env com suas configurações
```

5. **Execute as migrações**
```bash
python manage.py migrate
```

6. **Crie um superusuário**
```bash
python manage.py createsuperuser
```

7. **Inicie o servidor**
```bash
python manage.py runserver
```

## ⚙️ Configuração

### Configuração do SMS

1. **Cadastre-se no SMSDev:** https://app.smsdev.com.br
2. **Obtenha suas credenciais** no painel da API
3. **Configure no arquivo .env:**
```env
SMS_ENABLED=True
SMSDEV_USUARIO=seu_email@exemplo.com
SMSDEV_TOKEN=sua_chave_token
```

### Configuração para Produção

1. **Configure o banco de dados PostgreSQL**
2. **Configure variáveis de ambiente de produção**
3. **Configure servidor web (Nginx + Gunicorn)**
4. **Configure SSL/HTTPS**
5. **Configure domínio personalizado**

## 📱 Como Usar

### Para Barbeiros
1. **Faça login** no sistema
2. **Visualize agendamentos** do dia
3. **Confirme atendimentos** quando necessário
4. **Marque "À caminho"** para enviar SMS automático
5. **Conclua atendimentos** após finalização


## 🎨 Interface

### Painel Principal
- Calendário interativo
- Lista de agendamentos do dia
- Status visual dos atendimentos
- Botões de ação rápida

### Gestão de Clientes
- Formulário completo de cadastro
- Lista paginada com busca
- Histórico de serviços
- Edição e exclusão segura

### Relatórios
- Dashboard financeiro
- Gráficos de faturamento
- Análise por período
- Exportação de dados

## 🔒 Segurança

- ✅ Autenticação segura
- ✅ Proteção CSRF
- ✅ Validação de dados
- ✅ Sanitização de inputs
- ✅ Logs de auditoria
- ✅ Controle de acesso

## 📈 Melhorias Futuras

- [ ] App mobile para clientes
- [ ] Integração com WhatsApp
- [ ] Sistema de avaliações
- [ ] Agendamento online
- [ ] Pagamento integrado
- [ ] Dashboard analítico
- [ ] Notificações push
- [ ] Integração com Google Calendar

## 🤝 Contribuição

Este é um projeto de portfólio, mas sugestões são bem-vindas!

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👨‍💻 Desenvolvedor

**Seu Nome**
- LinkedIn: [seu-linkedin](https://linkedin.com/in/seu-perfil)
- GitHub: [seu-github](https://github.com/notdougz)
- Email: doug.dev@hotmail.com

---

⭐ **Se este projeto foi útil, deixe uma estrela!** ⭐
