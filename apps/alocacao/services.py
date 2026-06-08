from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Alocacao, HistoricoAlocacao


def registrar_historico_alocacao(
    alocacao,
    status_anterior,
    status_novo,
    responsavel_alteracao='Sistema',
    observacao=None
):
    return HistoricoAlocacao.objects.create(
        alocacao=alocacao,
        status_anterior=status_anterior,
        status_novo=status_novo,
        responsavel_alteracao=responsavel_alteracao,
        observacao=observacao
    )


@transaction.atomic
def criar_alocacao(
    solicitacao,
    data_inicio,
    data_fim_prevista,
    km_inicial,
    observacao=None,
    responsavel_alteracao='Sistema'
):
    if solicitacao.status != 'aprovada':
        raise ValidationError('Apenas solicitacoes aprovadas podem gerar alocacao.')
    
    solicitacao.refresh_from_db()
    try:
        _ = solicitacao.alocacao
        raise ValidationError('A solicitacao ja possui uma alocacao associada.')
    except Alocacao.DoesNotExist:
        pass

    if data_fim_prevista < data_inicio:
        raise ValidationError('A data fim prevista nao pode ser anterior a data de inicio.')

    if km_inicial < 0:
        raise ValidationError('A quilometragem inicial nao pode ser negativa.')

    veiculo = solicitacao.veiculo
    if veiculo.status != 'disponivel':
        raise ValidationError('O veiculo precisa estar disponivel para ser alocado.')

    alocacao = Alocacao.objects.create(
        solicitacao=solicitacao,
        data_inicio=data_inicio,
        data_fim_prevista=data_fim_prevista,
        km_inicial=km_inicial,
        status='ativa',
        observacao=observacao
    )

    veiculo.status = 'alocado'
    veiculo.save(update_fields=['status'])

    registrar_historico_alocacao(
        alocacao=alocacao,
        status_anterior='nova',
        status_novo='ativa',
        responsavel_alteracao=responsavel_alteracao,
        observacao=observacao
    )

    return alocacao


@transaction.atomic
def finalizar_alocacao(
    alocacao,
    data_fim_real,
    km_final,
    observacao=None,
    responsavel_alteracao='Sistema'
):
    if alocacao.status != 'ativa':
        raise ValidationError('Apenas alocacoes ativas podem ser finalizadas.')

    if data_fim_real < alocacao.data_inicio:
        raise ValidationError('A data final real nao pode ser anterior a data de inicio.')

    if km_final < alocacao.km_inicial:
        raise ValidationError('A quilometragem final nao pode ser menor que a inicial.')

    status_anterior = alocacao.status
    alocacao.data_fim_real = data_fim_real
    alocacao.km_final = km_final
    alocacao.status = 'finalizada'
    alocacao.observacao = observacao or alocacao.observacao
    alocacao.save(update_fields=[
        'data_fim_real',
        'km_final',
        'status',
        'observacao',
    ])

    veiculo = alocacao.solicitacao.veiculo
    veiculo.status = 'disponivel'
    veiculo.quilometragem = km_final
    veiculo.save(update_fields=['status', 'quilometragem'])

    solicitacao = alocacao.solicitacao
    solicitacao.status = 'finalizada'
    solicitacao.save(update_fields=['status'])

    registrar_historico_alocacao(
        alocacao=alocacao,
        status_anterior=status_anterior,
        status_novo='finalizada',
        responsavel_alteracao=responsavel_alteracao,
        observacao=observacao
    )

    return alocacao


@transaction.atomic
def cancelar_alocacao(
    alocacao,
    observacao=None,
    responsavel_alteracao='Sistema'
):
    if alocacao.status != 'ativa':
        raise ValidationError('Apenas alocacoes ativas podem ser canceladas.')

    status_anterior = alocacao.status
    alocacao.status = 'cancelada'
    alocacao.observacao = observacao or alocacao.observacao
    alocacao.save(update_fields=['status', 'observacao'])

    veiculo = alocacao.solicitacao.veiculo
    veiculo.status = 'disponivel'
    veiculo.save(update_fields=['status'])

    registrar_historico_alocacao(
        alocacao=alocacao,
        status_anterior=status_anterior,
        status_novo='cancelada',
        responsavel_alteracao=responsavel_alteracao,
        observacao=observacao
    )

    return alocacao
