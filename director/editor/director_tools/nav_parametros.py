"""Calcula configuracao de tiles sem depender do Unreal; nunca altera a cena."""
import math
from fractions import Fraction


def _positivo(valor, nome):
    if isinstance(valor, bool):
        raise ValueError(f'{nome} precisa ser positivo e finito')
    try:
        n = float(valor)
    except (TypeError, ValueError):
        raise ValueError(f'{nome} precisa ser positivo e finito') from None
    if not math.isfinite(n) or n <= 0:
        raise ValueError(f'{nome} precisa ser positivo e finito')
    return n


def tile_sugerido(celulas, tile):
    """Multiplo comum mais proximo. Proposta, nao autorizacao para mudar o level."""
    fr = [Fraction(str(c)).limit_denominator(10000) for c in celulas]
    if any(f <= 0 for f in fr):
        raise ValueError('precisao de celula insuficiente para propor tile compativel')
    multiplo = Fraction(math.lcm(*(f.numerator for f in fr)), math.gcd(*(f.denominator for f in fr)))
    return float(multiplo * max(1, round(Fraction(str(tile)) / multiplo)))


def preparar(perfis, tile_atual, escopo, celula, altura, tile_cm=None):
    if escopo not in ('regiao', 'level'):
        raise ValueError('escopo deve ser regiao ou level')
    if len(perfis) != 3:
        raise ValueError('esperados tres perfis nativos: LOW, DEFAULT e HIGH')
    celula = _positivo(celula, 'celula_cm')
    altura = _positivo(altura, 'altura_cm')
    tile = _positivo(tile_atual if tile_cm is None else tile_cm, 'tile_cm')
    novos = [dict(p) for p in perfis]
    for i, p in enumerate(novos):
        if escopo == 'level' or i == 2:
            p.update(cell_size=celula, cell_height=altura)
    cells = [_positivo(p['cell_size'], 'cell_size') for p in novos]
    if any(c > tile for c in cells):
        raise ValueError('tile_cm precisa comportar pelo menos uma celula de cada perfil')
    # O gerador Recast usa TruncToInt(TileSizeUU / CellSize) por resolucao.
    # Valores retornados pelo motor podem carregar erro float32 (ex.: 1000/53).
    efetivos = []
    for c in cells:
        inteiro = round(tile / c)
        quantidade = inteiro if abs(tile-inteiro*c) <= .001 else math.floor(tile/c)
        efetivos.append(quantidade*c)
    if max(efetivos) - min(efetivos) > .001:
        sugestao = tile_sugerido(cells, tile)
        raise ValueError(f'perfis geram tiles desalinhados {efetivos} cm; '
                         f'proposta: tile_cm={sugestao:g}. Alterar tile_cm afeta o level inteiro; '
                         'nao foi aplicado automaticamente')
    return {'resolucoes': novos, 'tile_cm': tile, 'tiles_efetivos_cm': efetivos,
            'tile_alterado': abs(tile - float(tile_atual)) > .001}
