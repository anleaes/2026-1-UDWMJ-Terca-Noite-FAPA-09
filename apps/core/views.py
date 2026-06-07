from django.shortcuts import render, get_object_or_404
from catalogo.models import Catalogo


def _normalizar_url_imgur(url):
    """
    Garante que a URL do Imgur aponta para o arquivo de imagem direto,
    não para a página HTML do Imgur (que não carrega em <img>).

    Exemplos de conversao:
      https://imgur.com/abc1234          -> https://i.imgur.com/abc1234.jpeg
      https://imgur.com/abc1234.jpeg     -> https://i.imgur.com/abc1234.jpeg
      https://www.imgur.com/a/abc1234    -> mantém (album, nao converte)
      https://i.imgur.com/abc1234.jpeg   -> mantém (ja é direto)
      https://outra-url.com/foto.jpg     -> mantém (nao é imgur)
    """
    if not url:
        return url

    import re

    # Já é link direto do Imgur — não mexe
    if url.startswith('https://i.imgur.com/') or url.startswith('http://i.imgur.com/'):
        return url

    # Página do Imgur: imgur.com/<id> ou www.imgur.com/<id>
    match = re.match(
        r'https?://(?:www\.)?imgur\.com/([a-zA-Z0-9]+)(?:\.[a-zA-Z]+)?$',
        url
    )
    if match:
        img_id = match.group(1)
        return f'https://i.imgur.com/{img_id}.jpeg'

    # Qualquer outra coisa (outros domínios, albums /a/, etc.) — retorna sem alterar
    return url


def home(request):
    catalogos = Catalogo.objects.select_related(
        'veiculo', 'veiculo__grupo'
    ).filter(ativo=True).order_by('-destaque', 'preco_diaria')

    # Normaliza URLs do Imgur em memória (não salva no banco)
    for c in catalogos:
        if c.foto:
            c.foto = _normalizar_url_imgur(c.foto)

    return render(request, 'core/home.html', {'catalogos': catalogos})


def veiculo_detalhe(request, pk):
    catalogo = get_object_or_404(
        Catalogo.objects.select_related('veiculo', 'veiculo__grupo'),
        pk=pk
    )
    if catalogo.foto:
        catalogo.foto = _normalizar_url_imgur(catalogo.foto)

    return render(request, 'core/veiculo_detalhe.html', {'catalogo': catalogo})
