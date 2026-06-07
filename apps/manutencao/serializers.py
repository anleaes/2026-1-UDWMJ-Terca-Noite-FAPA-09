from rest_framework import serializers

from .models import Manutencao, Peca, PecaManutencao


class ManutencaoSerializer(serializers.ModelSerializer):
    veiculo_descricao = serializers.StringRelatedField(source='veiculo', read_only=True)

    class Meta:
        model = Manutencao
        fields = [
            'id',
            'veiculo',
            'veiculo_descricao',
            'tipo_manutencao',
            'descricao',
            'data_entrada',
            'data_saida',
            'custo',
            'status',
        ]


class PecaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Peca
        fields = [
            'id',
            'tipo_peca',
            'fabricante',
            'preco_unitario',
        ]

    def validate_preco_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError('O preco unitario nao pode ser negativo.')
        return value


class PecaManutencaoSerializer(serializers.ModelSerializer):
    manutencao_descricao = serializers.StringRelatedField(source='manutencao', read_only=True)
    peca_descricao = serializers.StringRelatedField(source='peca', read_only=True)

    class Meta:
        model = PecaManutencao
        fields = [
            'id',
            'manutencao',
            'manutencao_descricao',
            'peca',
            'peca_descricao',
            'quantidade',
            'preco_unitario',
            'sub_total',
        ]
        read_only_fields = [
            'sub_total',
        ]

    def validate(self, attrs):
        manutencao = attrs.get('manutencao', getattr(self.instance, 'manutencao', None))
        if manutencao and manutencao.status in ('CONCLUIDA', 'CANCELADA'):
            raise serializers.ValidationError({
                'manutencao': 'Nao e possivel adicionar pecas em manutencoes concluidas ou canceladas.'
            })
        return attrs

    def validate_quantidade(self, value):
        if value <= 0:
            raise serializers.ValidationError('A quantidade deve ser maior que zero.')
        return value

    def validate_preco_unitario(self, value):
        if value < 0:
            raise serializers.ValidationError('O preco unitario nao pode ser negativo.')
        return value

    def create(self, validated_data):
        validated_data['sub_total'] = (
            validated_data['quantidade'] * validated_data['preco_unitario']
        )
        return super().create(validated_data)

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        instance.sub_total = instance.quantidade * instance.preco_unitario
        instance.save(update_fields=['sub_total'])
        return instance
