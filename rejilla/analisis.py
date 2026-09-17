"""Corrección de cada ejercicio, sin nada de pantalla ni de disco."""
from collections import defaultdict
from dataclasses import dataclass, field

from .manos import combos, describir, fila_de, FILAS, tramos
from .rangos import nombre_rama

JUEGA = 'RCA'


@dataclass
class ResultadoFila:
    dicha: dict            # mano -> letra que se dijo (F si no salió en ninguna respuesta)
    real: dict             # mano -> letra de la tabla
    fallos: set = field(default_factory=set)

    @property
    def acierto(self):
        return not self.fallos


def corregir_fila(respuestas, rejilla, fila):
    """respuestas = {letra: conjunto de manos de la fila}."""
    dicha = {m: 'F' for m in fila.manos}
    for letra, manos in respuestas.items():
        for m in manos:
            if dicha[m] != 'F':
                raise ValueError(f'{m} está en dos respuestas a la vez')
            dicha[m] = letra
    real = {m: rejilla.accion(m) for m in fila.manos}
    return ResultadoFila(dicha, real, {m for m in fila.manos if dicha[m] != real[m]})


def indice_frontera(manos, fila):
    """Índice de la última mano del trozo que empieza arriba; -1 si la de arriba no está."""
    trozos = tramos(manos, fila)
    return trozos[0][1] if trozos and trozos[0][0] == 0 else -1


@dataclass
class ResultadoSalto:
    real_suited: str | None
    real_offsuit: str | None
    acierto_suited: bool
    acierto_offsuit: bool
    distancia_real: int
    distancia_tuya: int
    sueltas_suited: str
    sueltas_offsuit: str
    celdas: dict            # mano -> ¿dijo que juega? (solo las que decide la respuesta)
    fallos: set

    @property
    def acierto_distancia(self):
        return self.distancia_real == self.distancia_tuya

    @property
    def acierto(self):
        return self.acierto_suited and self.acierto_offsuit


def corregir_salto(tuya_suited, tuya_offsuit, rejilla, rango):
    """Última suited y última offsuit que juegan en la fila de `rango` (A, K, ...). None = ninguna."""
    lados = {}
    celdas, fallos = {}, set()
    for sufijo, tuya in (('s', tuya_suited), ('o', tuya_offsuit)):
        fila = _fila(rango, sufijo)
        juega = {m for m in fila.manos if rejilla.juega(m)}
        k_real = indice_frontera(juega, fila)
        k_tuyo = fila.manos.index(tuya) if tuya else -1
        superior = set(fila.manos[:k_real + 1])
        for k in range(0, min(max(k_real, k_tuyo) + 2, len(fila.manos))):
            m = fila.manos[k]
            if m in juega and m not in superior:
                continue  # suelta: esta pregunta no la cubre
            celdas[m] = k <= k_tuyo
            if celdas[m] != (m in juega):
                fallos.add(m)
        sueltas = describir(juega - superior, fila) if juega - superior else ''
        lados[sufijo] = (fila.manos[k_real] if k_real >= 0 else None, k_real, k_tuyo, sueltas)
    (rs, ks, ts, ss), (ro, ko, to, so) = lados['s'], lados['o']
    return ResultadoSalto(rs, ro, ks == ts, ko == to, ks - ko, ts - to, ss, so, celdas, fallos)


def _fila(rango, sufijo):
    return next(f for f in FILAS if f.clave == rango + sufijo)


@dataclass
class ResultadoDiferencial:
    aciertos: set
    faltan: set
    sobran: set

    @property
    def acierto(self):
        return not self.faltan and not self.sobran


def diferencial(antes, despues):
    """(las que entran, las que salen) al pasar de una rejilla a otra."""
    a, b = antes.manos(JUEGA), despues.manos(JUEGA)
    return b - a, a - b


def corregir_diferencial(dichas, entran):
    return ResultadoDiferencial(dichas & entran, entran - dichas, dichas - entran)


def zona(pos, rama, mano):
    return f'{pos} · {nombre_rama(rama)} · {fila_de(mano).nombre}'


def peores_zonas(intentos, cuantas=3, minimo=2):
    """intentos = [(pos, rama, mano, acierto)] -> [(zona, fallos, intentos)] de peor a mejor."""
    cuenta = defaultdict(lambda: [0, 0])
    for pos, rama, mano, acierto in intentos:
        c = cuenta[zona(pos, rama, mano)]
        c[0] += not acierto
        c[1] += 1
    return ordenar_zonas(cuenta, cuantas, minimo)


def ordenar_zonas(cuenta, cuantas=3, minimo=2):
    """cuenta = {zona: [fallos, intentos]} -> las peores por tasa de fallo, y a igualdad, por fallos."""
    malas = [(z, f, n) for z, (f, n) in cuenta.items() if n >= minimo and f]
    malas.sort(key=lambda x: (-x[1] / x[2], -x[1]))
    return malas[:cuantas]


def porcentaje_estimado(real, respuestas):
    """(% que juega tu versión, % real, celdas contestadas). Lo no contestado se da por bien."""
    juega = real.manos(JUEGA)
    for mano, letra in respuestas.items():
        (juega.add if letra in JUEGA else juega.discard)(mano)
    return 100 * sum(combos(m) for m in juega) / 1326, real.porcentaje(JUEGA), len(respuestas)
