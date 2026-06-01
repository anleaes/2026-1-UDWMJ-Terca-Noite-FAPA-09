from django.urls import path

from .views import (
    ClienteListView,
    ClienteDetailView,
    ClienteCreateView,
    ClienteUpdateView,
    ClienteDeleteView,
    FuncionarioListView,
    FuncionarioDetailView,
    FuncionarioCreateView,
    FuncionarioUpdateView,
    FuncionarioDeleteView,
)


app_name = 'users_web'


urlpatterns = [
    path('clientes/', ClienteListView.as_view(), name='clientes_lista'),
    path('clientes/listar/', ClienteListView.as_view(), name='clientes_listar'),
    path('clientes/novo/', ClienteCreateView.as_view(), name='clientes_novo'),
    path('clientes/criar/', ClienteCreateView.as_view(), name='clientes_criar'),
    path('clientes/<int:pk>/', ClienteDetailView.as_view(), name='clientes_detalhe'),
    path('clientes/<int:pk>/editar/', ClienteUpdateView.as_view(), name='clientes_editar'),
    path('clientes/<int:pk>/excluir/', ClienteDeleteView.as_view(), name='clientes_excluir'),
    path('clientes/<int:pk>/deletar/', ClienteDeleteView.as_view(), name='clientes_deletar'),

    path('funcionarios/', FuncionarioListView.as_view(), name='funcionarios_lista'),
    path('funcionarios/listar/', FuncionarioListView.as_view(), name='funcionarios_listar'),
    path('funcionarios/novo/', FuncionarioCreateView.as_view(), name='funcionarios_novo'),
    path('funcionarios/criar/', FuncionarioCreateView.as_view(), name='funcionarios_criar'),
    path('funcionarios/<int:pk>/', FuncionarioDetailView.as_view(), name='funcionarios_detalhe'),
    path('funcionarios/<int:pk>/editar/', FuncionarioUpdateView.as_view(), name='funcionarios_editar'),
    path('funcionarios/<int:pk>/excluir/', FuncionarioDeleteView.as_view(), name='funcionarios_excluir'),
    path('funcionarios/<int:pk>/deletar/', FuncionarioDeleteView.as_view(), name='funcionarios_deletar'),
]