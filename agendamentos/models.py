from django.db import models

class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15, unique=True, blank=True, null=True)
    endereco = models.TextField(blank=True, null=True, help_text="Endereço completo do cliente")
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.nome

class Servico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField(blank=True, null=True)
    duracao = models.IntegerField(help_text="Duração em minutos")
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return self.nome
    
class Agendamento(models.Model):
    STATUS_CHOICES = [
        ('confirmado', 'Pendente'),
        ('a_caminho', 'À caminho'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    PAGAMENTO_CHOICES = [
        ('pendente', 'Pendente'),
        ('pago', 'Pago'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.SET_NULL, null=True, blank=True, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT)
    data = models.DateField()
    hora = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='confirmado')
    status_pagamento = models.CharField(max_length=10, choices=PAGAMENTO_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True, null=True)
    previsao_chegada = models.IntegerField(blank=True, null=True, help_text="Previsão de chegada em minutos")
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.cliente.nome if self.cliente else 'Cliente avulso'} - {self.servico.nome} em {self.data}"
    
    class Meta:
        ordering = ['-data', '-hora']