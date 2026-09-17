import unittest

from rejilla.ejercicios import diferencial
from rejilla.leitner import clave
from rejilla.tests.utiles import contexto


class Preguntar(unittest.TestCase):
    def test_acierto(self):
        ctx = contexto(['44 A5s-A4s 65s'])
        diferencial.preguntar(ctx, 'UTG', 'HJ')
        self.assertEqual(ctx.sesion.marcador['Diferencial'], [1, 1])
        self.assertIn('Bien: entran 4', ctx.consola.texto)
        self.assertEqual(ctx.estado.tarjetas[clave('6max', 'HJ', 'RFI', '65s')]['respuesta'], 'R')

    def test_faltan_y_sobran_con_la_rejilla_marcada(self):
        ctx = contexto(['44 A5s 33'])
        diferencial.preguntar(ctx, 'UTG', 'HJ')
        texto = ctx.consola.texto
        self.assertEqual(ctx.sesion.marcador['Diferencial'], [0, 1])
        self.assertIn('Entran 4 y acertaste 2', texto)
        self.assertIn('Te faltan: A4s 65s', texto)
        self.assertIn('Sobran: 33', texto)
        self.assertIn('44 R+', texto)
        self.assertIn('65sR?', texto)
        self.assertIn('33 .*', texto)

    def test_nada(self):
        ctx = contexto(['nada'])
        diferencial.preguntar(ctx, 'UTG', 'HJ')
        self.assertIn('Te faltan: 44 A5s-A4s 65s', ctx.consola.texto)

    def test_decir_que_entra_una_que_ya_jugaba_es_fallo_de_la_de_antes(self):
        ctx = contexto(['44 A5s-A4s 65s AKs'])
        diferencial.preguntar(ctx, 'UTG', 'HJ')
        self.assertEqual(ctx.estado.tarjetas[clave('6max', 'UTG', 'RFI', 'AKs')]['fallos'], 1)
        self.assertNotIn(clave('6max', 'HJ', 'RFI', 'AKs'), ctx.estado.tarjetas)


class Eleccion(unittest.TestCase):
    def test_el_salto_de_co_a_btn_es_el_que_mas_pesa(self):
        pesos = diferencial.pesos(contexto())
        self.assertEqual(set(pesos), {('UTG', 'HJ'), ('HJ', 'CO'), ('CO', 'BTN'), ('BTN', 'SB')})
        self.assertEqual(max(pesos, key=pesos.get), ('CO', 'BTN'))

    def test_filtro_de_posicion(self):
        self.assertEqual(set(diferencial.pesos(contexto(pos='BTN'))), {('CO', 'BTN'), ('BTN', 'SB')})
