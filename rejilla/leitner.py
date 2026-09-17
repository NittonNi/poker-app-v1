"""Repetición espaciada con cajas de Leitner sobre (mano, posición, rama).

- Fallo: vuelve a la caja 1 y toca hoy mismo.
- Acierto: suma racha; con dos seguidos sube de caja y se espacia.
- Caja 1 toca el mismo día; 2, al día siguiente; 3, a los 3 días; 4, a los 7; 5, a los 16.
"""
import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

INTERVALOS = {1: 0, 2: 1, 3: 3, 4: 7, 5: 16}
ACIERTOS_PARA_SUBIR = 2


def clave(mesa, pos, rama, mano):
    return f'{mesa}|{pos}|{rama}|{mano}'


class Estado:
    def __init__(self, ruta):
        self.ruta = Path(ruta)
        self.tarjetas = {}
        self.aviso = ''
        if self.ruta.exists():
            texto = self.ruta.read_text(encoding='utf-8')
            try:
                self.tarjetas = json.loads(texto)['tarjetas']
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                copia = self.ruta.with_name(f'{self.ruta.name}.roto-{datetime.now():%Y%m%d-%H%M%S}')
                self.ruta.rename(copia)
                self.aviso = f'no se pudo leer {self.ruta} ({e}); lo he guardado como {copia.name} y empiezo de cero'

    def registrar(self, k, acierto, respuesta, hoy):
        t = self.tarjetas.setdefault(k, {'caja': 1, 'racha': 0, 'vistas': 0, 'fallos': 0})
        t['vistas'] += 1
        if acierto:
            t['racha'] += 1
            if t['racha'] >= ACIERTOS_PARA_SUBIR:
                t['caja'] = min(t['caja'] + 1, max(INTERVALOS))
                t['racha'] = 0
        else:
            t['fallos'] += 1
            t['caja'], t['racha'] = 1, 0
        t['proxima'] = (hoy + timedelta(days=INTERVALOS[t['caja']])).isoformat()
        t['respuesta'] = respuesta
        t['ultima'] = hoy.isoformat()

    def prioridad(self, k, hoy):
        """Más alto = antes. Vencidas (más cuanto más baja la caja) > nuevas > el resto."""
        t = self.tarjetas.get(k)
        if t is None:
            return 3
        if date.fromisoformat(t['proxima']) <= hoy:
            return 10 - t['caja']
        return 0.2

    def respuestas(self, mesa, pos, rama):
        prefijo = f'{mesa}|{pos}|{rama}|'
        return {k[len(prefijo):]: t['respuesta'] for k, t in self.tarjetas.items() if k.startswith(prefijo)}

    def guardar(self):
        self.ruta.parent.mkdir(parents=True, exist_ok=True)
        temporal = self.ruta.with_name(self.ruta.name + '.tmp')
        temporal.write_text(json.dumps({'version': 1, 'tarjetas': self.tarjetas}, ensure_ascii=False),
                            encoding='utf-8')
        os.replace(temporal, self.ruta)
