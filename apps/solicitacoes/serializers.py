from rest_framework import serializers
from .models import Solicitacao


class SolicitacaoSerializer(serializers.ModelSerializer):
    valor_diaria = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )
    quantidade_dias = serializers.IntegerField(read_only=True)
    valor_total_estimado = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Solicitacao
        fields = '__all__'
