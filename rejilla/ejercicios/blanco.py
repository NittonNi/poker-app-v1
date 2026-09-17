"""Rejilla en blanco: la rellenas de memoria y al final se compara con la real."""
from ..manos import expandir, mano_de
from ..pantalla import lado_a_lado
from ..rangos import NOMBRE_ACCION, Rejilla, partir_rama
from .comun import elegir as elegir_ponderado, leer_accion, pct, verbo

NOMBRE = 'Rejilla en blanco'
AYUDA = ('  Escribe tramos y acción: 22+ r · KQs-K9s raise · AKo c. También: ver · borrar K9s · fin.\n'
         '  Lo que no rellenes cuenta como retirarse.')
TODAS = [mano_de(i, j) for i in range(13) for j in range(13)]


def jugar(ctx):
    preguntar(ctx, *elegir(ctx))


def elegir(ctx):
    ramas = ctx.ramas()
    return elegir_ponderado(ctx.rng, ramas, [ctx.prioridad_media(p, r, TODAS) for p, r in ramas])


def _leer_linea(texto):
    """'22+ r' o 'r 22+' -> (conjunto, letra)."""
    trozos = texto.split()
    if len(trozos) >= 2 and leer_accion(trozos[-1]):
        return expandir(' '.join(trozos[:-1])), leer_accion(trozos[-1])
    if len(trozos) >= 2 and leer_accion(trozos[0]):
        return expandir(' '.join(trozos[1:])), leer_accion(trozos[0])
    raise ValueError('falta la acción al principio o al final (r, c, f o a)')


def preguntar(ctx, pos, rama):
    real = ctx.rangos.rejilla(pos, rama)
    tuyas = {m: None for m in TODAS}
    ctx.cabecera(NOMBRE, pos, rama)
    ctx.escribir(AYUDA)
    while True:
        linea = ctx.consola.preguntar('  > ')
        orden = linea.strip().lower()
        if orden == 'fin':
            break
        if orden == 'ver':
            ctx.escribir(*ctx.pintor.rejilla(tuyas))
            continue
        try:
            if orden.startswith('borrar '):
                manos = expandir(linea.strip()[7:])
                for m in manos:
                    tuyas[m] = None
                ctx.escribir(f'  {_manos(len(manos))} {"borrada" if len(manos) == 1 else "borradas"}')
            else:
                manos, letra = _leer_linea(linea)
                for m in manos:
                    tuyas[m] = letra
                ctx.escribir(f'  {_manos(len(manos))} → {NOMBRE_ACCION[letra]}')
        except ValueError as e:
            ctx.escribir(f'  {e}')

    dichas = {m: letra or 'F' for m, letra in tuyas.items()}
    fallos = {m for m in TODAS if dichas[m] != real.accion(m)}
    marcas = {m: '*' for m in fallos}
    ctx.escribir(*lado_a_lado([ctx.pintor.rejilla(dichas, marcas, 'Tu rejilla (* = fallo)'),
                               ctx.pintor.rejilla(ctx.celdas(pos, rama), marcas, 'La correcta')], ancho=ctx.ancho))
    ctx.escribir('  ' + ctx.pintor.leyenda(''.join(real.acciones_presentes()) + ''.join(set(dichas.values())) + 'F'))
    aciertos = 169 - len(fallos)
    ctx.escribir(f'  Aciertos: {aciertos} de 169 ({pct(100 * aciertos / 169)})')
    tu_rejilla = _rejilla(dichas)
    etiqueta = 'Abre' if partir_rama(rama)[0] == 'RFI' else 'Juega'
    ctx.escribir(f'  {etiqueta} tu versión: {pct(tu_rejilla.porcentaje())} · la tabla: {pct(real.porcentaje())}')
    acciones = real.acciones_presentes()
    if len(acciones) > 1:
        for letra in acciones:
            ctx.escribir(f'    {verbo(rama, letra)}: tú {pct(tu_rejilla.porcentaje(letra))}'
                         f' · tabla {pct(real.porcentaje(letra))}')

    ctx.anotar(pos, rama, {m: (m not in fallos, dichas[m]) for m in TODAS})
    ctx.sesion.anotar(NOMBRE, not fallos)


def _manos(n):
    return f'{n} {"mano" if n == 1 else "manos"}'


def _rejilla(dichas):
    return Rejilla([''.join(dichas[mano_de(i, j)] for j in range(13)) for i in range(13)])
