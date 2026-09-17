"""Informe al cerrar: marcador, tus tres zonas peores y tu porcentaje frente al de la tabla."""
from collections import defaultdict

from .analisis import ordenar_zonas, peores_zonas, porcentaje_estimado, zona
from .ejercicios.comun import pct
from .rangos import nombre_rama

ORDEN = ['Fronteras', 'Salto', 'Salto: distancia', 'Diferencial', 'Identifica', 'Dentro o fuera', 'Rejilla en blanco']


def informe(rangos, estado, sesion=None):
    lineas = []
    if sesion is not None:
        lineas += ['', 'Resumen de la sesión']
        nombres = sorted(sesion.marcador, key=lambda n: ORDEN.index(n) if n in ORDEN else len(ORDEN))
        lineas += [f'  {n}: {a} de {t}' for n, (a, t) in ((n, sesion.marcador[n]) for n in nombres)]
        if not sesion.marcador:
            lineas.append('  No has contestado nada.')
        peores = peores_zonas(sesion.intentos) or peores_zonas(sesion.intentos, minimo=1)
    else:
        peores = _peores_de_siempre(estado, rangos.mesa)

    lineas += ['', 'Tus tres zonas peores' + ('' if sesion is not None else ' (desde que empezaste)')]
    for k, (z, fallos, intentos) in enumerate(peores, 1):
        lineas.append(f'  {k}. {z}: {fallos} {"fallo" if fallos == 1 else "fallos"} de {intentos}')
    if not peores:
        lineas.append('  Ninguna zona con fallos.')

    lineas += ['', 'Lo que jugarías tú frente a la tabla (lo no contestado se da por bien)',
               f'  {"":<28}{"Tú":>9}{"Tabla":>9}{"Dif.":>7}  Contestadas']
    for pos, rama in rangos.ramas():
        respuestas = {m: r for m, r in estado.respuestas(rangos.mesa, pos, rama).items() if r}
        if rama != 'RFI' and not respuestas:
            continue
        tuyo, real, vistas = porcentaje_estimado(rangos.rejilla(pos, rama), respuestas)
        nombre = f'{pos} · abrir' if rama == 'RFI' else f'{pos} · {nombre_rama(rama)}'
        dif = f'{tuyo - real:+.1f}'.replace('.', ',')
        lineas.append(f'  {nombre:<28}{pct(tuyo):>9}{pct(real):>9}{dif:>7}  {vistas}/169')
    return lineas


def _peores_de_siempre(estado, mesa, cuantas=3, minimo=2):
    cuenta = defaultdict(lambda: [0, 0])
    for k, t in estado.tarjetas.items():
        m, pos, rama, mano = k.split('|')
        if m == mesa:
            c = cuenta[zona(pos, rama, mano)]
            c[0] += t['fallos']
            c[1] += t['vistas']
    return ordenar_zonas(cuenta, cuantas, minimo)
