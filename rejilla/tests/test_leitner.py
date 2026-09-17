import json
import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from rejilla.leitner import Estado, clave

HOY = date(2026, 9, 17)
K = clave('6max', 'BTN', 'RFI', 'K7s')


def estado_nuevo():
    return Estado(Path(tempfile.mkdtemp()) / 'sub' / 'rejilla.json')


class Cajas(unittest.TestCase):
    def test_un_acierto_no_basta_para_subir(self):
        e = estado_nuevo()
        e.registrar(K, True, 'R', HOY)
        t = e.tarjetas[K]
        self.assertEqual((t['caja'], t['racha'], t['proxima']), (1, 1, HOY.isoformat()))

    def test_dos_aciertos_seguidos_suben_y_espacian(self):
        e = estado_nuevo()
        e.registrar(K, True, 'R', HOY)
        e.registrar(K, True, 'R', HOY)
        t = e.tarjetas[K]
        self.assertEqual((t['caja'], t['racha'], t['proxima']), (2, 0, (HOY + timedelta(days=1)).isoformat()))

    def test_un_fallo_vuelve_a_la_primera_caja_para_hoy(self):
        e = estado_nuevo()
        for _ in range(6):
            e.registrar(K, True, 'R', HOY)
        self.assertEqual(e.tarjetas[K]['caja'], 4)
        e.registrar(K, False, 'F', HOY)
        t = e.tarjetas[K]
        self.assertEqual((t['caja'], t['racha'], t['proxima'], t['fallos'], t['vistas']),
                         (1, 0, HOY.isoformat(), 1, 7))

    def test_un_fallo_en_medio_corta_la_racha(self):
        e = estado_nuevo()
        e.registrar(K, True, 'R', HOY)
        e.registrar(K, False, 'F', HOY)
        e.registrar(K, True, 'R', HOY)
        self.assertEqual((e.tarjetas[K]['caja'], e.tarjetas[K]['racha']), (1, 1))

    def test_la_caja_5_es_el_techo(self):
        e = estado_nuevo()
        for _ in range(20):
            e.registrar(K, True, 'R', HOY)
        self.assertEqual(e.tarjetas[K]['caja'], 5)
        self.assertEqual(e.tarjetas[K]['proxima'], (HOY + timedelta(days=16)).isoformat())


class Prioridad(unittest.TestCase):
    def test_vencidas_de_caja_baja_primero_luego_nuevas_luego_el_resto(self):
        e = estado_nuevo()
        baja, alta, futura = (clave('6max', 'CO', 'RFI', m) for m in ('A9o', 'A8o', 'A7o'))
        e.registrar(baja, False, 'F', HOY)
        e.tarjetas[alta] = {'caja': 5, 'racha': 0, 'proxima': HOY.isoformat(), 'vistas': 9, 'fallos': 0,
                            'respuesta': 'R', 'ultima': HOY.isoformat()}
        e.registrar(futura, True, 'R', HOY)
        e.registrar(futura, True, 'R', HOY)  # caja 2, mañana
        nueva = clave('6max', 'CO', 'RFI', 'A6o')
        orden = sorted([futura, nueva, alta, baja], key=lambda k: -e.prioridad(k, HOY))
        self.assertEqual(orden, [baja, alta, nueva, futura])
        self.assertGreater(e.prioridad(futura, HOY), 0)


class Disco(unittest.TestCase):
    def test_se_guarda_y_se_vuelve_a_leer(self):
        e = estado_nuevo()
        e.registrar(K, False, 'F', HOY)
        e.guardar()
        otra = Estado(e.ruta)
        self.assertEqual(otra.tarjetas, e.tarjetas)

    def test_respuestas_de_una_rejilla(self):
        e = estado_nuevo()
        e.registrar(clave('6max', 'BTN', 'RFI', 'K7s'), False, 'F', HOY)
        e.registrar(clave('6max', 'BTN', 'RFI', 'AA'), True, 'R', HOY)
        e.registrar(clave('6max', 'CO', 'RFI', 'AA'), True, 'R', HOY)
        self.assertEqual(e.respuestas('6max', 'BTN', 'RFI'), {'K7s': 'F', 'AA': 'R'})

    def test_fichero_roto_no_se_pisa(self):
        carpeta = Path(tempfile.mkdtemp())
        ruta = carpeta / 'rejilla.json'
        ruta.write_text('{esto no es json', encoding='utf-8')
        e = Estado(ruta)
        self.assertEqual(e.tarjetas, {})
        self.assertIn('no se pudo leer', e.aviso)
        copias = list(carpeta.glob('rejilla.json.roto-*'))
        self.assertEqual(len(copias), 1)
        self.assertEqual(copias[0].read_text(encoding='utf-8'), '{esto no es json')

    def test_formato_en_disco(self):
        e = estado_nuevo()
        e.registrar(K, True, 'R', HOY)
        e.guardar()
        datos = json.loads(e.ruta.read_text(encoding='utf-8'))
        self.assertEqual(datos['version'], 1)
        self.assertIn(K, datos['tarjetas'])
