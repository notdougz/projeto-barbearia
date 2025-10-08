from django.db import models
from django.contrib.auth.models import User

# NOVO MODELO PARA CLIENTES
class Cliente(models.Model):
    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=15, unique=True) # Telefone é único
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
        ('confirmado', 'Confirmado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]

    # AGORA O AGENDAMENTO SE LIGA AO NOVO MODELO CLIENTE
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT)
    data = models.DateField()
    hora = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='confirmado')
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.cliente.nome} - {self.servico.nome} em {self.data}"

    class Meta:
        ordering = ['-data', '-hora']