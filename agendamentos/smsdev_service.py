import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

class SMSDevService:
    """Serviço para envio de SMS usando SMSDev (Brasileira)"""
    
    def __init__(self):
        self.enabled = getattr(settings, 'SMS_ENABLED', False)
        self.usuario = getattr(settings, 'SMSDEV_USUARIO', None)
        self.token = getattr(settings, 'SMSDEV_TOKEN', None)
        self.api_url = 'https://api.smsdev.com.br/v1/send'
        
        if not all([self.usuario, self.token]):
            logger.warning("SMSDev: Credenciais não configuradas")
    
    def enviar_sms(self, telefone, mensagem):
        """
        Envia SMS para um número de telefone
        
        Args:
            telefone (str): Número do telefone (formato: 11999999999)
            mensagem (str): Texto da mensagem
            
        Returns:
            dict: {'sucesso': bool, 'erro': str, 'id': str}
        """
        if not self.enabled:
            logger.info(f"SMS desabilitado - Mensagem que seria enviada: {mensagem}")
            return {'sucesso': False, 'erro': 'SMS desabilitado', 'id': None}
        
        if not all([self.usuario, self.token]):
            logger.error("SMSDev: Credenciais não configuradas")
            return {'sucesso': False, 'erro': 'Credenciais SMSDev não configuradas', 'id': None}
        
        # Validar telefone
        telefone_limpo = self._limpar_telefone(telefone)
        if not telefone_limpo:
            return {'sucesso': False, 'erro': 'Número de telefone inválido', 'id': None}
        
        try:
            # Dados para envio
            dados = {
                'key': self.token,
                'type': 9,  # Tipo SMS
                'number': telefone_limpo,
                'msg': mensagem
            }
            
            # Enviar SMS
            response = requests.post(self.api_url, data=dados, timeout=30)
            
            if response.status_code == 200:
                resultado = response.json()
                
                if resultado.get('situacao') == 'OK':
                    logger.info(f"SMSDev: SMS enviado com sucesso - ID: {resultado.get('id')}")
                    return {
                        'sucesso': True,
                        'erro': None,
                        'id': resultado.get('id'),
                        'situacao': resultado.get('situacao')
                    }
                else:
                    logger.error(f"SMSDev: Erro no envio - {resultado}")
                    return {
                        'sucesso': False,
                        'erro': resultado.get('descricao', 'Erro desconhecido'),
                        'id': None
                    }
            else:
                logger.error(f"SMSDev: Erro HTTP {response.status_code}")
                return {'sucesso': False, 'erro': f'Erro HTTP {response.status_code}', 'id': None}
                
        except requests.exceptions.RequestException as e:
            logger.error(f"SMSDev: Erro de conexão - {e}")
            return {'sucesso': False, 'erro': f'Erro de conexão: {str(e)}', 'id': None}
        except Exception as e:
            logger.error(f"SMSDev: Erro inesperado - {e}")
            return {'sucesso': False, 'erro': str(e), 'id': None}
    
    def _limpar_telefone(self, telefone):
        """
        Limpa e formata o número de telefone para SMSDev
        
        Args:
            telefone (str): Número de telefone
            
        Returns:
            str: Número formatado ou None se inválido
        """
        if not telefone:
            return None
        
        # Remover caracteres não numéricos
        telefone_limpo = ''.join(filter(str.isdigit, telefone))
        
        # Se começar com 55 (Brasil), remover
        if telefone_limpo.startswith('55'):
            telefone_limpo = telefone_limpo[2:]
        
        # Se começar com 0, remover
        if telefone_limpo.startswith('0'):
            telefone_limpo = telefone_limpo[1:]
        
        # Verificar se tem 10 ou 11 dígitos (DDD + número)
        if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
            return None
        
        return telefone_limpo
    
    def enviar_barbeiro_a_caminho(self, agendamento, previsao_minutos=None):
        """
        Envia SMS específico para "barbeiro a caminho"
        
        Args:
            agendamento: Objeto Agendamento
            previsao_minutos: Previsão de chegada em minutos (opcional)
            
        Returns:
            dict: Resultado do envio
        """
        if not agendamento.cliente or not agendamento.cliente.telefone:
            return {'sucesso': False, 'erro': 'Cliente sem telefone', 'id': None}
        
        # Usar previsão do agendamento se não fornecida
        if previsao_minutos is None:
            previsao_minutos = agendamento.previsao_chegada
        
        # Montar mensagem personalizada
        mensagem = self._montar_mensagem_barbeiro_a_caminho(agendamento, previsao_minutos)
        
        return self.enviar_sms(agendamento.cliente.telefone, mensagem)
    
    def _montar_mensagem_barbeiro_a_caminho(self, agendamento, previsao_minutos):
        """
        Monta a mensagem de "barbeiro a caminho"
        
        Args:
            agendamento: Objeto Agendamento
            previsao_minutos: Previsão de chegada em minutos
            
        Returns:
            str: Mensagem formatada
        """
        nome_cliente = agendamento.cliente.nome.split()[0]  # Primeiro nome
        
        # Montar mensagem com previsão de chegada
        if previsao_minutos:
            mensagem = f"Olá, {nome_cliente}! Seu barbeiro está a caminho, a previsão de chegada é de {previsao_minutos} minutos. ⭐✂"
        else:
            mensagem = f"Olá, {nome_cliente}! Seu barbeiro está a caminho. ⭐✂"
        
        return mensagem

# Instância global do serviço
smsdev_service = SMSDevService()
