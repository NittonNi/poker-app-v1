import unittest

from rejilla.ejercicios import reloj
from rejilla.leitner import clave
from rejilla.tests.utiles import contexto


class UnaMano(unittest.TestCase):
    def test_dentro_a_tiempo(self):
        ctx = contexto(teclas=[('d', 1.0)])
        self.assertTrue(reloj.preguntar(ctx, 'UTG', 'RFI', 'AA'))
        self.assertEqual(ctx.estado.tarjetas[clave('6max', 'UTG', 'RFI', 'AA')]['respuesta'], 'R')

    def test_tecla_equivocada(self):
        ctx = contexto(teclas=[('f', 0.5)])
        self.assertFalse(reloj.preguntar(ctx, 'UTG', 'RFI', 'AA'))
        self.assertIn('era dentro', ctx.consola.texto)

    def test_sin_tecla_se_acaba_el_tiempo(self):
        ctx = contexto(teclas=[(None, 3.0)])
        self.assertFalse(reloj.preguntar(ctx, 'UTG', 'RFI', 'AA'))
        self.assertIn('tiempo', ctx.consola.texto)
        self.assertIsNone(ctx.estado.tarjetas[clave('6max', 'UTG', 'RFI', 'AA')]['respuesta'])

    def test_bien_pero_tarde_es_fallo(self):
        ctx = contexto(teclas=[('d', 3.4)])
        self.assertFalse(reloj.preguntar(ctx, 'UTG', 'RFI', 'AA'))
        self.assertIn('tiempo', ctx.consola.texto)

    def test_varias_acciones_con_su_tecla(self):
        ctx = contexto(teclas=[('r', 1.0), ('c', 1.0)])
        self.assertTrue(reloj.preguntar(ctx, 'BTN', 'vs_open_UTG', 'AQs'))
        self.assertFalse(reloj.preguntar(ctx, 'BTN', 'vs_open_UTG', 'AQs'))
        self.assertIn('era resube (3bet)', ctx.consola.texto)

    def test_tecla_que_no_vale_es_fallo(self):
        ctx = contexto(teclas=[('x', 0.4)])
        self.assertFalse(reloj.preguntar(ctx, 'UTG', 'RFI', 'AA'))
        self.assertIn('tecla', ctx.consola.texto)


class Bloque(unittest.TestCase):
    def test_mapa_de_fallos_al_final(self):
        ctx = contexto(teclas=[('f', 1.0), ('d', 1.0), (None, 3.0)], pos='UTG', rama='RFI')
        manos = iter(['KTs', 'AA', 'K9s'])
        reloj.jugar(ctx, 3, elegir=lambda ctx, anterior: ('UTG', 'RFI', next(manos)))
        texto = ctx.consola.texto
        self.assertEqual(ctx.sesion.marcador['Dentro o fuera'], [1, 3])
        self.assertIn('Dentro o fuera: 1 de 3', texto)
        self.assertIn('KTsR*', texto)
        self.assertIn('K9s.!', texto)
        self.assertIn('UTG · abrir (RFI) · fila de la K, suited: 2', texto)


class Eleccion(unittest.TestCase):
    def test_cerca_de_la_frontera(self):
        rejilla = contexto().rangos.rejilla('UTG', 'RFI')
        self.assertTrue(reloj.cerca_de_frontera(rejilla, 'KTs'))
        self.assertTrue(reloj.cerca_de_frontera(rejilla, 'K9s'))
        self.assertFalse(reloj.cerca_de_frontera(rejilla, 'K4s'))
        self.assertFalse(reloj.cerca_de_frontera(rejilla, 'AA'))
        self.assertTrue(reloj.cerca_de_frontera(rejilla, '55'))

    def test_las_de_la_frontera_pesan_el_triple(self):
        ctx = contexto()
        self.assertEqual(reloj.peso(ctx, 'UTG', 'RFI', 'KTs'), 3 * reloj.peso(ctx, 'UTG', 'RFI', 'K4s'))

    def test_no_repite_la_misma_seguida(self):
        ctx = contexto(pos='UTG', rama='RFI')
        anterior = None
        for _ in range(50):
            actual = reloj.elegir(ctx, anterior)
            self.assertNotEqual(actual, anterior)
            anterior = actual
