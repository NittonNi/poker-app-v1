import unittest

from rejilla.ejercicios import fronteras
from rejilla.leitner import clave
from rejilla.manos import FILAS, fila_de
from rejilla.tests.utiles import contexto

K_SUITED = fila_de('KQs')
A_SUITED = fila_de('AKs')


class UnaAccion(unittest.TestCase):
    def test_acierto(self):
        ctx = contexto(['KTs'])
        fronteras.preguntar_fila(ctx, 'UTG', 'RFI', K_SUITED)
        self.assertEqual(ctx.sesion.marcador['Fronteras'], [1, 1])
        self.assertIn('¿Hasta dónde llega?', ctx.consola.preguntas[0])
        self.assertIn('Bien', ctx.consola.texto)
        tarjetas = ctx.estado.tarjetas
        self.assertEqual(len([k for k in tarjetas if k.startswith('6max|UTG|RFI|K')]), 11)  # KQs..K2s
        self.assertEqual(tarjetas[clave('6max', 'UTG', 'RFI', 'K9s')]['fallos'], 0)

    def test_fallo_dice_la_buena_los_escalones_y_vuelve_luego(self):
        ctx = contexto(['K9s'])
        fronteras.preguntar_fila(ctx, 'UTG', 'RFI', K_SUITED)
        self.assertEqual(ctx.sesion.marcador['Fronteras'], [0, 1])
        self.assertIn('Es KTs+', ctx.consola.texto)
        self.assertIn('te pasas 1 escalón', ctx.consola.texto)
        self.assertEqual(ctx.estado.tarjetas[clave('6max', 'UTG', 'RFI', 'K9s')]['fallos'], 1)
        for _ in range(3):
            ctx.sesion.avanzar()
        self.assertEqual(ctx.sesion.pendiente('fronteras'), ('UTG', 'RFI', 'Ks'))

    def test_las_sueltas_cuentan(self):
        ctx = contexto(['ATs'])
        fronteras.preguntar_fila(ctx, 'HJ', 'RFI', A_SUITED)
        self.assertEqual(ctx.sesion.marcador['Fronteras'], [0, 1])
        self.assertIn('Es ATs+ A5s-A4s', ctx.consola.texto)

    def test_respuesta_que_no_se_entiende_se_repite_sin_contar(self):
        ctx = contexto(['Q9s', 'KTs'])
        fronteras.preguntar_fila(ctx, 'UTG', 'RFI', K_SUITED)
        self.assertEqual(ctx.sesion.marcador['Fronteras'], [1, 1])
        self.assertIn('no está en la fila de la K, suited', ctx.consola.texto)


class VariasAcciones(unittest.TestCase):
    def test_pregunta_cada_accion_de_la_rejilla(self):
        ctx = contexto(['AJs+ A5s-A3s', 'ATs-A6s A2s'])
        fronteras.preguntar_fila(ctx, 'BTN', 'vs_open_UTG', A_SUITED)
        self.assertEqual(ctx.sesion.marcador['Fronteras'], [1, 1])
        self.assertIn('¿Qué resube (3bet)?', ctx.consola.preguntas[0])
        self.assertIn('¿Qué paga?', ctx.consola.preguntas[1])

    def test_la_misma_mano_en_dos_respuestas_vuelve_a_preguntar_todo(self):
        ctx = contexto(['AKs', 'AKs', 'AJs+ A5s-A3s', 'ATs-A6s A2s'])
        fronteras.preguntar_fila(ctx, 'BTN', 'vs_open_UTG', A_SUITED)
        self.assertEqual(ctx.sesion.marcador['Fronteras'], [1, 1])
        self.assertIn('AKs está en dos respuestas', ctx.consola.texto)


class Eleccion(unittest.TestCase):
    def test_respeta_los_filtros(self):
        ctx = contexto(pos='CO', rama='RFI')
        for _ in range(20):
            pos, rama, fila = fronteras.elegir_fila(ctx)
            self.assertEqual((pos, rama), ('CO', 'RFI'))
            self.assertIn(fila, FILAS)

    def test_las_filas_donde_no_se_juega_nada_salen_diez_veces_menos(self):
        from rejilla.manos import fila_por_clave
        ctx = contexto()
        vacia = fronteras.peso_fila(ctx, 'UTG', 'RFI', fila_por_clave('4s'))
        llena = fronteras.peso_fila(ctx, 'UTG', 'RFI', fila_por_clave('Ks'))
        self.assertAlmostEqual(vacia * 10, llena)

    def test_lo_pendiente_va_primero(self):
        ctx = contexto()
        ctx.sesion.repetir_luego('fronteras', ('BTN', 'RFI', 'Ks'), dentro=0)
        self.assertEqual(fronteras.elegir_fila(ctx), ('BTN', 'RFI', K_SUITED))
