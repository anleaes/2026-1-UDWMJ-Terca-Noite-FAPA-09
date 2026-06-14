"""
Comando: python manage.py popular_banco

Popula o banco com dados de teste realistas e VARIADOS:
  - 5 grupos de veiculo (Economico, Compacto, Intermediario, SUV, Premium)
  - ~30 veiculos distribuidos em varias marcas e modelos (para filtros em cascata)
  - 1 entrada de catalogo para cada veiculo
  - 5 clientes (senha padrao: senha123)
  - 3 funcionarios (senha padrao: senha123)
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

        # ── GRUPOS ────────────────────────────────────────────────────────
        self.stdout.write('Criando grupos...')
        grupos = {}
        dados_grupos = [
            ('Economico',     'Compactos de baixo consumo, ideais para uso urbano.',                    5,  89.90),
            ('Compacto',      'Hatches e sedans compactos com bom equilibrio entre custo e conforto.',  5, 109.90),
            ('Intermediario', 'Sedans e hatches medios com bom espaco interno e conforto.',             5, 139.90),
            ('SUV',           'Utilitarios esportivos com mais espaco para familias e bagagem.',        7, 199.90),
            ('Premium',       'Veiculos de alto padrao com acabamento e tecnologia superiores.',        5, 379.90),
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
        # Lista pensada para os filtros em cascata: cada GRUPO tem varias MARCAS,
        # e cada MARCA tem 1+ MODELOS. Total ~30 veiculos.
        self.stdout.write('Criando veiculos...')
        veiculos_data = [
            # (grupo,          placa,      renavam,       marca,        modelo,         fab,  mod,  cor,         km,    comb,       preco,  destaque, desc_comercial)

            # === ECONOMICO ===
            ('Economico',     'ECN0A01', '10000000001', 'Volkswagen', 'Gol',           2021, 2022, 'Branco',   38000, 'flex',      89.90, False, 'Hatch economico, ideal para uso urbano e baixa manutencao.'),
            ('Economico',     'ECN0A02', '10000000002', 'Volkswagen', 'up!',           2020, 2021, 'Vermelho', 45000, 'flex',      85.90, False, 'Compacto agil, perfeito para o dia a dia da cidade.'),
            ('Economico',     'ECN0A03', '10000000003', 'Fiat',       'Mobi',          2022, 2023, 'Cinza',    18000, 'flex',      82.90, False, 'O mais economico da frota. Otimo custo-beneficio.'),
            ('Economico',     'ECN0A04', '10000000004', 'Fiat',       'Uno',           2021, 2021, 'Branco',   29000, 'flex',      84.90, False, 'Classico brasileiro: simples, robusto e barato.'),
            ('Economico',     'ECN0A05', '10000000005', 'Chevrolet',  'Joy',           2020, 2021, 'Prata',    52000, 'flex',      88.90, False, 'Compacto confiavel com bom porta-malas.'),
            ('Economico',     'ECN0A06', '10000000006', 'Renault',    'Kwid',          2022, 2022, 'Laranja',  21000, 'flex',      87.90, True,  'Visual de SUV em tamanho compacto. Estiloso e economico.'),

            # === COMPACTO ===
            ('Compacto',      'CMP0B01', '20000000001', 'Volkswagen', 'Polo',          2022, 2023, 'Prata',    18000, 'flex',     109.90, True,  'O hatch mais vendido do segmento. Tecnologia e seguranca.'),
            ('Compacto',      'CMP0B02', '20000000002', 'Fiat',       'Argo',          2022, 2022, 'Branco',   24000, 'flex',     104.90, False, 'Design moderno e interior amplo para um hatch de entrada.'),
            ('Compacto',      'CMP0B03', '20000000003', 'Chevrolet',  'Onix',          2023, 2023, 'Preto',     9000, 'flex',     119.90, True,  'O hatch mais vendido do Brasil. Confortavel e pratico.'),
            ('Compacto',      'CMP0B04', '20000000004', 'Hyundai',    'HB20',          2022, 2023, 'Azul',     16000, 'flex',     112.90, False, 'Hatch sul-coreano com bom acabamento e garantia.'),
            ('Compacto',      'CMP0B05', '20000000005', 'Renault',    'Sandero',       2021, 2022, 'Cinza',    34000, 'flex',     102.90, False, 'Hatch com porta-malas generoso e bom conforto.'),
            ('Compacto',      'CMP0B06', '20000000006', 'Hyundai',    'HB20S',         2022, 2023, 'Prata',    19000, 'flex',     118.90, False, 'Versao sedan do HB20: mais espaco no porta-malas.'),

            # === INTERMEDIARIO ===
            ('Intermediario', 'INT0C01', '30000000001', 'Volkswagen', 'Virtus',        2022, 2023, 'Cinza',    24000, 'flex',     139.90, False, 'Sedan elegante com espaco interno generoso. Otimo para viagens.'),
            ('Intermediario', 'INT0C02', '30000000002', 'Volkswagen', 'Jetta',         2022, 2022, 'Preto',    31000, 'gasolina', 159.90, False, 'Sedan medio premium com motor TSI e cambio automatico.'),
            ('Intermediario', 'INT0C03', '30000000003', 'Toyota',     'Corolla',       2022, 2023, 'Branco',   28000, 'hibrido',  179.90, True,  'Tecnologia hibrida que combina economia e desempenho.'),
            ('Intermediario', 'INT0C04', '30000000004', 'Toyota',     'Yaris Sedan',   2021, 2022, 'Prata',    36000, 'flex',     139.90, False, 'Sedan compacto da Toyota: confiavel e economico.'),
            ('Intermediario', 'INT0C05', '30000000005', 'Honda',      'Civic',         2023, 2023, 'Azul',      7500, 'gasolina', 189.90, True,  'Esportividade e tecnologia em um sedan premium.'),
            ('Intermediario', 'INT0C06', '30000000006', 'Honda',      'City',          2022, 2023, 'Cinza',    19000, 'flex',     159.90, False, 'Sedan compacto Honda: refinamento e baixo consumo.'),
            ('Intermediario', 'INT0C07', '30000000007', 'Nissan',     'Sentra',        2021, 2022, 'Preto',    41000, 'gasolina', 149.90, False, 'Sedan medio com bom conforto e equipamentos.'),

            # === SUV ===
            ('SUV',           'SUV0D01', '40000000001', 'Jeep',       'Renegade',      2022, 2022, 'Verde',    27000, 'flex',     199.90, False, 'SUV compacto com visual aventureiro e bom espaco interno.'),
            ('SUV',           'SUV0D02', '40000000002', 'Jeep',       'Compass',       2022, 2023, 'Preto',    28000, 'flex',     239.90, True,  'SUV medio com tracao 4x4 opcional. Ideal para cidade e estrada.'),
            ('SUV',           'SUV0D03', '40000000003', 'Toyota',     'Corolla Cross', 2022, 2023, 'Branco',   22000, 'hibrido',  249.90, True,  'SUV hibrido: economia de carro pequeno com altura de SUV.'),
            ('SUV',           'SUV0D04', '40000000004', 'Toyota',     'SW4',           2021, 2022, 'Prata',    55000, 'diesel',   349.90, False, 'SUV grande, motor diesel, 7 lugares. Para familias.'),
            ('SUV',           'SUV0D05', '40000000005', 'Honda',      'HR-V',          2022, 2023, 'Prata',    21000, 'flex',     219.90, False, 'SUV compacto Honda: design moderno e dirigibilidade.'),
            ('SUV',           'SUV0D06', '40000000006', 'Volkswagen', 'T-Cross',       2022, 2023, 'Azul',     23000, 'flex',     219.90, False, 'SUV compacto VW com motor turbo e otimo acabamento.'),
            ('SUV',           'SUV0D07', '40000000007', 'Nissan',     'Kicks',         2021, 2022, 'Vermelho', 39000, 'flex',     189.90, False, 'SUV compacto com bom porta-malas e visual marcante.'),

            # === PREMIUM ===
            ('Premium',       'PRM0E01', '50000000001', 'BMW',        '320i',          2023, 2023, 'Cinza',     4200, 'gasolina', 389.90, True,  'Esportividade e luxo alemaes. Acabamento impecavel.'),
            ('Premium',       'PRM0E02', '50000000002', 'BMW',        'X1',            2022, 2023, 'Branco',   11500, 'gasolina', 419.90, False, 'SUV premium compacto da BMW. Tecnologia de ponta.'),
            ('Premium',       'PRM0E03', '50000000003', 'Mercedes',   'C 200',         2022, 2023, 'Preto',    11000, 'gasolina', 429.90, True,  'Icone da elegancia. Motor 1.5T com desempenho refinado.'),
            ('Premium',       'PRM0E04', '50000000004', 'Mercedes',   'GLA 200',       2022, 2022, 'Cinza',    15000, 'gasolina', 449.90, False, 'SUV compacto Mercedes-Benz: luxo em formato urbano.'),
            ('Premium',       'PRM0E05', '50000000005', 'Audi',       'A3 Sedan',      2023, 2023, 'Branco',    8500, 'gasolina', 369.90, False, 'Sedan compacto premium com cambio S tronic.'),
            ('Premium',       'PRM0E06', '50000000006', 'Audi',       'Q3',            2022, 2023, 'Preto',    13800, 'gasolina', 439.90, False, 'SUV premium Audi com motor TFSI e Virtual Cockpit.'),
        ]

        # URLs de imagens (Unsplash). Se alguma falhar, o front mostra placeholder.
        fotos_genericas = [
            'https://images.unsplash.com/photo-1503376780353-7e6692767b70?w=800',  # Lamborghini
            'https://images.unsplash.com/photo-1494976388531-d1058494cdd8?w=800',  # Mercedes vermelho
            'https://images.unsplash.com/photo-1542362567-b07e54358753?w=800',  # sedan
            'https://images.unsplash.com/photo-1583121274602-3e2820c69888?w=800',  # sedan moderno
            'https://images.unsplash.com/photo-1492144534655-ae79c964c9d7?w=800',  # classico
            'https://images.unsplash.com/photo-1568844293986-8d0400bd4745?w=800',  # generico
            'https://images.unsplash.com/photo-1552519507-da3b142c6e3d?w=800',  # esportivo
            'https://images.unsplash.com/photo-1606664515524-ed2f786a0bd6?w=800',  # SUV
            'https://images.unsplash.com/photo-1502877338535-766e1452684a?w=800',  # SUV branco
            'https://images.unsplash.com/photo-1605559424843-9e4c228bf1c2?w=800',  # BMW
            'https://images.unsplash.com/photo-1617531653332-bd46c24f2068?w=800',  # premium
            'https://images.unsplash.com/photo-1503736334956-4c8f8e92946d?w=800',  # generico
        ]

        veiculos = []
        for i, dados in enumerate(veiculos_data):
            grupo_nome, placa, renavam, marca, modelo, fab, mod, cor, km, comb, preco, destaque, desc_comercial = dados
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

            # cria catalogo correspondente
            foto_url = fotos_genericas[i % len(fotos_genericas)]
            Catalogo.objects.get_or_create(
                veiculo=v,
                defaults=dict(
                    preco_diaria=preco,
                    foto=foto_url,
                    descricao_comercial=desc_comercial,
                    destaque=destaque,
                    ativo=True,
                )
            )

        # ── CLIENTES ──────────────────────────────────────────────────────
        self.stdout.write('Criando clientes...')
        clientes_data = [
            ('Ana Paula Oliveira',  'ana.oliveira@email.com',   '123.456.789-00', '(51) 99100-1111', '12345678900', 'B',  datetime.date(2026, 8, 15)),
            ('Carlos Eduardo Lima', 'carlos.lima@email.com',    '234.567.890-11', '(51) 99200-2222', '23456789011', 'B',  datetime.date(2027, 12, 31)),
            ('Fernanda Costa',      'fernanda.costa@email.com', '345.678.901-22', '(51) 99300-3333', '34567890122', 'B',  datetime.date(2027, 3, 20)),
            ('Rafael Souza',        'rafael.souza@email.com',   '456.789.012-33', '(51) 99400-4444', '45678901233', 'AB', datetime.date(2028, 6, 1)),
            ('Juliana Mendes',      'juliana.mendes@email.com', '567.890.123-44', '(51) 99500-5555', '56789012344', 'B',  datetime.date(2028, 1, 10)),
        ]
        clientes = []
        for nome, email, cpf, tel, cnh, cat_cnh, val_cnh in clientes_data:
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
            ('Marcos Antonio Silva', 'marcos.silva@applocacao.com',   '678.901.234-55', '(51) 98001-0001', 'Gerente',           'ADMIN'),
            ('Beatriz Santos',       'beatriz.santos@applocacao.com', '789.012.345-66', '(51) 98002-0002', 'Atendente',         'OPERADOR'),
            ('Diego Ferreira',       'diego.ferreira@applocacao.com', '890.123.456-77', '(51) 98003-0003', 'Analista de Frota', 'OPERADOR'),
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
            ('Matriz Porto Alegre',   'Av. Borges de Medeiros, 2000', 'Porto Alegre',  'RS', '90110-150'),
            ('Filial Aeroporto POA',  'Av. Severo Dullius, 90010',    'Porto Alegre',  'RS', '90200-310'),
            ('Filial Canoas',         'Av. Victor Barreto, 1500',     'Canoas',        'RS', '92310-000'),
            ('Filial Novo Hamburgo',  'Rua Frederico Ritter, 800',    'Novo Hamburgo', 'RS', '93310-100'),
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
            (clientes[0], veiculos[0],  locais[0], funcionarios[0], hoje - datetime.timedelta(10), hoje - datetime.timedelta(5), 'Viagem de negocios',  'finalizada'),
            (clientes[1], veiculos[7],  locais[1], funcionarios[1], hoje - datetime.timedelta(3),  hoje + datetime.timedelta(2), 'Viagem a lazer',      'aprovada'),
            (clientes[2], veiculos[14], locais[0], None,            hoje + datetime.timedelta(2),  hoje + datetime.timedelta(7), 'Mudanca residencial', 'pendente'),
            (clientes[3], veiculos[20], locais[3], None,            hoje + datetime.timedelta(5),  hoje + datetime.timedelta(8), 'Uso corporativo',     'pendente'),
            (clientes[4], veiculos[16], locais[2], funcionarios[2], hoje - datetime.timedelta(15), hoje - datetime.timedelta(8), 'Visita familiar',     'finalizada'),
            (clientes[0], veiculos[27], locais[1], funcionarios[1], hoje - datetime.timedelta(1),  hoje + datetime.timedelta(4), 'Evento corporativo',  'aprovada'),
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
        aloc_data = [
            (solicitacoes[1], hoje - datetime.timedelta(3), hoje + datetime.timedelta(2), None, veiculos[7].quilometragem,  None, 'ativa'),
            (solicitacoes[5], hoje - datetime.timedelta(1), hoje + datetime.timedelta(4), None, veiculos[27].quilometragem, None, 'ativa'),
        ]
        for sol, ini, fim_prev, fim_real, km_ini, km_fin, status in aloc_data:
            if Alocacao.objects.filter(solicitacao=sol).exists():
                a = Alocacao.objects.get(solicitacao=sol)
                self.stdout.write(f'  Alocacao #{a.id} ja existe')
            else:
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
            (veiculos[2], 'Revisao geral',  'Troca de oleo, filtros e verificacao geral.',     hoje - datetime.timedelta(20), hoje - datetime.timedelta(14), 450.00, 'CONCLUIDA'),
            (veiculos[19], 'Troca de pneus', 'Substituicao dos quatro pneus por desgaste.',     hoje - datetime.timedelta(5),  None,                          800.00, 'EM_ANDAMENTO'),
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
            ('Filtro de oleo',    'Bosch',    45.90),
            ('Filtro de ar',      'Fram',     38.50),
            ('Pneu 185/65 R15',   'Pirelli', 320.00),
            ('Pastilha de freio', 'TRW',      89.90),
        ]
        pecas = []
        for tipo, fab, preco in pecas_data:
            p, criado = Peca.objects.get_or_create(
                tipo_peca=tipo, fabricante=fab,
                defaults=dict(preco_unitario=preco)
            )
            pecas.append(p)
            status = 'criada' if criado else 'ja existe'
            self.stdout.write(f'  {tipo} - {fab} ({status})')

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

        self.stdout.write(self.style.SUCCESS('\nBanco populado com sucesso!'))
        self.stdout.write(f'  {len(grupos)} grupos  |  {len(veiculos)} veiculos  |  {len(veiculos)} catalogos')
        self.stdout.write(f'  {len(clientes)} clientes  |  {len(funcionarios)} funcionarios  |  {len(locais)} locais')
        self.stdout.write(f'  {len(solicitacoes)} solicitacoes  |  2 alocacoes  |  {len(manutencoes)} manutencoes  |  {len(pecas)} pecas')
        self.stdout.write(self.style.WARNING('\nLOGINS DISPONIVEIS (senha de todos: senha123):'))
        self.stdout.write('  CLIENTES:')
        for c in clientes:
            self.stdout.write(f'    {c.email}')
        self.stdout.write('  FUNCIONARIOS:')
        for f in funcionarios:
            self.stdout.write(f'    {f.email}')
