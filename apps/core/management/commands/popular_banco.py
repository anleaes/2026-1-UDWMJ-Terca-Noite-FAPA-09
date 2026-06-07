"""
Comando: python manage.py popular_banco

Popula o banco com dados de teste realistas:
  - 4 grupos de veiculo
  - 10 veiculos
  - 10 entradas no catalogo (com URLs de imagem do Imgur)
  - 5 clientes
  - 3 funcionarios
  - 4 locais
  - 6 solicitacoes (varios status)
  - 2 alocacoes ativas
  - 2 manutencoes
  - 4 pecas

Uso:
    python manage.py popular_banco
    python manage.py popular_banco --limpar   # apaga tudo antes de inserir
"""

from django.core.management.base import BaseCommand
from django.db import transaction
import datetime


class Command(BaseCommand):
    help = 'Popula o banco com dados de teste'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limpar',
            action='store_true',
            help='Apaga todos os dados existentes antes de inserir',
        )

    @transaction.atomic
    def handle(self, *args, **options):
        # imports aqui para evitar problemas de importacao circular
        from grupo_veiculo.models import GrupoVeiculo
        from veiculo.models import Veiculo
        from catalogo.models import Catalogo
        from users.models import Cliente, Funcionario
        from locais.models import Local
        from solicitacoes.models import Solicitacao
        from alocacao.models import Alocacao, HistoricoAlocacao
        from manutencao.models import Manutencao, Peca, PecaManutencao

        if options['limpar']:
            self.stdout.write('Limpando dados existentes...')
            PecaManutencao.objects.all().delete()
            HistoricoAlocacao.objects.all().delete()
            Alocacao.objects.all().delete()
            Solicitacao.objects.all().delete()
            Manutencao.objects.all().delete()
            Catalogo.objects.all().delete()
            Veiculo.objects.all().delete()
            GrupoVeiculo.objects.all().delete()
            Cliente.objects.all().delete()
            Funcionario.objects.all().delete()
            Local.objects.all().delete()
            Peca.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Dados apagados.'))

        today = datetime.date.today

        # ── GRUPOS ────────────────────────────────────────────────────────
        self.stdout.write('Criando grupos...')
        grupos = {}
        dados_grupos = [
            ('Economico',  'Veiculos compactos e de baixo consumo, ideais para uso urbano.',        5,  89.90),
            ('Intermediario', 'Sedas e hatches medios com bom conforto e espaco interno.',          5, 129.90),
            ('SUV',        'Utilitarios esportivos com maior espaco e conforto para familias.',     7, 199.90),
            ('Premium',    'Veiculos de alto padrao com acabamento e tecnologia superiores.',       5, 349.90),
        ]
        for nome, desc, cap, valor in dados_grupos:
            g, criado = GrupoVeiculo.objects.get_or_create(
                nome=nome,
                defaults=dict(descricao=desc, capacidade_passageiros=cap,
                              valor_base_diaria=valor, ativo=True)
            )
            grupos[nome] = g
            status = 'criado' if criado else 'ja existe'
            self.stdout.write(f'  {nome} ({status})')

        # ── VEICULOS ──────────────────────────────────────────────────────
        self.stdout.write('Criando veiculos...')
        veiculos_data = [
            # grupo,          placa,       renavam,         marca,      modelo,        fab,  mod,  cor,          km,      comb
            ('Economico',    'ABC1D23',  '12345678901',  'Volkswagen', 'Polo',        2022, 2023, 'Prata',       18000, 'flex'),
            ('Economico',    'DEF2E34',  '23456789012',  'Fiat',       'Argo',        2021, 2022, 'Branco',      32000, 'flex'),
            ('Economico',    'GHI3F45',  '34567890123',  'Chevrolet',  'Onix',        2023, 2023, 'Preto',        9000, 'flex'),
            ('Intermediario','JKL4G56',  '45678901234',  'Volkswagen', 'Virtus',      2022, 2022, 'Cinza',       24000, 'flex'),
            ('Intermediario','MNO5H67',  '56789012345',  'Toyota',     'Corolla',     2021, 2022, 'Branco',      41000, 'hibrido'),
            ('Intermediario','PQR6I78',  '67890123456',  'Honda',      'Civic',       2023, 2023, 'Azul',         7500, 'gasolina'),
            ('SUV',          'STU7J89',  '78901234567',  'Jeep',       'Compass',     2022, 2022, 'Preto',       28000, 'flex'),
            ('SUV',          'VWX8K90',  '89012345678',  'Toyota',     'SW4',         2021, 2022, 'Branco',      55000, 'diesel'),
            ('Premium',      'YZA9L01',  '90123456789',  'BMW',        '320i',        2023, 2023, 'Cinza',        4200, 'gasolina'),
            ('Premium',      'BCD0M12',  '01234567890',  'Mercedes',   'C 200',       2022, 2023, 'Preto',       11000, 'gasolina'),
        ]
        veiculos = []
        for grupo_nome, placa, renavam, marca, modelo, fab, mod, cor, km, comb in veiculos_data:
            v, criado = Veiculo.objects.get_or_create(
                placa=placa,
                defaults=dict(
                    grupo=grupos[grupo_nome], renavam=renavam,
                    marca=marca, modelo=modelo,
                    ano_fabricacao=fab, ano_modelo=mod,
                    cor=cor, quilometragem=km,
                    tipo_combustivel=comb, status='disponivel'
                )
            )
            veiculos.append(v)
            status = 'criado' if criado else 'ja existe'
            self.stdout.write(f'  {marca} {modelo} {placa} ({status})')

        # ── CATALOGO ──────────────────────────────────────────────────────
        # URLs de imagens publicas do Imgur (JPEGs diretos, sem redirecionamento)
        self.stdout.write('Criando catalogo...')
        fotos = [
            'https://i.imgur.com/9QFtf5D.jpeg',  # Polo prata
            'https://i.imgur.com/gSClyQD.jpeg',  # Argo branco
            'https://i.imgur.com/QwTc2pN.jpeg',  # Onix preto
            'https://i.imgur.com/LkP3nZJ.jpeg',  # Virtus cinza
            'https://i.imgur.com/H8vRmKE.jpeg',  # Corolla branco
            'https://i.imgur.com/XdT7kBP.jpeg',  # Civic azul
            'https://i.imgur.com/2mFpLsQ.jpeg',  # Compass preto
            'https://i.imgur.com/rN4cWtV.jpeg',  # SW4 branco
            'https://i.imgur.com/DqYjU6A.jpeg',  # BMW cinza
            'https://i.imgur.com/nKbPx3M.jpeg',  # Mercedes preto
        ]
        precos = [89.90, 99.90, 94.90, 139.90, 179.90, 169.90, 219.90, 239.90, 389.90, 429.90]
        descricoes = [
            'Compacto ideal para o dia a dia urbano. Baixo consumo e facil estacionamento.',
            'Design moderno e interior amplo para um hatch de entrada. Excelente custo-beneficio.',
            'O hatch mais vendido do Brasil. Confortavel, economico e pratico.',
            'Seda elegante com espaco interno generoso. Perfeito para viagens longas.',
            'Tecnologia hibrida que combina economia e desempenho. Zero emissoes no transito lento.',
            'Esportividade e tecnologia em um sedan premium. Ideal para quem busca performance.',
            'SUV compacto com tração 4x4 opcional. Ideal para cidade e estrada.',
            'SUV robusto com motor diesel. Capacidade para 7 passageiros e bagagem.',
            'Esportividade e luxo alemaes. Acabamento impecavel e tecnologia de ponta.',
            'O icone da elegancia. Motor 1.5T com desempenho refinado e conforto absoluto.',
        ]
        destaques = [False, False, True, False, True, False, True, False, True, True]
        for i, v in enumerate(veiculos):
            cat, criado = Catalogo.objects.get_or_create(
                veiculo=v,
                defaults=dict(
                    preco_diaria=precos[i],
                    foto=fotos[i],
                    descricao_comercial=descricoes[i],
                    destaque=destaques[i],
                    ativo=True,
                )
            )
            status = 'criado' if criado else 'ja existe'
            self.stdout.write(f'  Catalogo {v.modelo} ({status})')

        # ── CLIENTES ──────────────────────────────────────────────────────
        self.stdout.write('Criando clientes...')
        clientes_data = [
            ('Ana Paula Oliveira',  'ana.oliveira@email.com',   '123.456.789-00', '(51) 99100-1111', '12345678900', 'B', datetime.date(2026, 8, 15)),
            ('Carlos Eduardo Lima', 'carlos.lima@email.com',    '234.567.890-11', '(51) 99200-2222', '23456789011', 'B', datetime.date(2025, 12, 31)),
            ('Fernanda Costa',      'fernanda.costa@email.com', '345.678.901-22', '(51) 99300-3333', '34567890122', 'B', datetime.date(2027, 3, 20)),
            ('Rafael Souza',        'rafael.souza@email.com',   '456.789.012-33', '(51) 99400-4444', '45678901233', 'AB','2026-06-01'),
            ('Juliana Mendes',      'juliana.mendes@email.com', '567.890.123-44', '(51) 99500-5555', '56789012344', 'B', datetime.date(2028, 1, 10)),
        ]
        clientes = []
        for nome, email, cpf, tel, cnh, cat_cnh, val_cnh in clientes_data:
            if isinstance(val_cnh, str):
                val_cnh = datetime.date.fromisoformat(val_cnh)
            c, criado = Cliente.objects.get_or_create(
                email=email,
                defaults=dict(
                    nome=nome, senha='senha123', cpf=cpf,
                    telefone=tel, status='ATIVO',
                    cnh=cnh, categoria_cnh=cat_cnh, validade_cnh=val_cnh,
                )
            )
            clientes.append(c)
            status = 'criado' if criado else 'ja existe'
            self.stdout.write(f'  {nome} ({status})')

        # ── FUNCIONARIOS ──────────────────────────────────────────────────
        self.stdout.write('Criando funcionarios...')
        funcs_data = [
            ('Marcos Antonio Silva', 'marcos.silva@applocacao.com', '678.901.234-55', '(51) 98001-0001', 'Gerente',            'ADMIN'),
            ('Beatriz Santos',       'beatriz.santos@applocacao.com','789.012.345-66', '(51) 98002-0002', 'Atendente',          'OPERADOR'),
            ('Diego Ferreira',       'diego.ferreira@applocacao.com','890.123.456-77', '(51) 98003-0003', 'Analista de Frota',  'OPERADOR'),
        ]
        funcionarios = []
        for nome, email, cpf, tel, cargo, nivel in funcs_data:
            f, criado = Funcionario.objects.get_or_create(
                email=email,
                defaults=dict(
                    nome=nome, senha='senha123', cpf=cpf,
                    telefone=tel, status='ATIVO',
                    cargo=cargo, nivel_acesso=nivel, ativo=True,
                )
            )
            funcionarios.append(f)
            status = 'criado' if criado else 'ja existe'
            self.stdout.write(f'  {nome} ({status})')

        # ── LOCAIS ────────────────────────────────────────────────────────
        self.stdout.write('Criando locais...')
        locais_data = [
            ('Matriz Porto Alegre',   'Av. Borges de Medeiros, 2000', 'Porto Alegre', 'RS', '90110-150'),
            ('Filial Aeroporto POA',  'Av. Severo Dullius, 90010',   'Porto Alegre', 'RS', '90200-310'),
            ('Filial Canoas',         'Av. Victor Barreto, 1500',    'Canoas',       'RS', '92310-000'),
            ('Filial Novo Hamburgo',  'Rua Frederico Ritter, 800',   'Novo Hamburgo','RS', '93310-100'),
        ]
        locais = []
        for nome, end, cidade, estado, cep in locais_data:
            l, criado = Local.objects.get_or_create(
                nome=nome,
                defaults=dict(endereco=end, cidade=cidade, estado=estado, cep=cep)
            )
            locais.append(l)
            status = 'criado' if criado else 'ja existe'
            self.stdout.write(f'  {nome} ({status})')

        # ── SOLICITACOES ──────────────────────────────────────────────────
        self.stdout.write('Criando solicitacoes...')
        hoje = datetime.date.today()
        sol_data = [
            # cliente, veiculo, local, func,   inicio,        fim,            motivo,             status
            (clientes[0], veiculos[0], locais[0], funcionarios[0], hoje - datetime.timedelta(10), hoje - datetime.timedelta(5), 'Viagem de negocios', 'finalizada'),
            (clientes[1], veiculos[3], locais[1], funcionarios[1], hoje - datetime.timedelta(3),  hoje + datetime.timedelta(2), 'Viagem a lazer',     'aprovada'),
            (clientes[2], veiculos[6], locais[0], None,            hoje + datetime.timedelta(2),  hoje + datetime.timedelta(7), 'Mudanca residencial','pendente'),
            (clientes[3], veiculos[8], locais[3], None,            hoje + datetime.timedelta(5),  hoje + datetime.timedelta(8), 'Uso corporativo',    'pendente'),
            (clientes[4], veiculos[4], locais[2], funcionarios[2], hoje - datetime.timedelta(15), hoje - datetime.timedelta(8), 'Visita familiar',    'finalizada'),
            (clientes[0], veiculos[9], locais[1], funcionarios[1], hoje - datetime.timedelta(1),  hoje + datetime.timedelta(4), 'Evento corporativo', 'aprovada'),
        ]
        solicitacoes = []
        for i, (cli, vei, loc, func, ini, fim, motivo, status) in enumerate(sol_data):
            if Solicitacao.objects.filter(cliente=cli, veiculo=vei, data_inicio_desejada=ini).exists():
                s = Solicitacao.objects.get(cliente=cli, veiculo=vei, data_inicio_desejada=ini)
                self.stdout.write(f'  Solicitacao #{s.id} ja existe')
            else:
                s = Solicitacao.objects.create(
                    cliente=cli, veiculo=vei, local=loc, funcionario=func,
                    data_inicio_desejada=ini, data_fim_desejada=fim,
                    motivo=motivo, status=status,
                )
                self.stdout.write(f'  Solicitacao #{s.id} {cli.nome} / {vei.modelo} ({status}) criada')
            solicitacoes.append(s)

        # ── ALOCACOES ─────────────────────────────────────────────────────
        self.stdout.write('Criando alocacoes...')
        # usa solicitacoes aprovadas (indices 1 e 5)
        aloc_data = [
            (solicitacoes[1], hoje - datetime.timedelta(3),  hoje + datetime.timedelta(2),  None,  veiculos[3].quilometragem, None,   'ativa'),
            (solicitacoes[5], hoje - datetime.timedelta(1),  hoje + datetime.timedelta(4),  None,  veiculos[9].quilometragem, None,   'ativa'),
        ]
        for sol, ini, fim_prev, fim_real, km_ini, km_fin, status in aloc_data:
            if Alocacao.objects.filter(solicitacao=sol).exists():
                a = Alocacao.objects.get(solicitacao=sol)
                self.stdout.write(f'  Alocacao #{a.id} ja existe')
            else:
                # marca veiculo como alocado
                sol.veiculo.status = 'alocado'
                sol.veiculo.save()
                a = Alocacao.objects.create(
                    solicitacao=sol, data_inicio=ini,
                    data_fim_prevista=fim_prev, data_fim_real=fim_real,
                    km_inicial=km_ini, km_final=km_fin, status=status,
                )
                HistoricoAlocacao.objects.create(
                    alocacao=a, status_anterior='nova', status_novo='ativa',
                    responsavel_alteracao='Sistema',
                )
                self.stdout.write(f'  Alocacao #{a.id} ({status}) criada')

        # ── MANUTENCOES ───────────────────────────────────────────────────
        self.stdout.write('Criando manutencoes...')
        man_data = [
            (veiculos[1], 'Revisao geral',    'Troca de oleo, filtros e verificacao geral do veiculo.',  hoje - datetime.timedelta(20), hoje - datetime.timedelta(14), 450.00, 'CONCLUIDA'),
            (veiculos[7], 'Troca de pneus',   'Substituicao dos quatro pneus por desgaste.',             hoje - datetime.timedelta(5),  None,                          800.00, 'EM_ANDAMENTO'),
        ]
        manutencoes = []
        for vei, tipo, desc, entrada, saida, custo, status in man_data:
            if Manutencao.objects.filter(veiculo=vei, tipo_manutencao=tipo).exists():
                m = Manutencao.objects.get(veiculo=vei, tipo_manutencao=tipo)
                self.stdout.write(f'  Manutencao #{m.id} ja existe')
            else:
                if status == 'EM_ANDAMENTO':
                    vei.status = 'manutencao'
                    vei.save()
                m = Manutencao.objects.create(
                    veiculo=vei, tipo_manutencao=tipo, descricao=desc,
                    data_entrada=entrada, data_saida=saida,
                    custo=custo, status=status,
                )
                self.stdout.write(f'  Manutencao #{m.id} {tipo} ({status}) criada')
            manutencoes.append(m)

        # ── PECAS ─────────────────────────────────────────────────────────
        self.stdout.write('Criando pecas...')
        pecas_data = [
            ('Filtro de oleo',   'Bosch',      45.90),
            ('Filtro de ar',     'Fram',        38.50),
            ('Pneu 185/65 R15',  'Pirelli',    320.00),
            ('Pastilha de freio','TRW',         89.90),
        ]
        pecas = []
        for tipo, fab, preco in pecas_data:
            p, criado = Peca.objects.get_or_create(
                tipo_peca=tipo, fabricante=fab,
                defaults=dict(preco_unitario=preco)
            )
            pecas.append(p)
            status = 'criada' if criado else 'ja existe'
            self.stdout.write(f'  {tipo} — {fab} ({status})')

        # vincula pecas na manutencao concluida
        m_concluida = manutencoes[0]
        for peca, qtd in [(pecas[0], 1), (pecas[1], 1)]:
            if not PecaManutencao.objects.filter(manutencao=m_concluida, peca=peca).exists():
                PecaManutencao.objects.create(
                    manutencao=m_concluida, peca=peca,
                    quantidade=qtd,
                    preco_unitario=peca.preco_unitario,
                    sub_total=peca.preco_unitario * qtd,
                )
                self.stdout.write(f'  PecaManutencao: {qtd}x {peca.tipo_peca} na manutencao #{m_concluida.id}')

        self.stdout.write(self.style.SUCCESS('\nBanco populado com sucesso!'))
        self.stdout.write('  4 grupos  |  10 veiculos  |  10 catalogo')
        self.stdout.write('  5 clientes  |  3 funcionarios  |  4 locais')
        self.stdout.write('  6 solicitacoes  |  2 alocacoes  |  2 manutencoes  |  4 pecas')
