from rest_framework import serializers
from .models import Alocacao, HistoricoAlocacao


class AlocacaoSerializer(serializers.ModelSerializer):
    solicitacao_descricao = serializers.StringRelatedField(
        source='solicitacao',
        read_only=True
    )

    valor_diaria = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    quantidade_dias = serializers.IntegerField(read_only=True)

    valor_total_previsto = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        read_only=True
    )

    class Meta:
        model = Alocacao
        fields = [
            'id',
            'solicitacao',
            'solicitacao_descricao',
            'data_inicio',
            'data_fim_prevista',
            'data_fim_real',
            'km_inicial',
            'km_final',
            'status',
            'observacao',
            'valor_diaria',
            'quantidade_dias',
            'valor_total_previsto',
        ]


class HistoricoAlocacaoSerializer(serializers.ModelSerializer):
    alocacao_descricao = serializers.StringRelatedField(
        source='alocacao',
        read_only=True
    )

    class Meta:
        model = HistoricoAlocacao
        fields = [
            'id',
            'alocacao',
            'alocacao_descricao',
            'data_evento',
            'tipo_evento',
            'descricao',
        ]