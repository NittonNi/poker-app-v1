"""El salto suited/offsuit: «CO, fila de la A: ¿última suited y última offsuit?», y cuántos escalones las separan."""
from ..analisis import corregir_salto
from ..manos import RANGOS, fila_por_clave, leer_mano_de_fila
from .comun import elegir as elegir_ponderado

NOMBRE = 'Salto'


def jugar(ctx):
    preguntar(ctx, *elegir(ctx))


def elegir(ctx):
    pendiente = ctx.sesion.pendiente('salto')
    if pendiente:
        return pendiente
    candidatos, pesos = [], []
    for pos, rama in ctx.ramas():
        rejilla = ctx.rangos.rejilla(pos, rama)
        for rango in RANGOS[:-1]:
            manos = fila_por_clave(rango + 's').manos + fila_por_clave(rango + 'o').manos
            if any(rejilla.juega(m) for m in manos):
                candidatos.append((pos, rama, rango))
                pesos.append(ctx.prioridad_media(pos, rama, manos))
    return elegir_ponderado(ctx.rng, candidatos, pesos)


def preguntar(ctx, pos, rama, rango):
    rejilla = ctx.rangos.rejilla(pos, rama)
    suited, offsuit = fila_por_clave(rango + 's'), fila_por_clave(rango + 'o')
    ctx.cabecera(NOMBRE, pos, rama, f'fila de la {rango}')
    tuya_s = ctx.preguntar('  ¿Última suited que juega? ', lambda r: leer_mano_de_fila(r, suited))
    tuya_o = ctx.preguntar('  ¿Y la última offsuit? ', lambda r: leer_mano_de_fila(r, offsuit))
    r = corregir_salto(tuya_s, tuya_o, rejilla, rango)

    def escalones(n):
        return f'{n} {"escalón" if abs(n) == 1 else "escalones"}'

    if r.acierto and r.acierto_distancia:
        ctx.escribir(f'  Bien: {r.real_suited or "nada"} y {r.real_offsuit or "nada"} · salto de {escalones(r.distancia_real)}')
    else:
        partes = []
        for lado, real, tuya, ok in (('suited', r.real_suited, tuya_s, r.acierto_suited),
                                     ('offsuit', r.real_offsuit, tuya_o, r.acierto_offsuit)):
            partes.append(f'{lado} {real or "nada"} bien' if ok else f'{lado} es {real or "nada"} (tú {tuya or "nada"})')
        partes.append(f'salto de {escalones(r.distancia_real)} bien' if r.acierto_distancia
                      else f'salto de {escalones(r.distancia_real)}, tú {r.distancia_tuya}')
        ctx.escribir('  No. ' + ' · '.join(partes))
    for lado, sueltas in (('suited', r.sueltas_suited), ('offsuit', r.sueltas_offsuit)):
        if sueltas:
            ctx.escribir(f'  Además entran sueltas en {lado}: {sueltas}')
    celdas = ctx.celdas(pos, rama)
    marcas = {m: '*' for m in r.fallos}
    ctx.escribir('  ' + ctx.pintor.fila(suited, celdas, marcas), '  ' + ctx.pintor.fila(offsuit, celdas, marcas))

    acciones = rejilla.acciones_presentes()
    if len(acciones) == 1:  # con varias acciones «juega» no dice cuál, así que no cuenta para Leitner
        ctx.anotar(pos, rama, {m: (m not in r.fallos, acciones[0] if dice else 'F') for m, dice in r.celdas.items()})
    ctx.sesion.anotar(NOMBRE, r.acierto)
    ctx.sesion.anotar(f'{NOMBRE}: distancia', r.acierto_distancia)
    if not (r.acierto and r.acierto_distancia):
        ctx.sesion.repetir_luego('salto', (pos, rama, rango))
