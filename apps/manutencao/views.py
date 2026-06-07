from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse, reverse_lazy
from django.utils.dateparse import parse_date
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, UpdateView
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from .forms import ManutencaoFinalizarForm, ManutencaoForm, PecaForm, PecaManutencaoForm
from .models import Manutencao, Peca, PecaManutencao
from .serializers import ManutencaoSerializer, PecaManutencaoSerializer, PecaSerializer
from .services import abrir_manutencao, cancelar_manutencao, finalizar_manutencao


def _raise_api_validation_error(error):
    messages = error.messages if hasattr(error, 'messages') else [str(error)]
    raise ValidationError({'detail': messages})


class ManutencaoViewSet(viewsets.ModelViewSet):
    queryset = Manutencao.objects.select_related('veiculo').all()
    serializer_class = ManutencaoSerializer

    def perform_update(self, serializer):
        if serializer.instance.status in ('ABERTA', 'EM_ANDAMENTO'):
            raise ValidationError({
                'detail': 'Manutencoes abertas devem ser finalizadas ou canceladas pelo fluxo oficial.'
            })
        serializer.save()

    def perform_create(self, serializer):
        dados = serializer.validated_data
        try:
            serializer.instance = abrir_manutencao(
                veiculo=dados['veiculo'],
                tipo_manutencao=dados['tipo_manutencao'],
                descricao=dados['descricao'],
                data_entrada=dados['data_entrada'],
                custo=dados['custo']
            )
        except DjangoValidationError as error:
            _raise_api_validation_error(error)

    @action(detail=True, methods=['post'])
    def finalizar(self, request, pk=None):
        manutencao = self.get_object()
        data_saida = parse_date(request.data.get('data_saida', ''))
        custo = request.data.get('custo')

        if data_saida is None:
            raise ValidationError({'data_saida': 'Informe uma data valida no formato YYYY-MM-DD.'})

        if custo in (None, ''):
            custo = None
        else:
            try:
                custo = Decimal(str(custo))
            except (InvalidOperation, TypeError, ValueError):
                raise ValidationError({'custo': 'Informe um custo valido.'})

        try:
            manutencao = finalizar_manutencao(
                manutencao=manutencao,
                data_saida=data_saida,
                custo=custo
            )
        except DjangoValidationError as error:
            _raise_api_validation_error(error)

        serializer = self.get_serializer(manutencao)
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancelar(self, request, pk=None):
        try:
            manutencao = cancelar_manutencao(self.get_object())
        except DjangoValidationError as error:
            _raise_api_validation_error(error)

        serializer = self.get_serializer(manutencao)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def perform_destroy(self, instance):
        if instance.status in ('ABERTA', 'EM_ANDAMENTO'):
            raise ValidationError({
                'detail': 'Manutencoes abertas devem ser finalizadas ou canceladas antes de excluir.'
            })
        instance.delete()


class PecaViewSet(viewsets.ModelViewSet):
    queryset = Peca.objects.all().order_by('tipo_peca', 'fabricante')
    serializer_class = PecaSerializer


class PecaManutencaoViewSet(viewsets.ModelViewSet):
    queryset = PecaManutencao.objects.select_related(
        'manutencao',
        'peca'
    ).all()
    serializer_class = PecaManutencaoSerializer

    def perform_destroy(self, instance):
        if instance.manutencao.status in ('CONCLUIDA', 'CANCELADA'):
            raise ValidationError({
                'detail': 'Nao e possivel remover pecas de manutencoes concluidas ou canceladas.'
            })
        instance.delete()


class ManutencaoListView(ListView):
    model = Manutencao
    template_name = 'manutencao/lista.html'
    context_object_name = 'manutencoes'
    queryset = Manutencao.objects.select_related('veiculo').all().order_by('-data_entrada')


class ManutencaoDetailView(DetailView):
    model = Manutencao
    template_name = 'manutencao/detalhe.html'
    context_object_name = 'manutencao'

    def get_queryset(self):
        return Manutencao.objects.select_related('veiculo').prefetch_related(
            'pecas_manutencao__peca'
        )


class ManutencaoCreateView(CreateView):
    model = Manutencao
    form_class = ManutencaoForm
    template_name = 'manutencao/form.html'
    success_url = reverse_lazy('manutencao_web:lista')

    def form_valid(self, form):
        try:
            self.object = abrir_manutencao(
                veiculo=form.cleaned_data['veiculo'],
                tipo_manutencao=form.cleaned_data['tipo_manutencao'],
                descricao=form.cleaned_data['descricao'],
                data_entrada=form.cleaned_data['data_entrada'],
                custo=form.cleaned_data['custo']
            )
        except DjangoValidationError as error:
            form.add_error(None, error)
            return self.form_invalid(form)

        return HttpResponseRedirect(self.get_success_url())


class ManutencaoUpdateView(UpdateView):
    model = Manutencao
    form_class = ManutencaoForm
    template_name = 'manutencao/form.html'
    success_url = reverse_lazy('manutencao_web:lista')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.status in ('ABERTA', 'EM_ANDAMENTO'):
            return redirect('manutencao_web:detalhe', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)


class ManutencaoDeleteView(DeleteView):
    model = Manutencao
    template_name = 'manutencao/confirmar_delete.html'
    context_object_name = 'manutencao'
    success_url = reverse_lazy('manutencao_web:lista')

    def form_valid(self, form):
        if self.object.status in ('ABERTA', 'EM_ANDAMENTO'):
            context = self.get_context_data(object=self.object)
            context['erro'] = 'Manutencoes abertas devem ser finalizadas ou canceladas antes de excluir.'
            return self.render_to_response(context)
        return super().form_valid(form)


