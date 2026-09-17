"""python -m rejilla [repaso | fronteras | diferencial | salto | reloj | identifica | blanco | ver | informe]"""
import argparse
import random
import sys
from datetime import date
from pathlib import Path

from .consola import Consola, Salir
from .ejercicios import blanco, diferencial, fronteras, identifica, reloj, salto
from .ejercicios.comun import Contexto, elegir, pct, verbo
from .informe import informe
from .leitner import Estado
from .pantalla import Pintor, activar_ansi, ancho_terminal, color_por_defecto
from .rangos import RangosInvalidos, cargar, leer_rama, nombre_rama
from .sesion import Sesion

RANGOS = Path(__file__).resolve().parent.parent / 'ranges.json'
ESTADO = Path.home() / '.poker-trainer' / 'rejilla.json'

MODULOS = {'fronteras': fronteras, 'diferencial': diferencial, 'salto': salto, 'identifica': identifica,
           'blanco': blanco}
POR_DEFECTO = {'repaso': 20, 'fronteras': 10, 'diferencial': 3, 'salto': 5, 'reloj': 20, 'identifica': 3,
               'blanco': 1}
# En el repaso mezclado, fronteras es lo que más sale y diferencial lo siguiente. La rejilla en
# blanco es larga y va aparte.
PESOS_REPASO = {'fronteras': 40, 'diferencial': 20, 'salto': 15, 'reloj': 15, 'identifica': 10}
MANOS_RELOJ_EN_REPASO = 5

MENU = [('repaso', 'Repaso mezclado'), ('fronteras', 'Fronteras'), ('diferencial', 'Diferencial entre posiciones'),
        ('salto', 'Salto suited/offsuit'), ('reloj', 'Dentro o fuera, a contrarreloj'),
        ('identifica', 'Identifica la posición'), ('blanco', 'Rejilla en blanco'), ('ver', 'Ver una rejilla'),
        ('informe', 'Informe')]


def elegir_ejercicio(rng):
    return elegir(rng, list(PESOS_REPASO), list(PESOS_REPASO.values()))


def ronda(ctx, orden, n):
    if orden == 'reloj':
        reloj.jugar(ctx, n)
        return
    for _ in range(n):
        ejercicio = elegir_ejercicio(ctx.rng) if orden == 'repaso' else orden
        if ejercicio == 'reloj':
            reloj.jugar(ctx, MANOS_RELOJ_EN_REPASO)
        else:
            MODULOS[ejercicio].jugar(ctx)
        ctx.sesion.avanzar()


def ver(ctx, pos, rama_texto=None):
    pos = pos.upper()
    if rama_texto:
        rama = leer_rama(rama_texto)
        claves = [(pos, rama)] if rama and ctx.rangos.rejilla(pos, rama) else []
    else:
        claves = [c for c in ctx.rangos.ramas() if c[0] == pos]
    if not claves:
        ctx.escribir(f'No hay ninguna rejilla para «{" ".join(filter(None, (pos, rama_texto)))}».')
        return 1
    for p, r in claves:
        rejilla = ctx.rangos.rejilla(p, r)
        ctx.escribir('', f'{p} · {nombre_rama(r)} · {pct(rejilla.porcentaje())}')
        acciones = rejilla.acciones_presentes()
        if len(acciones) > 1:
            ctx.escribir(' · '.join(f'{verbo(r, x)} {pct(rejilla.porcentaje(x))}' for x in acciones))
        ctx.escribir(*ctx.pintor.rejilla(ctx.celdas(p, r)))
    ctx.escribir(ctx.pintor.leyenda('RCAF'))
    return 0


def menu(ctx):
    while True:
        ctx.escribir('', f'Rejilla · {ctx.mesa} · {len(ctx.ramas())} rejillas')
        for k, (_, texto) in enumerate(MENU, 1):
            ctx.escribir(f'  {k} {texto}')
        ctx.escribir('  0 Salir')
        opcion = ctx.consola.preguntar('> ')
        if opcion == '0':
            return
        if not (opcion.isdigit() and 1 <= int(opcion) <= len(MENU)):
            ctx.escribir('Elige un número de la lista.')
            continue
        orden = MENU[int(opcion) - 1][0]
        if orden == 'ver':
            partes = ctx.consola.preguntar('Posición y rama (BTN RFI · BB open SB · BTN para ver todas): ').split(None, 1)
            if partes:
                ver(ctx, partes[0], partes[1] if len(partes) > 1 else None)
        elif orden == 'informe':
            ctx.escribir(*informe(ctx.rangos, ctx.estado))
        else:
            ronda(ctx, orden, POR_DEFECTO[orden])


