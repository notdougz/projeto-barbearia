from django.db import models
from django.contrib.auth.models import User

# Modelo para estender o User padrão do Django com informações extras
class PerfilCliente(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    telefone = models.CharField(max_length=15)
    
    # Campos de endereço
    cep = models.CharField(max_length=9)
    rua = models.CharField(max_length=200)
    numero = models.CharField(max_length=10)
    complemento = models.CharField(max_length=100, blank=True, null=True)
    bairro = models.CharField(max_length=100)
    cidade = models.CharField(max_length=100)
    estado = models.CharField(max_length=2)
    
    def __str__(self):
        return f"{self.user.first_name} - {self.telefone}"

# Modelo para os serviços oferecidos
class Servico(models.Model):
    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    duracao = models.IntegerField(help_text="Duração em minutos")
    preco = models.DecimalField(max_digits=6, decimal_places=2)
    ativo = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.nome} - R$ {self.preco}"
    
    class Meta:
        verbose_name_plural = "Serviços"

# Modelo para os agendamentos
class Agendamento(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('confirmado', 'Confirmado'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    ]
    
    cliente = models.ForeignKey(User, on_delete=models.CASCADE, related_name='agendamentos')
    servico = models.ForeignKey(Servico, on_delete=models.PROTECT)
    data = models.DateField()
    hora = models.TimeField()
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='pendente')
    observacoes = models.TextField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.cliente.first_name} - {self.servico.nome} - {self.data} às {self.hora}"
    
    class Meta:
        ordering = ['-data', '-hora']
