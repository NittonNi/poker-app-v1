import unittest

from rejilla.ejercicios import salto
from rejilla.leitner import clave
from rejilla.tests.utiles import contexto


class Salto(unittest.TestCase):
    def test_acierto_con_distancia(self):
        ctx = contexto(['A2s', 'ATo'])
        salto.preguntar(ctx, 'CO', 'RFI', 'A')
        self.assertEqual(ctx.sesion.marcador['Salto'], [1, 1])
        self.assertEqual(ctx.sesion.marcador['Salto: distancia'], [1, 1])
        self.assertIn('Bien', ctx.consola.texto)
        self.assertIn('8 escalones', ctx.consola.texto)

    def test_fallo_en_offsuit_tambien_estropea_la_distancia(self):
        ctx = contexto(['a2', 'a9'])
        salto.preguntar(ctx, 'CO', 'RFI', 'A')
        self.assertEqual(ctx.sesion.marcador['Salto'], [0, 1])
        self.assertEqual(ctx.sesion.marcador['Salto: distancia'], [0, 1])
        self.assertIn('offsuit es ATo', ctx.consola.texto)
        self.assertIn('salto de 8 escalones, tú 7', ctx.consola.texto)  # A2s a A9o son 7
        self.assertEqual(ctx.estado.tarjetas[clave('6max', 'CO', 'RFI', 'A9o')]['fallos'], 1)

    def test_avisa_de_las_sueltas(self):
        ctx = contexto(['ATs', 'AJo'])
        salto.preguntar(ctx, 'HJ', 'RFI', 'A')
        self.assertEqual(ctx.sesion.marcador['Salto'], [1, 1])
        self.assertIn('sueltas en suited: A5s-A4s', ctx.consola.texto)

    def test_con_varias_acciones_no_toca_leitner(self):
        ctx = contexto(['A2s', 'ATo'])
        salto.preguntar(ctx, 'BTN', 'vs_open_UTG', 'A')
        self.assertEqual(ctx.sesion.marcador['Salto'], [1, 1])
        self.assertEqual(ctx.estado.tarjetas, {})

    def test_solo_filas_donde_se_juega_algo(self):
        ctx = contexto(pos='UTG', rama='RFI')
        for _ in range(40):
            pos, rama, rango = salto.elegir(ctx)
            self.assertIn(rango, 'AKQJT987')
