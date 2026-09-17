"""Manos de la rejilla 13×13: notación, filas y tramos.

La rejilla va de A a 2 en filas y columnas. Las parejas están en la diagonal,
las suited por encima (fila = carta alta) y las offsuit por debajo (columna =
carta alta), como en la web.
"""
import re
from dataclasses import dataclass

RANGOS = 'AKQJT98765432'
NADA = {'nada', '-', 'ninguna', 'ninguno'}
_MANO = re.compile(r'^([2-9TJQKA])([2-9TJQKA])([SO]?)$', re.I)


def mano_de(i, j):
    if i == j:
        return RANGOS[i] * 2
    if i < j:
        return RANGOS[i] + RANGOS[j] + 's'
    return RANGOS[j] + RANGOS[i] + 'o'


def celda_de(mano):
    alta, baja = RANGOS.index(mano[0]), RANGOS.index(mano[1])
    if len(mano) == 2 or mano[2] == 's':
        return alta, baja
    return baja, alta


def combos(mano):
    return 6 if len(mano) == 2 else 4 if mano[2] == 's' else 12


def _partes(token):
    x = _MANO.match(token.strip().replace('10', 'T'))
    if not x:
        raise ValueError(f'«{token}» no es una mano (ejemplos: AKs, K9o, 77)')
    a, b, palo = x[1].upper(), x[2].upper(), x[3].lower()
    if RANGOS.index(a) > RANGOS.index(b):
        a, b = b, a
    if a == b and palo:
        raise ValueError(f'«{token}»: una pareja no lleva s ni o')
    return a, b, palo


def normalizar(token):
    a, b, palo = _partes(token)
    if a != b and not palo:
        raise ValueError(f'«{token}»: falta decir si es suited (s) u offsuit (o)')
    return a + b + palo


def _variantes(token):
    """AK -> [AKs, AKo]; el resto, la mano tal cual."""
    a, b, palo = _partes(token)
    if a == b:
        return [a + b]
    return [a + b + palo] if palo else [a + b + 's', a + b + 'o']


@dataclass(frozen=True)
class Fila:
    clave: str
    nombre: str
    manos: tuple


def _filas():
    filas = [Fila('parejas', 'parejas', tuple(r * 2 for r in RANGOS))]
    for tipo, sufijo in (('suited', 's'), ('offsuit', 'o')):
        for i, r in enumerate(RANGOS[:-1]):
            filas.append(Fila(f'{r}{sufijo}', f'fila de la {r}, {tipo}',
                              tuple(r + k + sufijo for k in RANGOS[i + 1:])))
    return filas


FILAS = _filas()
_FILA_DE = {m: f for f in FILAS for m in f.manos}


def fila_de(mano):
    return _FILA_DE[mano]


def fila_por_clave(clave):
    return next(f for f in FILAS if f.clave == clave)


def _expandir_token(token):
    manos = set()
    if '-' in token:
        izq, der = token.split('-', 1)
        a_s, b_s = _variantes(izq), _variantes(der)
        if len(a_s) != len(b_s):
            raise ValueError(f'«{token}»: los dos extremos tienen que ser del mismo tipo')
        for a, b in zip(a_s, b_s):
            fila = fila_de(a)
            if fila_de(b) is not fila:
                raise ValueError(f'«{token}»: {a} y {b} no están en la misma fila')
            i, j = sorted((fila.manos.index(a), fila.manos.index(b)))
            manos.update(fila.manos[i:j + 1])
    elif token.endswith('+'):
        for base in _variantes(token[:-1]):
            fila = fila_de(base)
            manos.update(fila.manos[:fila.manos.index(base) + 1])
    else:
        manos.update(_variantes(token))
    return manos


def expandir(texto):
    """'KQs-K9s 22+ AKo' -> conjunto de manos. Lanza ValueError si algo no se entiende."""
    manos = set()
    for token in re.split(r'[\s,]+', texto.strip()):
        if token:
            manos |= _expandir_token(token)
    return manos


def leer_frontera(texto, fila):
    """Respuesta sobre una fila. Una mano sola significa esa y todo lo de encima."""
    t = texto.strip()
    if t.lower() in NADA:
        return set()
    sufijo = '' if fila.clave == 'parejas' else fila.clave[1]
    tokens = [_con_sufijo(tok, sufijo) for tok in re.split(r'[\s,]+', t) if tok]
    if len(tokens) == 1 and '-' not in tokens[0] and not tokens[0].endswith('+'):
        base = normalizar(tokens[0])
        if base not in fila.manos:
            raise ValueError(f'{base} no está en la {fila.nombre}')
        tokens[0] += '+'
    manos = expandir(' '.join(tokens))
    fuera = [m for f in FILAS for m in f.manos if m in manos and f is not fila]
    if fuera:
        raise ValueError(f'{", ".join(fuera)} no {"está" if len(fuera) == 1 else "están"} en la {fila.nombre}')
    return manos


def leer_mano_de_fila(texto, fila):
    """Una sola mano de la fila (sin palo, se pone el de la fila). None si la respuesta es «nada»."""
    t = texto.strip()
    if t.lower() in NADA:
        return None
    if re.search(r'[\s,+-]', t):
        raise ValueError('aquí va una sola mano (o «nada»)')
    mano = normalizar(_con_sufijo(t, '' if fila.clave == 'parejas' else fila.clave[1]))
    if mano not in fila.manos:
        raise ValueError(f'{mano} no está en la {fila.nombre}')
    return mano


def _con_sufijo(token, sufijo):
    if not sufijo:
        return token
    def poner(parte):
        p = parte.strip().upper().replace('10', 'T')
        return p + sufijo if re.fullmatch(r'[2-9TJQKA]{2}', p) and p[0] != p[1] else parte
    mas = token.endswith('+')
    cuerpo = token[:-1] if mas else token
    return '-'.join(poner(p) for p in cuerpo.split('-')) + ('+' if mas else '')


def tramos(manos, fila):
    """Trozos seguidos de la fila que están en el conjunto, como índices (inicio, fin)."""
    trozos, inicio = [], None
    for k, m in enumerate(fila.manos + ('',)):
        if m in manos and inicio is None:
            inicio = k
        elif m not in manos and inicio is not None:
            trozos.append((inicio, k - 1))
            inicio = None
    return trozos


def describir(manos, fila):
    piezas = []
    for i, j in tramos(manos, fila):
        if i == 0 and j > 0:
            piezas.append(fila.manos[j] + '+')
        elif i == j:
            piezas.append(fila.manos[i])
        else:
            piezas.append(f'{fila.manos[i]}-{fila.manos[j]}')
    return ' '.join(piezas) or 'nada'


def describir_conjunto(manos):
    """Manos de cualquier fila, en tramos y en el orden de las filas."""
    piezas = [describir(manos, f) for f in FILAS if manos & set(f.manos)]
    return ' '.join(piezas) or 'nada'
