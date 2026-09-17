import unittest

from rejilla.manos import fila_de
from rejilla.pantalla import Pintor, lado_a_lado, visible
from rejilla.rangos import Rejilla
from rejilla.tests.test_rangos import rejilla_con

REJILLA = Rejilla(rejilla_con(AA='R', AKs='C', AKo='A'))


def celdas(rejilla):
    from rejilla.manos import mano_de
    return {mano_de(i, j): rejilla.filas[i][j] for i in range(13) for j in range(13)}


class Rejillas(unittest.TestCase):
    def test_sin_color_cada_celda_lleva_mano_letra_y_marca(self):
        lineas = Pintor(color=False).rejilla(celdas(REJILLA), marcas={'AKs': '*'})
        self.assertEqual(len(lineas), 13)
        self.assertTrue(lineas[0].startswith('AA R AKsC*AQs. '))
        self.assertIn('AKoA ', lineas[1])
        self.assertEqual({visible(l) for l in lineas}, {65})

    def test_con_color_es_mas_estrecha_y_lleva_escapes(self):
        lineas = Pintor(color=True).rejilla(celdas(REJILLA))
        self.assertEqual({visible(l) for l in lineas}, {52})
        self.assertIn('\x1b[', lineas[0])

    def test_celdas_sin_rellenar(self):
        vacia = {m: None for m in celdas(REJILLA)}
        linea = Pintor(color=False).rejilla(vacia)[0]
        self.assertTrue(linea.startswith('AA · AKs· '))

    def test_titulo_encima(self):
        lineas = Pintor(color=False).rejilla(celdas(REJILLA), titulo='BTN · abrir')
        self.assertEqual(lineas[0], 'BTN · abrir')
        self.assertEqual(len(lineas), 14)

    def test_una_fila_suelta(self):
        linea = Pintor(color=False).fila(fila_de('AKs'), celdas(REJILLA), marcas={'AQs': '*'})
        self.assertTrue(linea.startswith('AKsC AQs.*AJs. '))

    def test_leyenda_solo_con_las_acciones_que_salen(self):
        texto = Pintor(color=False).leyenda('RF')
        self.assertIn('subir', texto)
        self.assertNotIn('pagar', texto)


class Juntar(unittest.TestCase):
    def test_lado_a_lado_si_cabe(self):
        a, b = ['aaa', 'a'], ['bb', 'bb', 'bb']
        self.assertEqual(lado_a_lado([a, b], ancho=20, separacion=2), ['aaa  bb', 'a    bb', '     bb'])

    def test_una_debajo_de_otra_si_no_cabe(self):
        self.assertEqual(lado_a_lado([['aaaa'], ['bbbb']], ancho=6, separacion=2), ['aaaa', '', 'bbbb'])

    def test_el_ancho_no_cuenta_los_escapes_de_color(self):
        a = ['\x1b[41mAA\x1b[0m']
        self.assertEqual(lado_a_lado([a, ['KK']], ancho=6, separacion=1), ['\x1b[41mAA\x1b[0m KK'])
