"""
Serviços para notificações de agendamentos
"""
# import requests  # Descomente quando configurar APIs externas
from django.conf import settings
from django.contrib import messages

class NotificationService:
    """Serviço para envio de notificações por SMS"""
    
    @staticmethod
    def send_sms_message(phone_number, message):
        """
        Envia SMS usando API externa
        Para usar, você precisa configurar uma API de SMS (como Twilio, etc.)
        """
        try:
            # Exemplo usando uma API fictícia - substitua pela sua API real
            # url = "https://api.sms.com/send"
            # data = {
            #     "phone": phone_number,
            #     "message": message
            # }
            # response = requests.post(url, data=data)
            # return response.status_code == 200
            
            # Por enquanto, apenas simula o envio
            print(f"💬 SMS para {phone_number}: {message}")
            return True
            
        except Exception as e:
            print(f"Erro ao enviar SMS: {e}")
            return False
    
    @classmethod
    def notify_client_on_the_way(cls, agendamento, previsao_minutos):
        """
        Notifica o cliente que o barbeiro está a caminho via SMS
        """
        if not agendamento.cliente or not agendamento.cliente.telefone:
            return False, "Cliente sem telefone cadastrado"
        
        # Limpa o número do telefone
        phone = agendamento.cliente.telefone.replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
        
        # Monta a mensagem
        message = f"Olá {agendamento.cliente.nome}! 😊\n\nSeu barbeiro está a caminho e a previsão é de {previsao_minutos} minutos.\n\nObrigado pela preferência! 💇‍♂️"
        
        # Envia notificação por SMS
        sms_sent = cls.send_sms_message(phone, message)
        
        return sms_sent, "Notificação SMS enviada com sucesso!" if sms_sent else "Erro ao enviar SMS"

def format_phone_number(phone):
    """Formata o número de telefone para APIs"""
    if not phone:
        return None
    
    # Remove caracteres especiais
    clean_phone = phone.replace('+', '').replace('-', '').replace('(', '').replace(')', '').replace(' ', '')
    
    # Adiciona código do país se necessário (Brasil)
    if clean_phone.startswith('55'):
        return clean_phone
    elif clean_phone.startswith('11') or clean_phone.startswith('21') or clean_phone.startswith('31'):
        return f"55{clean_phone}"
    else:
        return f"55{clean_phone}"