def _argumentos(argv):
    comunes = argparse.ArgumentParser(add_help=False)
    comunes.add_argument('--rangos', type=Path, default=argparse.SUPPRESS, help='ranges.json (por defecto, el del repo)')
    comunes.add_argument('--estado', type=Path, default=argparse.SUPPRESS,
                         help=f'dónde se guarda tu progreso (por defecto {ESTADO})')
    comunes.add_argument('--mesa', choices=['6max', '9max'], default=argparse.SUPPRESS)
    comunes.add_argument('--pos', default=argparse.SUPPRESS, help='solo esta posición')
    comunes.add_argument('--rama', default=argparse.SUPPRESS, help='solo esta rama: RFI, vs_open, vs_3bet o una concreta')
    comunes.add_argument('--limite', type=float, default=argparse.SUPPRESS, help='segundos en el contrarreloj (3)')
    comunes.add_argument('--semilla', type=int, default=argparse.SUPPRESS)
    comunes.add_argument('--sin-color', action='store_true', default=argparse.SUPPRESS)

    parser = argparse.ArgumentParser(prog='python -m rejilla', parents=[comunes],
                                     description='Memorizar las rejillas 13×13 de rangos.')
    ordenes = parser.add_subparsers(dest='orden')
    for orden, texto in MENU:
        sub = ordenes.add_parser(orden, parents=[comunes], help=texto)
        if orden == 'ver':
            sub.add_argument('que_pos', metavar='POS')
            sub.add_argument('que_rama', metavar='RAMA', nargs='?')
        elif orden != 'informe':
            sub.add_argument('-n', type=int, default=None, help='cuántas preguntas (o manos en el reloj)')
    args = parser.parse_args(argv)
    for nombre, valor in (('rangos', RANGOS), ('estado', ESTADO), ('mesa', '6max'), ('pos', None), ('rama', None),
                          ('limite', 3.0), ('semilla', None), ('sin_color', False), ('n', None)):
        if not hasattr(args, nombre):
            setattr(args, nombre, valor)
    return args


def main(argv=None, consola=None, hoy=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(errors='replace')
    args = _argumentos(argv)
    real = consola is None
    consola = consola or Consola()
    color = real and not args.sin_color and color_por_defecto()
    if color:
        activar_ansi()

    try:
        rangos = cargar(args.rangos, args.mesa)
    except RangosInvalidos as e:
        consola.escribir(str(e))
        return 1
    if args.pos and args.pos.upper() not in rangos.posiciones:
        consola.escribir(f'{args.pos} no es una posición de {args.mesa} ({", ".join(rangos.posiciones)}).')
        return 2
    estado = Estado(args.estado)
    if estado.aviso:
        consola.escribir(f'Aviso: {estado.aviso}')
    ctx = Contexto(rangos, estado, consola, Pintor(color), Sesion(), random.Random(args.semilla), hoy or date.today(),
                   pos=args.pos.upper() if args.pos else None, rama=args.rama, limite=args.limite,
                   ancho=ancho_terminal() if real else 200)

    if args.orden == 'ver':
        return ver(ctx, args.que_pos, args.que_rama)
    if args.orden == 'informe':
        ctx.escribir(*informe(rangos, estado))
        return 0
    if not ctx.ramas():
        ctx.escribir('No hay ninguna rejilla con esos filtros.')
        return 1
    try:
        if args.orden:
            ronda(ctx, args.orden, args.n or POR_DEFECTO[args.orden])
        else:
            menu(ctx)
    except (Salir, KeyboardInterrupt):
        pass
    ctx.escribir(*informe(rangos, estado, ctx.sesion))
    return 0


if __name__ == '__main__':
    sys.exit(main())
