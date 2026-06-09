from django.shortcuts import render

from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from rest_framework import viewsets

from .forms import SolicitacaoForm
from .models import Solicitacao
from .serializers import SolicitacaoSerializer


class SolicitacaoListView(ListView):
    model = Solicitacao
    template_name = 'solicitacoes/lista.html'
    context_object_name = 'solicitacoes'
    queryset = Solicitacao.objects.select_related(
        'cliente',
        'veiculo',
        'local',
        'funcionario'
    ).all().order_by('-data_solicitacao')


class SolicitacaoDetailView(DetailView):
    model = Solicitacao
    template_name = 'solicitacoes/detalhe.html'
    context_object_name = 'solicitacao'


class SolicitacaoCreateView(CreateView):
    model = Solicitacao
    form_class = SolicitacaoForm
    template_name = 'solicitacoes/form.html'
    success_url = reverse_lazy('solicitacoes:lista')


class SolicitacaoUpdateView(UpdateView):
    model = Solicitacao
    form_class = SolicitacaoForm
    template_name = 'solicitacoes/form.html'
    success_url = reverse_lazy('solicitacoes:lista')


class SolicitacaoDeleteView(DeleteView):
    model = Solicitacao
    template_name = 'solicitacoes/confirmar_delete.html'
    context_object_name = 'solicitacao'
    success_url = reverse_lazy('solicitacoes:lista')


class SolicitacaoViewSet(viewsets.ModelViewSet):
    queryset = Solicitacao.objects.select_related(
        'cliente',
        'veiculo',
        'veiculo__grupo',
        'local',
        'funcionario'
    ).all()
    serializer_class = SolicitacaoSerializer
