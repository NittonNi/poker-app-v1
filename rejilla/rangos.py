"""Carga ranges.json: una rejilla 13×13 por cada (posición, rama). Nada de rangos en el código."""
import json
import re
from pathlib import Path

from .manos import combos, mano_de

POSICIONES = {
    '6max': ['UTG', 'HJ', 'CO', 'BTN', 'SB', 'BB'],
    '9max': ['UTG', 'UTG+1', 'UTG+2', 'LJ', 'HJ', 'CO', 'BTN', 'SB', 'BB'],
}
LETRAS = 'RCFA'
NOMBRE_ACCION = {'R': 'subir', 'C': 'pagar', 'F': 'retirarse', 'A': 'all-in'}
TIPOS_QUE_SE_ENTRENAN = ('RFI', 'vs_open', 'vs_3bet')
_ORDEN_TIPO = {'RFI': 0, 'vs_open': 1, 'vs_3bet': 2, 'vs_4bet': 3}
_RAMA = re.compile(r'^(RFI)$|^(vs_open|vs_3bet|vs_4bet)_(.+)$')


class RangosInvalidos(Exception):
    def __init__(self, ruta, problemas):
        self.problemas = problemas
        super().__init__(f'{ruta} tiene {len(problemas)} problema(s):\n' + '\n'.join(f'  - {p}' for p in problemas))


class Rejilla:
    def __init__(self, filas):
        self.filas = tuple(filas)

    def accion(self, mano):
        from .manos import celda_de
        i, j = celda_de(mano)
        return self.filas[i][j]

    def juega(self, mano):
        return self.accion(mano) != 'F'

    def manos(self, letras):
        return {mano_de(i, j) for i in range(13) for j in range(13) if self.filas[i][j] in letras}

    def porcentaje(self, letras='RCA'):
        return 100 * sum(combos(m) for m in self.manos(letras)) / 1326

    def acciones_presentes(self):
        """Las acciones distintas de retirarse que usa la rejilla, en orden R, C, A."""
        usadas = set(''.join(self.filas))
        return [x for x in 'RCA' if x in usadas]

    def __eq__(self, otra):
        return isinstance(otra, Rejilla) and self.filas == otra.filas

    def __hash__(self):
        return hash(self.filas)


def partir_rama(rama):
    """'vs_open_CO' -> ('vs_open', 'CO'); 'RFI' -> ('RFI', None); lo que no encaja -> (None, None)."""
    x = _RAMA.match(rama)
    if not x:
        return None, None
    return ('RFI', None) if x[1] else (x[2], x[3])


def nombre_rama(rama):
    tipo, rival = partir_rama(rama)
    return {'RFI': 'abrir (RFI)', 'vs_open': f'contra subida de {rival}', 'vs_3bet': f'contra 3bet de {rival}',
            'vs_4bet': f'contra 4bet de {rival}'}.get(tipo, rama)


def leer_rama(texto):
    t = re.sub(r'[\s_-]+', ' ', texto.strip().lower())
    if t in ('rfi', 'abrir', 'open'):
        return 'RFI'
    x = re.fullmatch(r'(?:vs ?)?(open|3 ?bet|4 ?bet) (\S+)', t)
    if not x:
        return None
    tipo = {'open': 'vs_open', '3bet': 'vs_3bet', '3 bet': 'vs_3bet', '4bet': 'vs_4bet', '4 bet': 'vs_4bet'}[x[1]]
    return f'{tipo}_{x[2].upper()}'


class Rangos:
    def __init__(self, mesa, rejillas):
        self.mesa = mesa
        self.posiciones = POSICIONES[mesa]
        self._rejillas = rejillas  # {(pos, rama): Rejilla}

    def rejilla(self, pos, rama):
        return self._rejillas.get((pos, rama))

    def ramas(self, tipos=TIPOS_QUE_SE_ENTRENAN):
        def orden(clave):
            pos, rama = clave
            tipo, rival = partir_rama(rama)
            return (self.posiciones.index(pos), _ORDEN_TIPO[tipo], self.posiciones.index(rival) if rival else -1)
        return sorted((k for k in self._rejillas if partir_rama(k[1])[0] in tipos), key=orden)

    def grupo(self, pos, rama):
        """Todas las (posición, rama) que tienen exactamente la misma rejilla."""
        objetivo = self.rejilla(pos, rama)
        return [k for k in self.ramas() if self._rejillas[k] == objetivo]


def cargar(ruta, mesa='6max'):
    try:
        datos = json.loads(Path(ruta).read_text(encoding='utf-8'))
    except (OSError, json.JSONDecodeError) as e:
        raise RangosInvalidos(ruta, [f'no se puede leer: {e}'])
    problemas = []
    if datos.get('version') != 1:
        problemas.append(f'version tiene que ser 1 y es {datos.get("version")!r}')
    if mesa not in datos:
        raise RangosInvalidos(ruta, problemas + [f'no hay rangos para la mesa {mesa}'])
    posiciones = POSICIONES[mesa]
    rejillas = {}
    for pos, ramas in datos[mesa].items():
        if pos not in posiciones:
            problemas.append(f'{pos}: no es una posición de {mesa} ({", ".join(posiciones)})')
            continue
        for rama, filas in ramas.items():
            problema = _problema_rama(pos, rama, posiciones) or _problema_filas(filas)
            if problema:
                problemas.append(f'{pos} · {rama}: {problema}')
            else:
                rejillas[(pos, rama)] = Rejilla(filas)
    if problemas:
        raise RangosInvalidos(ruta, problemas)
    return Rangos(mesa, rejillas)


def _problema_rama(pos, rama, posiciones):
    tipo, rival = partir_rama(rama)
    yo = posiciones.index(pos)
    if tipo is None:
        return 'nombre de rama desconocido (RFI, vs_open_X, vs_3bet_X o vs_4bet_X)'
    if tipo == 'RFI':
        return 'la ciega grande no puede abrir' if pos == 'BB' else None
    if rival not in posiciones:
        return f'{rival} no es una posición'
    el = posiciones.index(rival)
    if tipo in ('vs_open', 'vs_4bet') and not el < yo:
        return f'{rival} no habla antes que {pos}, así que no puede haber subido primero'
    if tipo == 'vs_3bet' and (pos == 'BB' or not el > yo):
        return f'para resubir a {pos}, {rival} tiene que hablar después'
    return None


def _problema_filas(filas):
    if not isinstance(filas, list) or len(filas) != 13:
        return 'tiene que tener 13 filas'
    for k, fila in enumerate(filas, 1):
        if not isinstance(fila, str) or len(fila) != 13:
            return f'la fila {k} tiene que tener 13 letras'
        raras = set(fila) - set(LETRAS)
        if raras:
            return f'la fila {k} tiene letras que no valen ({"".join(sorted(raras))}); solo R, C, F o A'
    return None
