from django.db import models

from locais.models import Local
from users.models import Cliente, Funcionario
from veiculo.models import Veiculo


class Solicitacao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovada', 'Aprovada'),
        ('recusada', 'Recusada'),
        ('cancelada', 'Cancelada'),
        ('finalizada', 'Finalizada'),
    ]

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='solicitacoes'
    )
    veiculo = models.ForeignKey(
        Veiculo,
        on_delete=models.PROTECT,
        related_name='solicitacoes'
    )
    local = models.ForeignKey(
        Local,
        on_delete=models.PROTECT,
        related_name='solicitacoes'
    )
    funcionario = models.ForeignKey(
        Funcionario,
        on_delete=models.SET_NULL,
        related_name='solicitacoes_analisadas',
        null=True,
        blank=True
    )
    data_solicitacao = models.DateField(auto_now_add=True)
    data_inicio_desejada = models.DateField()
    data_fim_desejada = models.DateField()
    motivo = models.CharField(max_length=255)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pendente'
    )
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Solicitacao #{self.id} - {self.cliente.nome}'
    
    @property
    def quantidade_dias(self):
        if not self.data_inicio_desejada or not self.data_fim_desejada:
            return 0

        dias = (self.data_fim_desejada - self.data_inicio_desejada).days

        return max(dias, 1)

    @property
    def valor_diaria(self):
        if not self.veiculo or not self.veiculo.grupo:
            return 0

        return self.veiculo.grupo.valor_base_diaria

    @property
    def valor_total_estimado(self):
        return self.valor_diaria * self.quantidade_dias
