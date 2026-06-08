from django.db import models


class Manutencao(models.Model):
    STATUS_CHOICES = [
        ('ABERTA', 'Aberta'),
        ('EM_ANDAMENTO', 'Em andamento'),
        ('CONCLUIDA', 'Concluida'),
        ('CANCELADA', 'Cancelada'),
    ]

    veiculo = models.ForeignKey(
        'veiculo.Veiculo',
        on_delete=models.PROTECT,
        related_name='manutencoes'
    )
    tipo_manutencao = models.CharField(max_length=100)
    descricao = models.TextField()
    data_entrada = models.DateField()
    data_saida = models.DateField(null=True, blank=True)
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='ABERTA'
    )

    def __str__(self):
        return f'{self.tipo_manutencao} - {self.veiculo}'


class Peca(models.Model):
    tipo_peca = models.CharField(max_length=100)
    fabricante = models.CharField(max_length=100)
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'{self.tipo_peca} - {self.fabricante}'


class PecaManutencao(models.Model):
    manutencao = models.ForeignKey(
        Manutencao,
        on_delete=models.CASCADE,
        related_name='pecas_manutencao'
    )
    peca = models.ForeignKey(
        Peca,
        on_delete=models.PROTECT,
        related_name='usos_manutencao'
    )
    quantidade = models.IntegerField()
    preco_unitario = models.DecimalField(max_digits=10, decimal_places=2)
    sub_total = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        self.sub_total = self.quantidade * self.preco_unitario
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.quantidade}x {self.peca} - {self.manutencao}'
