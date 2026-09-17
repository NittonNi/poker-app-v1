"""Fronteras: «CO, fila de la K suited, ¿hasta dónde llega?». El ejercicio principal."""
from ..analisis import corregir_fila, indice_frontera
from ..manos import FILAS, describir, fila_por_clave, leer_frontera
from .comun import elegir, verbo

NOMBRE = 'Fronteras'
AYUDA = '  Una mano sola es esa y todo lo de encima (K9s). Con sueltas: ATs+ A5s-A4s. Si no entra ninguna: nada.'
PESO_FILA_VACIA = 0.1  # las filas donde no se juega nada también se aprenden, pero salen mucho menos


def jugar(ctx):
    preguntar_fila(ctx, *elegir_fila(ctx))


def elegir_fila(ctx):
    pendiente = ctx.sesion.pendiente('fronteras')
    if pendiente:
        pos, rama, clave_fila = pendiente
        return pos, rama, fila_por_clave(clave_fila)
    candidatos = [(pos, rama, fila) for pos, rama in ctx.ramas() for fila in FILAS]
    return elegir(ctx.rng, candidatos, [peso_fila(ctx, *c) for c in candidatos])


def peso_fila(ctx, pos, rama, fila):
    peso = ctx.prioridad_media(pos, rama, fila.manos)
    if not any(ctx.rangos.rejilla(pos, rama).juega(m) for m in fila.manos):
        peso *= PESO_FILA_VACIA
    return peso


def preguntar_fila(ctx, pos, rama, fila):
    rejilla = ctx.rangos.rejilla(pos, rama)
    letras = rejilla.acciones_presentes() or ['R']
    ctx.cabecera(NOMBRE, pos, rama, fila.nombre)
    if ctx.sesion.primera_vez(NOMBRE):
        ctx.escribir(AYUDA)
    while True:
        respuestas = {}
        for letra in letras:
            texto = '  ¿Hasta dónde llega? ' if len(letras) == 1 else f'  ¿Qué {verbo(rama, letra)}? '
            respuestas[letra] = ctx.preguntar(texto, lambda r: leer_frontera(r, fila))
        try:
            resultado = corregir_fila(respuestas, rejilla, fila)
            break
        except ValueError as e:
            ctx.escribir(f'  {e}. Otra vez desde el principio.')

    reales = {letra: rejilla.manos(letra) & set(fila.manos) for letra in letras}
    if len(letras) == 1:
        (letra,) = letras
        buena, tuya = describir(reales[letra], fila), describir(respuestas[letra], fila)
    else:
        buena = ' · '.join(f'{verbo(rama, x)} {describir(reales[x], fila)}' for x in letras)
        tuya = ' · '.join(f'{verbo(rama, x)} {describir(respuestas[x], fila)}' for x in letras)
    if resultado.acierto:
        ctx.escribir(f'  Bien: {buena}')
    else:
        extra = _escalones(reales[letras[0]], respuestas[letras[0]], fila) if len(letras) == 1 else ''
        ctx.escribir(f'  No. Es {buena} · tú: {tuya}{extra}')
    ctx.escribir('  ' + ctx.pintor.fila(fila, ctx.celdas(pos, rama), {m: '*' for m in resultado.fallos}))

    ctx.anotar(pos, rama, {m: (m not in resultado.fallos, resultado.dicha[m]) for m in fila.manos})
    ctx.sesion.anotar(NOMBRE, resultado.acierto)
    if not resultado.acierto:
        ctx.sesion.repetir_luego('fronteras', (pos, rama, fila.clave))


def _escalones(real, tuya, fila):
    """« · te pasas 2 escalones» cuando lo único distinto es dónde acaba el trozo de arriba."""
    kr, kt = indice_frontera(real, fila), indice_frontera(tuya, fila)
    if kr < 0 or kt < 0 or kr == kt:
        return ''
    if real - set(fila.manos[:kr + 1]) != tuya - set(fila.manos[:kt + 1]):
        return ''
    n = abs(kt - kr)
    return f' · te {"pasas" if kt > kr else "quedas corto"} {n} {"escalón" if n == 1 else "escalones"}'
