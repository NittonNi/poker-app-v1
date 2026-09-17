"""Consola con guion y contexto listo para probar ejercicios sin teclado."""
import random
import tempfile
from datetime import date
from pathlib import Path

from rejilla.consola import Salir
from rejilla.ejercicios.comun import Contexto
from rejilla.leitner import Estado
from rejilla.pantalla import Pintor
from rejilla.rangos import cargar
from rejilla.sesion import Sesion

RAIZ = Path(__file__).resolve().parents[2]
HOY = date(2026, 9, 17)


class ConsolaGuion:
    """preguntar() devuelve las respuestas en orden; tecla() las teclas como (tecla, segundos)."""

    def __init__(self, respuestas=(), teclas=()):
        self.respuestas = list(respuestas)
        self.teclas = list(teclas)
        self.salida = []
        self.preguntas = []

    def escribir(self, texto=''):
        self.salida.append(texto)

    def preguntar(self, texto):
        self.preguntas.append(texto)
        if not self.respuestas:
            raise Salir()
        r = self.respuestas.pop(0)
        if r.strip().lower() == 'salir':
            raise Salir()
        return r

    def tecla(self, texto, limite):
        self.preguntas.append(texto)
        if not self.teclas:
            raise Salir()
        return self.teclas.pop(0)

    @property
    def texto(self):
        return '\n'.join(self.salida)


def contexto(respuestas=(), teclas=(), ruta_rangos=None, **filtros):
    return Contexto(
        rangos=cargar(ruta_rangos or RAIZ / 'ranges.json'),
        estado=Estado(Path(tempfile.mkdtemp()) / 'rejilla.json'),
        consola=ConsolaGuion(respuestas, teclas),
        pintor=Pintor(color=False),
        sesion=Sesion(),
        rng=random.Random(7),
        hoy=HOY,
        ancho=200,
        **filtros,
    )
