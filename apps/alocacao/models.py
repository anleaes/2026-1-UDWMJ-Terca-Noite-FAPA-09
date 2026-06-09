from django.db import models


class Alocacao(models.Model):
    STATUS_CHOICES = [
        ('ativa', 'Ativa'),
        ('finalizada', 'Finalizada'),
        ('cancelada', 'Cancelada'),
    ]

    solicitacao = models.OneToOneField(
        'solicitacoes.Solicitacao',
        on_delete=models.PROTECT,
        related_name='alocacao'
    )
    data_inicio = models.DateField()
    data_fim_prevista = models.DateField()
    data_fim_real = models.DateField(null=True, blank=True)
    km_inicial = models.FloatField()
    km_final = models.FloatField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ativa'
    )
    observacao = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'Alocacao #{self.id} - {self.solicitacao}'

    @property
    def quantidade_dias(self):
        if not self.data_inicio or not self.data_fim_prevista:
            return 0

        dias = (self.data_fim_prevista - self.data_inicio).days

        return max(dias, 1)

    @property
    def valor_diaria(self):
        if (
            not self.solicitacao
            or not self.solicitacao.veiculo
            or not self.solicitacao.veiculo.grupo
        ):
            return 0

        return self.solicitacao.veiculo.grupo.valor_base_diaria

    @property
    def valor_total_previsto(self):
        return self.valor_diaria * self.quantidade_dias


class HistoricoAlocacao(models.Model):
    alocacao = models.ForeignKey(
        Alocacao,
        on_delete=models.CASCADE,
        related_name='historicos'
    )
    data_registro = models.DateField(auto_now_add=True)
    status_anterior = models.CharField(max_length=20)
    status_novo = models.CharField(max_length=20)
    observacao = models.TextField(blank=True, null=True)
    responsavel_alteracao = models.CharField(max_length=100)

    def __str__(self):
        return f'Historico #{self.id} - {self.alocacao}'