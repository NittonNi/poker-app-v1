"""Lo que comparten los ejercicios: contexto, elección ponderada y lectura de acciones."""
import random
from dataclasses import dataclass
from datetime import date

from ..leitner import Estado, clave
from ..manos import mano_de
from ..pantalla import Pintor
from ..rangos import Rangos, nombre_rama, partir_rama
from ..sesion import Sesion

PALABRAS = {
    'R': {'r', 'raise', 'subir', 'sube', 'abrir', 'abre', 'resubir', 'resube', '3bet', '4bet', 'd', 'dentro'},
    'C': {'c', 'call', 'pagar', 'paga', 'igualar', 'iguala'},
    'F': {'f', 'fold', 'retirar', 'retirarse', 'retira', 'fuera'},
    'A': {'a', 'allin', 'all-in', 'jam', 'shove'},
}


def leer_accion(texto):
    t = texto.strip().lower()
    return next((letra for letra, palabras in PALABRAS.items() if t in palabras), None)


def verbo(rama, letra):
    if letra == 'A':
        return 'va all-in'
    if letra == 'C':
        return 'paga'
    return {'RFI': 'abre', 'vs_open': 'resube (3bet)', 'vs_3bet': 'hace 4bet'}.get(partir_rama(rama)[0], 'sube')


def elegir(rng, cosas, pesos):
    if not any(p > 0 for p in pesos):
        return rng.choice(cosas)
    return rng.choices(cosas, weights=pesos)[0]


def pct(x):
    return f'{x:.1f}'.replace('.', ',') + ' %'


@dataclass
class Contexto:
    rangos: Rangos
    estado: Estado
    consola: object
    pintor: Pintor
    sesion: Sesion
    rng: random.Random
    hoy: date
    pos: str | None = None
    rama: str | None = None
    limite: float = 3.0
    ancho: int = 120

    @property
    def mesa(self):
        return self.rangos.mesa

    def ramas(self):
        ramas = self.rangos.ramas()
        if self.pos:
            ramas = [r for r in ramas if r[0] == self.pos]
        if self.rama:
            ramas = [r for r in ramas if self.rama in (r[1], partir_rama(r[1])[0])]
        return ramas

    def celdas(self, pos, rama):
        filas = self.rangos.rejilla(pos, rama).filas
        return {mano_de(i, j): filas[i][j] for i in range(13) for j in range(13)}

    def prioridad_media(self, pos, rama, manos):
        manos = list(manos)
        return sum(self.estado.prioridad(clave(self.mesa, pos, rama, m), self.hoy) for m in manos) / len(manos)

    def anotar(self, pos, rama, resultados):
        """resultados = {mano: (acierto, lo que respondió)}: Leitner, sesión y disco."""
        for mano, (acierto, respuesta) in resultados.items():
            self.estado.registrar(clave(self.mesa, pos, rama, mano), acierto, respuesta, self.hoy)
            self.sesion.intentos.append((pos, rama, mano, acierto))
        self.estado.guardar()

    def escribir(self, *lineas):
        for linea in lineas:
            self.consola.escribir(linea)

    def cabecera(self, ejercicio, pos=None, rama=None, detalle=''):
        cuerpo = ' · '.join(([f'{pos} · {nombre_rama(rama)}'] if pos else []) + ([detalle] if detalle else []))
        self.escribir('', f'[{ejercicio}] {cuerpo}'.rstrip())

    def preguntar(self, texto, lector):
        """Repite la pregunta hasta que la respuesta se entiende."""
        while True:
            respuesta = self.consola.preguntar(texto)
            try:
                return lector(respuesta)
            except ValueError as e:
                self.escribir(f'  {e}. Otra vez.')
