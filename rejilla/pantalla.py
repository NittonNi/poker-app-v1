"""Rejilla en ASCII con color por acción. Sin color, la acción va como letra."""
import os
import re
import shutil
import sys
from itertools import zip_longest

from .manos import mano_de
from .rangos import NOMBRE_ACCION

_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')
FIN = '\x1b[0m'
# Colores de la paleta de 16 del terminal. Contraste calculado con la paleta Campbell de Windows
# Terminal: blanco (#F2F2F2) sobre rojo (#C50F1F) 5,42:1; negro (#0C0C0C) sobre verde (#13A10E)
# 5,71:1; blanco sobre magenta (#881798) 7,15:1; gris claro (#CCCCCC) sobre el fondo 12,18:1.
# El gris oscuro (#767676, 4,31:1) solo marca celdas aún sin rellenar.
ESTILO = {'R': '\x1b[97;41m', 'C': '\x1b[30;42m', 'A': '\x1b[97;45m', 'F': '\x1b[37m', None: '\x1b[90m'}
LETRA_SIN_COLOR = {'R': 'R', 'C': 'C', 'A': 'A', 'F': '.', None: '·'}


def visible(texto):
    return len(_ESCAPE.sub('', texto))


def color_por_defecto():
    return sys.stdout.isatty() and 'NO_COLOR' not in os.environ


def activar_ansi():
    """En la consola clásica de Windows los colores ANSI hay que encenderlos."""
    if os.name != 'nt':
        return
    try:
        import ctypes
        k32 = ctypes.windll.kernel32
        h = k32.GetStdHandle(-11)
        modo = ctypes.c_uint32()
        if k32.GetConsoleMode(h, ctypes.byref(modo)):
            k32.SetConsoleMode(h, modo.value | 0x0004)
    except (OSError, AttributeError):
        pass


def ancho_terminal():
    return shutil.get_terminal_size((120, 40)).columns


class Pintor:
    def __init__(self, color):
        self.color = color

    def celda(self, mano, letra, marca=' '):
        if self.color:
            if marca == ' ':
                return f'{ESTILO[letra]}{mano:<3} {FIN}'
            # Celda marcada: mano subrayada y la marca en negrita; sobre fondo oscuro, en amarillo.
            color_marca = '\x1b[1;93m' if letra in ('F', None) else '\x1b[1m'
            return f'{ESTILO[letra]}\x1b[4m{mano:<3}\x1b[24m{color_marca}{marca}{FIN}'
        return f'{mano:<3}{LETRA_SIN_COLOR[letra]}{marca}'

    def rejilla(self, celdas, marcas=None, titulo=''):
        """celdas = {mano: letra o None}; marcas = {mano: carácter} para señalar fallos, añadidas..."""
        marcas = marcas or {}
        lineas = [titulo] if titulo else []
        for i in range(13):
            lineas.append(''.join(self.celda(m, celdas.get(m), marcas.get(m, ' '))
                                  for m in (mano_de(i, j) for j in range(13))))
        return lineas

    def fila(self, fila, celdas, marcas=None):
        marcas = marcas or {}
        return ''.join(self.celda(m, celdas.get(m), marcas.get(m, ' ')) for m in fila.manos)

    def leyenda(self, letras):
        piezas = []
        for letra in 'RCAF':
            if letra in letras:
                muestra = f'{ESTILO[letra]} {letra} {FIN}' if self.color else letra
                piezas.append(f'{muestra} {NOMBRE_ACCION[letra]}')
        return ' · '.join(piezas)


def lado_a_lado(bloques, ancho=None, separacion=4):
    ancho = ancho or ancho_terminal()
    anchos = [max((visible(l) for l in b), default=0) for b in bloques]
    if sum(anchos) + separacion * (len(bloques) - 1) > ancho:
        salida = []
        for k, b in enumerate(bloques):
            salida += ([''] if k else []) + list(b)
        return salida
    salida = []
    for trozos in zip_longest(*bloques, fillvalue=''):
        piezas = [t + ' ' * (anchos[k] - visible(t)) for k, t in enumerate(trozos[:-1])] + [trozos[-1]]
        salida.append((' ' * separacion).join(piezas).rstrip())
    return salida
