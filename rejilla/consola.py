"""Entrada y salida de verdad. Los ejercicios solo hablan con esto, así se prueban con un guion."""
import os
import sys
import time


class Salir(Exception):
    """El usuario quiere acabar: «salir», Ctrl+C, Esc en el reloj o fin de la entrada."""


class Consola:
    def __init__(self, teclas_directas=None):
        if teclas_directas is None:
            teclas_directas = os.name == 'nt' and sys.stdin.isatty()
        self.teclas_directas = teclas_directas

    def escribir(self, texto=''):
        print(texto)

    def preguntar(self, texto):
        try:
            respuesta = input(texto).strip()
        except (EOFError, KeyboardInterrupt):
            print()
            raise Salir()
        if respuesta.lower() == 'salir':
            raise Salir()
        return respuesta

    def tecla(self, texto, limite):
        """(tecla en minúscula o None si se acaba el tiempo, segundos que tardó)."""
        if not self.teclas_directas:
            inicio = time.monotonic()
            respuesta = self.preguntar(texto)
            return respuesta.lower() or None, time.monotonic() - inicio
        import msvcrt
        sys.stdout.write(texto)
        sys.stdout.flush()
        while msvcrt.kbhit():  # lo que se pulsó antes de la pregunta no cuenta
            msvcrt.getwch()
        inicio = time.monotonic()
        while True:
            if msvcrt.kbhit():
                caracter = msvcrt.getwch()
                segundos = time.monotonic() - inicio
                if caracter in ('\x03', '\x1b'):
                    print()
                    raise Salir()
                print(caracter)
                return caracter.lower(), segundos
            if time.monotonic() - inicio > limite:
                print()
                return None, time.monotonic() - inicio
            time.sleep(0.01)
