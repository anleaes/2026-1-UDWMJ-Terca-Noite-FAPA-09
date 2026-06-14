from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.dateparse import parse_date
from django.views import View
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .models import Alocacao, HistoricoAlocacao
from .serializers import AlocacaoSerializer, HistoricoAlocacaoSerializer
from .services import cancelar_alocacao, criar_alocacao, finalizar_alocacao

from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from .forms import AlocacaoCancelarForm, AlocacaoFinalizarForm, AlocacaoForm


def _raise_api_validation_error(error):
    messages = error.messages if hasattr(error, 'messages') else [str(error)]
    raise ValidationError({'detail': messages})


class AlocacaoViewSet(viewsets.ModelViewSet):
    queryset = Alocacao.objects.select_related(
        'solicitacao',
        'solicitacao__veiculo',
        'solicitacao__veiculo__grupo'
    ).all()
    serializer_class = AlocacaoSerializer

    def partial_update(self, request, *args, **kwargs):
        alocacao = self.get_object()
        novo_status = request.data.get('status')

        if alocacao.status == 'ativa' and novo_status in ['finalizada', 'cancelada']:
            try:
                if novo_status == 'finalizada':
                    data_recebida = request.data.get('data_fim_real')

                    if data_recebida:
                        data_fim_real = parse_date(data_recebida)

                        if data_fim_real is None:
                            raise DjangoValidationError(
                                'Informe uma data valida no formato YYYY-MM-DD.'
                            )
                    else:
                        data_fim_real = alocacao.data_fim_prevista

                    km_recebido = request.data.get('km_final')

                    if km_recebido not in [None, '']:
                        km_final = float(km_recebido)
                    else:
                        km_atual_veiculo = alocacao.solicitacao.veiculo.quilometragem
                        km_final = max(
                            float(alocacao.km_inicial),
                            float(km_atual_veiculo or alocacao.km_inicial)
                        )

                    alocacao = finalizar_alocacao(
                        alocacao=alocacao,
                        data_fim_real=data_fim_real,
                        km_final=km_final,
                        observacao=request.data.get('observacao'),
                        responsavel_alteracao=request.data.get('responsavel_alteracao', 'API')
                    )

                elif novo_status == 'cancelada':
                    alocacao = cancelar_alocacao(
                        alocacao=alocacao,
                        observacao=request.data.get('observacao'),
                        responsavel_alteracao=request.data.get('responsavel_alteracao', 'API')
                    )

            except (DjangoValidationError, ValueError) as error:
                _raise_api_validation_error(error)

            serializer = self.get_serializer(alocacao)
            return Response(serializer.data, status=status.HTTP_200_OK)

        return super().partial_update(request, *args, **kwargs)

    def perform_update(self, serializer):
        if self.get_object().status == 'ativa':
            raise ValidationError({
                'detail': 'Alocacoes ativas devem ser finalizadas ou canceladas pelo fluxo oficial.'
            })
        serializer.save()

    def perform_create(self, serializer):
        dados = serializer.validated_data
        try:
            serializer.instance = criar_alocacao(
                solicitacao=dados['solicitacao'],
                data_inicio=dados['data_inicio'],
                data_fim_prevista=dados['data_fim_prevista'],
                km_inicial=dados['km_inicial'],
                observacao=dados.get('observacao'),
                responsavel_alteracao='API'
            )
        except DjangoValidationError as error:
            _raise_api_validation_error(error)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        alocacao = self.get_object()
        data_fim_real = parse_date(request.data.get('data_fim_real', ''))
        km_final = request.data.get('km_final')

        if data_fim_real is None:
            raise ValidationError({'data_fim_real': 'Informe uma data valida no formato YYYY-MM-DD.'})

        try:
            km_final = float(km_final)
        except (TypeError, ValueError):
            raise ValidationError({'km_final': 'Informe uma quilometragem final valida.'})

        try:
            alocacao = finalizar_alocacao(
                alocacao=alocacao,
                data_fim_real=data_fim_real,
                km_final=km_final,
                observacao=request.data.get('observacao'),
                responsavel_alteracao=request.data.get('responsavel_alteracao', 'API')
            )
        except DjangoValidationError as error:
            _raise_api_validation_error(error)

        serializer = self.get_serializer(alocacao)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        if instance.status == 'ativa':
            raise ValidationError({
                'detail': 'Alocacoes ativas devem ser finalizadas ou canceladas antes de excluir.'
            })
        instance.delete()

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        try:
            alocacao = cancelar_alocacao(
                alocacao=self.get_object(),
                observacao=request.data.get('observacao'),
                responsavel_alteracao=request.data.get('responsavel_alteracao', 'API')
            )
        except DjangoValidationError as error:
            _raise_api_validation_error(error)

        serializer = self.get_serializer(alocacao)
        return Response(serializer.data, status=status.HTTP_200_OK)


