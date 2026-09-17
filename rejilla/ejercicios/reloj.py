"""Dentro o fuera, a contrarreloj: posición y mano, una tecla en menos de 3 segundos.

Al acabar el bloque no se da un porcentaje suelto sino dónde caen los fallos: por zona de la
rejilla y pintados encima de la rejilla real.
"""
from collections import Counter

from ..analisis import zona
from ..leitner import clave
from ..manos import fila_de, mano_de
from ..rangos import NOMBRE_ACCION, nombre_rama
from .comun import elegir as elegir_ponderado, verbo

NOMBRE = 'Dentro o fuera'
FACTOR_FRONTERA = 3  # las manos pegadas a un cambio de acción salen el triple
TODAS = [mano_de(i, j) for i in range(13) for j in range(13)]


def cerca_de_frontera(rejilla, mano):
    fila = fila_de(mano)
    k = fila.manos.index(mano)
    vecinas = fila.manos[max(k - 1, 0):k] + fila.manos[k + 1:k + 2]
    return any(rejilla.accion(v) != rejilla.accion(mano) for v in vecinas)


def peso(ctx, pos, rama, mano):
    base = ctx.estado.prioridad(clave(ctx.mesa, pos, rama, mano), ctx.hoy)
    return base * (FACTOR_FRONTERA if cerca_de_frontera(ctx.rangos.rejilla(pos, rama), mano) else 1)


def elegir(ctx, anterior=None):
    pendiente = ctx.sesion.pendiente('reloj')
    if pendiente and pendiente != anterior:
        return pendiente
    if pendiente:
        ctx.sesion.repetir_luego('reloj', pendiente, dentro=1)
    candidatos = [(p, r, m) for p, r in ctx.ramas() for m in TODAS if (p, r, m) != anterior]
    return elegir_ponderado(ctx.rng, candidatos, [peso(ctx, *c) for c in candidatos])


def _teclas(rejilla):
    acciones = rejilla.acciones_presentes() or ['R']
    if len(acciones) == 1:
        return {'d': acciones[0], acciones[0].lower(): acciones[0], 'f': 'F'}, 'd/f'
    return {x.lower(): x for x in acciones} | {'f': 'F'}, '/'.join(x.lower() for x in acciones) + '/f'


def _nombre(rejilla, rama, letra):
    if len(rejilla.acciones_presentes()) <= 1:
        return 'fuera' if letra == 'F' else 'dentro'
    return NOMBRE_ACCION['F'] if letra == 'F' else verbo(rama, letra)


def preguntar(ctx, pos, rama, mano):
    return _preguntar(ctx, pos, rama, mano)[0]


def _preguntar(ctx, pos, rama, mano):
    rejilla = ctx.rangos.rejilla(pos, rama)
    teclas, ayuda = _teclas(rejilla)
    real = rejilla.accion(mano)
    tecla, segundos = ctx.consola.tecla(f'  {pos} · {nombre_rama(rama)} · {mano}  ({ayuda}) ', ctx.limite)
    letra = teclas.get(tecla) if tecla else None
    if tecla is None or segundos > ctx.limite:
        motivo = 'tiempo'
    elif letra is None:
        motivo = f'tecla «{tecla}» no vale'
    else:
        motivo = None if letra == real else 'no'
    if motivo:
        ctx.escribir(f'    {motivo} · era {_nombre(rejilla, rama, real)}')
    ctx.anotar(pos, rama, {mano: (motivo is None, letra)})
    ctx.sesion.anotar(NOMBRE, motivo is None)
    if motivo:
        ctx.sesion.repetir_luego('reloj', (pos, rama, mano))
    return motivo is None, motivo


def jugar(ctx, n=30, elegir=elegir):
    ctx.cabecera(NOMBRE, detalle=f'{n} manos, {ctx.limite:g} s cada una · d dentro, f fuera '
                                 '(con varias acciones: r c a f) · Esc para salir')
    resultados, anterior = [], None
    for _ in range(n):
        mano = elegir(ctx, anterior)
        _, motivo = _preguntar(ctx, *mano)
        resultados.append((*mano, motivo))
        anterior = mano
        ctx.sesion.avanzar()
    _mapa(ctx, resultados)


def _mapa(ctx, resultados):
    fallos = [r for r in resultados if r[3]]
    ctx.escribir('', f'  {NOMBRE}: {len(resultados) - len(fallos)} de {len(resultados)}')
    if not fallos:
        return
    ctx.escribir('  Dónde caen los fallos:')
    for z, k in Counter(zona(p, r, m) for p, r, m, _ in fallos).most_common(3):
        ctx.escribir(f'    {z}: {k}')
    for (p, r), _ in Counter((p, r) for p, r, _, _ in fallos).most_common(3):
        marcas = {m: '!' if motivo == 'tiempo' else '*' for pp, rr, m, motivo in fallos if (pp, rr) == (p, r)}
        ctx.escribir(*ctx.pintor.rejilla(ctx.celdas(p, r), marcas, f'{p} · {nombre_rama(r)}'))
    ctx.escribir('  * fallo · ! se acabó el tiempo')
