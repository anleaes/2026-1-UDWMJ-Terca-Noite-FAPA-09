from rest_framework import serializers
from .models import Cliente, Funcionario


class ClienteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cliente
        fields = [
            'id', 'nome', 'email', 'senha', 'cpf', 'telefone', 'status',
            'cnh', 'categoria_cnh', 'validade_cnh', 'data_cadastro',
        ]
        extra_kwargs = {'senha': {'write_only': False}}


class FuncionarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = Funcionario
        fields = [
            'id', 'nome', 'email', 'senha', 'cpf', 'telefone', 'status',
            'nivel_acesso', 'cargo', 'ativo',
        ]
        extra_kwargs = {'senha': {'write_only': False}}