class HistoricoAlocacaoViewSet(viewsets.ModelViewSet):
    queryset = HistoricoAlocacao.objects.select_related('alocacao').all()
    serializer_class = HistoricoAlocacaoSerializer


class AlocacaoListView(ListView):
    model = Alocacao
    template_name = 'alocacao/lista.html'
    context_object_name = 'alocacoes'
    queryset = Alocacao.objects.select_related(
        'solicitacao',
        'solicitacao__cliente',
        'solicitacao__veiculo',
        'solicitacao__local'
    ).all().order_by('-data_inicio')

class AlocacaoDetailView(DetailView):
    model = Alocacao
    template_name = 'alocacao/detalhe.html'
    context_object_name = 'alocacao'


class AlocacaoCreateView(CreateView):
    model = Alocacao
    form_class = AlocacaoForm
    template_name = 'alocacao/form.html'
    success_url = reverse_lazy('alocacao_web:lista')

    def form_valid(self, form):
        try:
            self.object = criar_alocacao(
                solicitacao=form.cleaned_data['solicitacao'],
                data_inicio=form.cleaned_data['data_inicio'],
                data_fim_prevista=form.cleaned_data['data_fim_prevista'],
                km_inicial=form.cleaned_data['km_inicial'],
                observacao=form.cleaned_data.get('observacao'),
                responsavel_alteracao='Tela web'
            )
        except DjangoValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())


class AlocacaoUpdateView(UpdateView):
    model = Alocacao
    form_class = AlocacaoForm
    template_name = 'alocacao/form.html'
    success_url = reverse_lazy('alocacao_web:lista')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status == 'ativa':
            return redirect('alocacao_web:detalhe', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)


class AlocacaoDeleteView(DeleteView):
    model = Alocacao
    template_name = 'alocacao/confirmar_delete.html'
    context_object_name = 'alocacao'
    success_url = reverse_lazy('alocacao_web:lista')

    def form_valid(self, form):
        if self.object.status == 'ativa':
            context = self.get_context_data(object=self.object)
            context['erro'] = 'Alocacoes ativas devem ser finalizadas ou canceladas antes de excluir.'
            return self.render_to_response(context)
        return super().form_valid(form)


class AlocacaoFinalizarView(View):
    template_name = 'alocacao/finalizar.html'

    def get(self, request, pk):
        alocacao = get_object_or_404(Alocacao, pk=pk)
        form = AlocacaoFinalizarForm()
        return render(request, self.template_name, {
            'alocacao': alocacao,
            'form': form,
        })

    def post(self, request, pk):
        alocacao = get_object_or_404(Alocacao, pk=pk)
        form = AlocacaoFinalizarForm(request.POST)

        if form.is_valid():
            try:
                finalizar_alocacao(
                    alocacao=alocacao,
                    data_fim_real=form.cleaned_data['data_fim_real'],
                    km_final=form.cleaned_data['km_final'],
                    observacao=form.cleaned_data.get('observacao'),
                    responsavel_alteracao='Tela web'
                )
                return redirect('alocacao_web:detalhe', pk=alocacao.pk)
            except DjangoValidationError as error:
                form.add_error(None, error)

        return render(request, self.template_name, {
            'alocacao': alocacao,
            'form': form,
        })


class AlocacaoCancelarView(View):
    template_name = 'alocacao/cancelar.html'

    def get(self, request, pk):
        alocacao = get_object_or_404(Alocacao, pk=pk)
        form = AlocacaoCancelarForm()
        return render(request, self.template_name, {
            'alocacao': alocacao,
            'form': form,
        })

    def post(self, request, pk):
        alocacao = get_object_or_404(Alocacao, pk=pk)
        form = AlocacaoCancelarForm(request.POST)

        if form.is_valid():
            try:
                cancelar_alocacao(
                    alocacao=alocacao,
                    observacao=form.cleaned_data.get('observacao'),
                    responsavel_alteracao='Tela web'
                )
                return redirect('alocacao_web:detalhe', pk=alocacao.pk)
            except DjangoValidationError as error:
                form.add_error(None, error)

        return render(request, self.template_name, {
            'alocacao': alocacao,
            'form': form,
        })


class HistoricoAlocacaoListView(ListView):
    model = HistoricoAlocacao
    template_name = 'alocacao/historico.html'
    context_object_name = 'historicos'

    def get_queryset(self):
        historicos = (
            HistoricoAlocacao.objects
            .select_related(
                'alocacao',
                'alocacao__solicitacao',
                'alocacao__solicitacao__funcionario'
            )
            .order_by('alocacao_id', '-data_registro', '-id')
        )

        ultimos_ids = {}

        for historico in historicos:
            if historico.alocacao_id not in ultimos_ids:
                ultimos_ids[historico.alocacao_id] = historico.id

        return (
            HistoricoAlocacao.objects
            .filter(id__in=ultimos_ids.values())
            .select_related(
                'alocacao',
                'alocacao__solicitacao',
                'alocacao__solicitacao__funcionario'
            )
            .order_by('-data_registro', '-id')
        )
