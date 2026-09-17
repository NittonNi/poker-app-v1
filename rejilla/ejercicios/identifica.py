"""Identifica la posición: una rejilla pintada sin nombre, y adivinas posición y rama."""
from ..manos import mano_de
from ..pantalla import lado_a_lado
from ..rangos import leer_rama, nombre_rama
from .comun import elegir as elegir_ponderado

NOMBRE = 'Identifica'


def jugar(ctx):
    preguntar(ctx, *elegir(ctx))


def elegir(ctx):
    """Una representante de cada grupo de rejillas idénticas, todas con la misma probabilidad."""
    pendiente = ctx.sesion.pendiente('identifica')
    if pendiente:
        return pendiente
    representantes = []
    for clave in ctx.ramas():
        if ctx.rangos.grupo(*clave)[0] == clave:
            representantes.append(clave)
    return elegir_ponderado(ctx.rng, representantes, [1] * len(representantes))


def _leer(ctx, texto):
    partes = texto.split(None, 1)
    if len(partes) < 2:
        raise ValueError('escribe posición y rama, por ejemplo: CO RFI')
    pos, rama = partes[0].upper(), leer_rama(partes[1])
    if pos not in ctx.rangos.posiciones or rama is None:
        raise ValueError('no entiendo esa posición o esa rama (ejemplos: CO RFI · BTN open UTG · SB 3bet BB)')
    if ctx.rangos.rejilla(pos, rama) is None:
        raise ValueError(f'{pos} · {rama} no está en ranges.json')
    return pos, rama


def preguntar(ctx, pos, rama):
    real = ctx.rangos.rejilla(pos, rama)
    ctx.escribir('', f'[{NOMBRE}] ¿De quién es esta rejilla?')
    ctx.escribir(*ctx.pintor.rejilla(ctx.celdas(pos, rama)))
    ctx.escribir('  ' + ctx.pintor.leyenda(''.join(real.acciones_presentes()) + 'F'))
    dicha = ctx.preguntar('  Posición y rama (CO RFI · BTN open UTG · SB 3bet BB): ', lambda t: _leer(ctx, t))
    grupo = ctx.rangos.grupo(pos, rama)
    acierto = dicha in grupo
    iguales = [f'{p} {nombre_rama(r)}' for p, r in grupo if (p, r) != (pos, rama)]

    if acierto:
        ctx.escribir(f'  Bien: {dicha[0]} · {nombre_rama(dicha[1])}')
    else:
        otra = ctx.rangos.rejilla(*dicha)
        distintas = {mano_de(i, j) for i in range(13) for j in range(13) if otra.filas[i][j] != real.filas[i][j]}
        ctx.escribir(f'  No. Era {pos} · {nombre_rama(rama)} · {len(distintas)} manos distintas (marcadas con *)')
        marcas = {m: '*' for m in distintas}
        ctx.escribir(*lado_a_lado([ctx.pintor.rejilla(ctx.celdas(*dicha), marcas, f'Dijiste {dicha[0]} · {nombre_rama(dicha[1])}'),
                                   ctx.pintor.rejilla(ctx.celdas(pos, rama), marcas, f'Era {pos} · {nombre_rama(rama)}')],
                                  ancho=ctx.ancho))
    if iguales:
        ctx.escribir(f'  Tiene la misma rejilla que: {", ".join(iguales)}')
    ctx.sesion.anotar(NOMBRE, acierto)
    if not acierto:
        ctx.sesion.repetir_luego('identifica', (pos, rama))
