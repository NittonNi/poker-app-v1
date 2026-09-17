"""Diferencial entre posiciones: «¿qué manos entran al pasar de HJ a CO?»."""
from ..analisis import corregir_diferencial, diferencial
from ..manos import NADA, describir_conjunto, expandir
from .comun import elegir as elegir_ponderado

NOMBRE = 'Diferencial'
MARCAS = '  + entra y lo dijiste · ? entra y no lo dijiste · * lo dijiste y no entra'


def jugar(ctx):
    salto = elegir(ctx)
    if salto is None:
        ctx.escribir('', f'[{NOMBRE}] No hay dos aperturas seguidas definidas con estos filtros.')
        return
    preguntar(ctx, *salto)


def pesos(ctx):
    """Peso de cada salto entre aperturas seguidas: cuantas más manos cambian, más sale."""
    abren = [p for p in ctx.rangos.posiciones if ctx.rangos.rejilla(p, 'RFI')]
    resultado = {}
    for a, b in zip(abren, abren[1:]):
        if ctx.pos and ctx.pos not in (a, b):
            continue
        entran, salen = diferencial(ctx.rangos.rejilla(a, 'RFI'), ctx.rangos.rejilla(b, 'RFI'))
        cambian = entran | salen
        resultado[(a, b)] = len(cambian) * (1 + (ctx.prioridad_media(b, 'RFI', cambian) if cambian else 0))
    return resultado


def elegir(ctx):
    pendiente = ctx.sesion.pendiente('diferencial')
    if pendiente:
        return pendiente
    p = pesos(ctx)
    return elegir_ponderado(ctx.rng, list(p), list(p.values())) if p else None


def _leer(texto):
    return set() if texto.strip().lower() in NADA else expandir(texto)


def preguntar(ctx, a, b):
    antes, despues = ctx.rangos.rejilla(a, 'RFI'), ctx.rangos.rejilla(b, 'RFI')
    entran, salen = diferencial(antes, despues)
    ctx.cabecera(NOMBRE, detalle=f'de {a} a {b} · abrir (RFI)')
    dichas = ctx.preguntar('  ¿Qué manos entran? ', _leer)
    r = corregir_diferencial(dichas, entran)

    if r.acierto:
        ctx.escribir(f'  Bien: entran {len(entran)}: {describir_conjunto(entran)}')
    else:
        ctx.escribir(f'  Entran {len(entran)} y acertaste {len(r.aciertos)}.')
        if r.faltan:
            ctx.escribir(f'  Te faltan: {describir_conjunto(r.faltan)}')
        if r.sobran:
            ctx.escribir(f'  Sobran: {describir_conjunto(r.sobran)}')
    if salen:
        ctx.escribir(f'  Además salen: {describir_conjunto(salen)}')
    marcas = {**{m: '+' for m in r.aciertos}, **{m: '?' for m in r.faltan}, **{m: '*' for m in r.sobran}}
    ctx.escribir(*ctx.pintor.rejilla(ctx.celdas(b, 'RFI'), marcas, titulo=f'{b} · abrir, viniendo de {a}'))
    ctx.escribir(MARCAS)

    letra = (despues.acciones_presentes() or ['R'])[0]
    ctx.anotar(b, 'RFI', {m: (True, letra) for m in r.aciertos} | {m: (False, 'F') for m in r.faltan}
               | {m: (False, letra) for m in r.sobran if not despues.juega(m)})
    # Si dice que «entra» una mano que ya jugaba antes, lo que no sabe es la rejilla de antes.
    ya_jugaban = {m for m in r.sobran if despues.juega(m)}
    if ya_jugaban:
        ctx.anotar(a, 'RFI', {m: (False, 'F') for m in ya_jugaban})
    ctx.sesion.anotar(NOMBRE, r.acierto)
    if not r.acierto:
        ctx.sesion.repetir_luego('diferencial', (a, b))