class ManutencaoFinalizarView(View):
    template_name = 'manutencao/finalizar.html'

    def get(self, request, pk):
        manutencao = get_object_or_404(Manutencao, pk=pk)
        form = ManutencaoFinalizarForm(initial={'custo': manutencao.custo})
        return render(request, self.template_name, {
            'manutencao': manutencao,
            'form': form,
        })

    def post(self, request, pk):
        manutencao = get_object_or_404(Manutencao, pk=pk)
        form = ManutencaoFinalizarForm(request.POST)

        if form.is_valid():
            try:
                finalizar_manutencao(
                    manutencao=manutencao,
                    data_saida=form.cleaned_data['data_saida'],
                    custo=form.cleaned_data.get('custo')
                )
                return redirect('manutencao_web:detalhe', pk=manutencao.pk)
            except DjangoValidationError as error:
                form.add_error(None, error)

        return render(request, self.template_name, {
            'manutencao': manutencao,
            'form': form,
        })


class ManutencaoCancelarView(View):
    template_name = 'manutencao/cancelar.html'

    def get(self, request, pk):
        manutencao = get_object_or_404(Manutencao, pk=pk)
        return render(request, self.template_name, {
            'manutencao': manutencao,
        })

    def post(self, request, pk):
        manutencao = get_object_or_404(Manutencao, pk=pk)

        try:
            cancelar_manutencao(manutencao)
            return redirect('manutencao_web:detalhe', pk=manutencao.pk)
        except DjangoValidationError as error:
            return render(request, self.template_name, {
                'manutencao': manutencao,
                'erro': error,
            })


class PecaListView(ListView):
    model = Peca
    template_name = 'manutencao/pecas_lista.html'
    context_object_name = 'pecas'
    queryset = Peca.objects.all().order_by('tipo_peca', 'fabricante')


class PecaDetailView(DetailView):
    model = Peca
    template_name = 'manutencao/pecas_detalhe.html'
    context_object_name = 'peca'


class PecaCreateView(CreateView):
    model = Peca
    form_class = PecaForm
    template_name = 'manutencao/pecas_form.html'
    success_url = reverse_lazy('manutencao_web:pecas_lista')


class PecaUpdateView(UpdateView):
    model = Peca
    form_class = PecaForm
    template_name = 'manutencao/pecas_form.html'
    success_url = reverse_lazy('manutencao_web:pecas_lista')


class PecaDeleteView(DeleteView):
    model = Peca
    template_name = 'manutencao/pecas_confirmar_delete.html'
    context_object_name = 'peca'
    success_url = reverse_lazy('manutencao_web:pecas_lista')


class PecaManutencaoListView(ListView):
    model = PecaManutencao
    template_name = 'manutencao/pecas_manutencao_lista.html'
    context_object_name = 'pecas_manutencao'
    queryset = PecaManutencao.objects.select_related(
        'manutencao',
        'peca'
    ).all().order_by('-id')


class PecaManutencaoDetailView(DetailView):
    model = PecaManutencao
    template_name = 'manutencao/pecas_manutencao_detalhe.html'
    context_object_name = 'peca_manutencao'


class PecaManutencaoCreateView(CreateView):
    model = PecaManutencao
    form_class = PecaManutencaoForm
    template_name = 'manutencao/pecas_manutencao_form.html'
    success_url = reverse_lazy('manutencao_web:pecas_manutencao_lista')

    def get_initial(self):
        initial = super().get_initial()
        manutencao_id = self.request.GET.get('manutencao')
        if manutencao_id:
            initial['manutencao'] = manutencao_id
        return initial

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields['manutencao'].queryset = Manutencao.objects.exclude(
            status__in=('CONCLUIDA', 'CANCELADA')
        ).order_by('-data_entrada')
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        manutencao_id = self.request.GET.get('manutencao')
        if manutencao_id:
            context['manutencao_selecionada'] = get_object_or_404(
                Manutencao,
                pk=manutencao_id
            )
        return context

    def get_success_url(self):
        return reverse('manutencao_web:detalhe', kwargs={
            'pk': self.object.manutencao_id
        })


class PecaManutencaoUpdateView(UpdateView):
    model = PecaManutencao
    form_class = PecaManutencaoForm
    template_name = 'manutencao/pecas_manutencao_form.html'
    success_url = reverse_lazy('manutencao_web:pecas_manutencao_lista')

    def dispatch(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.manutencao.status in ('CONCLUIDA', 'CANCELADA'):
            return redirect('manutencao_web:pecas_manutencao_detalhe', pk=self.object.pk)
        return super().dispatch(request, *args, **kwargs)


class PecaManutencaoDeleteView(DeleteView):
    model = PecaManutencao
    template_name = 'manutencao/pecas_manutencao_confirmar_delete.html'
    context_object_name = 'peca_manutencao'
    success_url = reverse_lazy('manutencao_web:pecas_manutencao_lista')

    def form_valid(self, form):
        if self.object.manutencao.status in ('CONCLUIDA', 'CANCELADA'):
            context = self.get_context_data(object=self.object)
            context['erro'] = 'Nao e possivel remover pecas de manutencoes concluidas ou canceladas.'
            return self.render_to_response(context)
        return super().form_valid(form)
