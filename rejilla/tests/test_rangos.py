import json
import tempfile
import unittest
from pathlib import Path

from rejilla.rangos import RangosInvalidos, Rejilla, cargar, leer_rama, nombre_rama

RAIZ = Path(__file__).resolve().parents[2]
TODO_F = ['F' * 13] * 13


def rejilla_con(**acciones):
    """Rejilla toda de retirarse salvo las manos indicadas: rejilla_con(AA='R', AKs='C')."""
    from rejilla.manos import celda_de
    filas = [list(f) for f in TODO_F]
    for mano, letra in acciones.items():
        i, j = celda_de(mano)
        filas[i][j] = letra
    return [''.join(f) for f in filas]


def escribir(datos):
    carpeta = tempfile.mkdtemp()
    ruta = Path(carpeta) / 'ranges.json'
    ruta.write_text(json.dumps(datos), encoding='utf-8')
    return ruta


class RejillaBasica(unittest.TestCase):
    def test_accion_y_porcentaje_por_combos(self):
        r = Rejilla(rejilla_con(AA='R', AKs='R', AKo='C'))
        self.assertEqual(r.accion('AA'), 'R')
        self.assertEqual(r.accion('AKo'), 'C')
        self.assertEqual(r.accion('72o'), 'F')
        self.assertAlmostEqual(r.porcentaje('R'), 100 * 10 / 1326)
        self.assertAlmostEqual(r.porcentaje(), 100 * 22 / 1326)  # todo lo que no es retirarse

    def test_manos_de_una_accion(self):
        r = Rejilla(rejilla_con(AA='R', KK='R'))
        self.assertEqual(r.manos('R'), {'AA', 'KK'})


class Cargar(unittest.TestCase):
    def test_carga_y_oculta_lo_que_no_esta(self):
        ruta = escribir({'version': 1, '6max': {'UTG': {'RFI': rejilla_con(AA='R')}}})
        rangos = cargar(ruta)
        self.assertEqual(rangos.ramas(), [('UTG', 'RFI')])
        self.assertIsNone(rangos.rejilla('HJ', 'RFI'))

    def test_las_ramas_que_no_se_entrenan_no_salen(self):
        ruta = escribir({'version': 1, '6max': {'HJ': {'RFI': TODO_F, 'vs_4bet_UTG': TODO_F}}})
        self.assertEqual(cargar(ruta).ramas(), [('HJ', 'RFI')])

    def test_orden_por_posicion_y_tipo_de_rama(self):
        ruta = escribir({'version': 1, '6max': {
            'BTN': {'vs_3bet_SB': TODO_F, 'vs_open_UTG': TODO_F, 'RFI': TODO_F},
            'UTG': {'RFI': TODO_F}}})
        self.assertEqual(cargar(ruta).ramas(),
                         [('UTG', 'RFI'), ('BTN', 'RFI'), ('BTN', 'vs_open_UTG'), ('BTN', 'vs_3bet_SB')])

    def test_rejillas_iguales_forman_grupo(self):
        ruta = escribir({'version': 1, '6max': {'BTN': {
            'vs_open_UTG': rejilla_con(AA='R'), 'vs_open_HJ': rejilla_con(AA='R'), 'vs_open_CO': TODO_F}}})
        rangos = cargar(ruta)
        self.assertEqual(rangos.grupo('BTN', 'vs_open_UTG'), [('BTN', 'vs_open_UTG'), ('BTN', 'vs_open_HJ')])

    def test_errores_se_juntan_y_se_explican(self):
        malos = {'version': 1, '6max': {
            'BB': {'RFI': TODO_F},                       # la BB no abre
            'UTG': {'vs_open_CO': TODO_F},               # nadie habla antes que UTG
            'CO': {'vs_3bet_UTG': TODO_F,                # UTG habla antes que CO
                   'RFI': ['F' * 13] * 12,               # faltan filas
                   'vs_open_HJ': ['X' * 13] * 13},       # letra rara
            'MP': {'RFI': TODO_F}}}                      # posición que no existe en 6max
        with self.assertRaises(RangosInvalidos) as ctx:
            cargar(escribir(malos))
        texto = str(ctx.exception)
        for trozo in ('BB · RFI', 'UTG · vs_open_CO', 'CO · vs_3bet_UTG', 'CO · RFI', 'CO · vs_open_HJ', 'MP'):
            self.assertIn(trozo, texto)

    def test_mesa_que_no_esta(self):
        with self.assertRaises(RangosInvalidos):
            cargar(escribir({'version': 1, '9max': {}}), mesa='6max')


class Nombres(unittest.TestCase):
    def test_nombre_rama(self):
        self.assertEqual(nombre_rama('RFI'), 'abrir (RFI)')
        self.assertEqual(nombre_rama('vs_open_UTG'), 'contra subida de UTG')
        self.assertEqual(nombre_rama('vs_3bet_SB'), 'contra 3bet de SB')

    def test_leer_rama_acepta_formas_sueltas(self):
        self.assertEqual(leer_rama('rfi'), 'RFI')
        self.assertEqual(leer_rama('vs open co'), 'vs_open_CO')
        self.assertEqual(leer_rama('vs_3bet_bb'), 'vs_3bet_BB')
        self.assertEqual(leer_rama('3bet sb'), 'vs_3bet_SB')
        self.assertIsNone(leer_rama('lo que sea'))


class DatosReales(unittest.TestCase):
    """ranges.json del repo: lo que dice el README tiene que cumplirse."""

    @classmethod
    def setUpClass(cls):
        cls.rangos = cargar(RAIZ / 'ranges.json')

    def test_porcentajes_de_apertura_de_la_web(self):
        esperado = {'UTG': 12.4, 'HJ': 13.7, 'CO': 23.4, 'BTN': 33.0, 'SB': 46.6}
        for pos, pct in esperado.items():
            self.assertAlmostEqual(self.rangos.rejilla(pos, 'RFI').porcentaje(), pct, places=1)

    def test_cada_posicion_posterior_abre_lo_de_la_anterior(self):
        orden = ['UTG', 'HJ', 'CO', 'BTN', 'SB']
        for antes, despues in zip(orden, orden[1:]):
            a = self.rangos.rejilla(antes, 'RFI').manos('R')
            b = self.rangos.rejilla(despues, 'RFI').manos('R')
            self.assertLessEqual(a, b, f'{antes} abre {sorted(a - b)} y {despues} no')

    def test_suited_nunca_mas_flojo_que_offsuit_ni_pareja_menor_mas_agresiva(self):
        from rejilla.manos import FILAS, RANGOS
        fuerza = {'F': 0, 'C': 1, 'R': 2, 'A': 3}
        for pos, rama in self.rangos.ramas():
            r = self.rangos.rejilla(pos, rama)
            for i, a in enumerate(RANGOS):
                for b in RANGOS[i + 1:]:
                    self.assertGreaterEqual(fuerza[r.accion(a + b + 's')], fuerza[r.accion(a + b + 'o')],
                                            f'{pos} {rama} {a}{b}')
            parejas = [fuerza[r.accion(m)] for m in FILAS[0].manos]
            self.assertEqual(parejas, sorted(parejas, reverse=True), f'{pos} {rama} parejas')

    def test_ramas_de_6max(self):
        ramas = self.rangos.ramas()
        self.assertEqual(len(ramas), 35)
        self.assertNotIn(('BB', 'RFI'), ramas)
        # la web agrupa CO y BTN en el mismo nivel: sus cinco rejillas contra subida son la misma
        self.assertEqual(len(self.rangos.grupo('BTN', 'vs_open_UTG')), 5)
