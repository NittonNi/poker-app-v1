"""Lo que pasa en una sesión: intentos por celda, marcador por ejercicio y lo que hay que repetir."""


class Sesion:
    def __init__(self):
        self.intentos = []       # (pos, rama, mano, acierto)
        self.marcador = {}       # ejercicio -> [aciertos, total]
        self.turno = 0
        self._pendientes = []    # (turno a partir del que vuelve, tipo, cosa)
        self._vistas = set()

    def anotar(self, ejercicio, acierto):
        m = self.marcador.setdefault(ejercicio, [0, 0])
        m[0] += bool(acierto)
        m[1] += 1

    def repetir_luego(self, tipo, cosa, dentro=3):
        self._pendientes.append((self.turno + dentro, tipo, cosa))

    def pendiente(self, tipo):
        for k, (turno, t, cosa) in enumerate(self._pendientes):
            if t == tipo and turno <= self.turno:
                del self._pendientes[k]
                return cosa
        return None

    def avanzar(self):
        self.turno += 1

    def primera_vez(self, cosa):
        nueva = cosa not in self._vistas
        self._vistas.add(cosa)
        return nueva
