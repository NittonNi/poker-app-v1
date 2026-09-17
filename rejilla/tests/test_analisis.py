import unittest

from rejilla.analisis import (corregir_diferencial, corregir_fila, corregir_salto, diferencial, peores_zonas,
                              porcentaje_estimado, zona)
from rejilla.manos import fila_de
from rejilla.rangos import Rejilla
from rejilla.tests.test_rangos import rejilla_con

# Fila de la A suited: abre ATs+ y A5s-A4s; offsuit: AJo+.
RFI = Rejilla(rejilla_con(AKs='R', AQs='R', AJs='R', ATs='R', A5s='R', A4s='R', AKo='R', AQo='R', AJo='R'))


class CorregirFila(unittest.TestCase):
    def test_acierto_exacto(self):
        r = corregir_fila({'R': {'AKs', 'AQs', 'AJs', 'ATs', 'A5s', 'A4s'}}, RFI, fila_de('ATs'))
        self.assertTrue(r.acierto)
        self.assertEqual(r.fallos, set())

    def test_sin_las_sueltas_falla_solo_en_ellas(self):
        r = corregir_fila({'R': {'AKs', 'AQs', 'AJs', 'ATs'}}, RFI, fila_de('ATs'))
        self.assertFalse(r.acierto)
        self.assertEqual(r.fallos, {'A5s', 'A4s'})
        self.assertEqual(r.dicha['A5s'], 'F')

    def test_con_dos_acciones_cada_mano_lleva_la_que_se_dijo(self):
        vs_open = Rejilla(rejilla_con(AKs='R', AQs='C', AJs='C'))
        r = corregir_fila({'R': {'AKs'}, 'C': {'AQs'}}, vs_open, fila_de('AKs'))
        self.assertEqual(r.fallos, {'AJs'})
        self.assertEqual(r.dicha['AQs'], 'C')

    def test_misma_mano_en_dos_acciones_es_error(self):
        with self.assertRaises(ValueError):
            corregir_fila({'R': {'AKs'}, 'C': {'AKs'}}, RFI, fila_de('AKs'))


class Salto(unittest.TestCase):
    def test_fronteras_y_distancia(self):
        r = corregir_salto('ATs', 'AJo', RFI, 'A')
        self.assertTrue(r.acierto_suited and r.acierto_offsuit)
        self.assertEqual((r.real_suited, r.real_offsuit), ('ATs', 'AJo'))
        self.assertEqual(r.distancia_real, 1)
        self.assertEqual(r.distancia_tuya, 1)
        self.assertEqual(r.sueltas_suited, 'A5s-A4s')

    def test_distancia_mal_aunque_una_frontera_este_bien(self):
        r = corregir_salto('A9s', 'AJo', RFI, 'A')
        self.assertFalse(r.acierto_suited)
        self.assertTrue(r.acierto_offsuit)
        self.assertEqual(r.distancia_tuya, 2)
        self.assertFalse(r.acierto_distancia)

    def test_nada_en_offsuit(self):
        r = corregir_salto('ATs', None, Rejilla(rejilla_con(ATs='R', AKs='R', AQs='R', AJs='R')), 'A')
        self.assertIsNone(r.real_offsuit)
        self.assertTrue(r.acierto_offsuit)
        self.assertEqual(r.distancia_real, 4)  # de 'ninguna' (antes de AK) a ATs hay 4 escalones

    def test_celdas_que_decide_la_respuesta(self):
        r = corregir_salto('AJs', 'AJo', RFI, 'A')
        # dijo AJs: ATs queda fuera y es fallo; las sueltas no se preguntan
        self.assertEqual(r.fallos, {'ATs'})
        self.assertIn('AKs', r.celdas)
        self.assertNotIn('A5s', r.celdas)


class Diferencial(unittest.TestCase):
    def test_entran_y_salen(self):
        a = Rejilla(rejilla_con(AA='R', KK='R'))
        b = Rejilla(rejilla_con(AA='R', QQ='R', JJ='R'))
        self.assertEqual(diferencial(a, b), ({'QQ', 'JJ'}, {'KK'}))

    def test_corregir(self):
        r = corregir_diferencial({'QQ', 'TT'}, {'QQ', 'JJ'})
        self.assertEqual((r.aciertos, r.faltan, r.sobran), ({'QQ'}, {'JJ'}, {'TT'}))
        self.assertFalse(r.acierto)


class Zonas(unittest.TestCase):
    def test_zona_es_posicion_rama_y_fila(self):
        self.assertEqual(zona('BTN', 'RFI', 'K7s'), 'BTN · abrir (RFI) · fila de la K, suited')

    def test_peores_zonas_por_tasa_de_fallo_con_minimo_de_intentos(self):
        intentos = ([('BTN', 'RFI', 'K7s', False)] * 3 + [('BTN', 'RFI', 'K6s', True)] +
                    [('UTG', 'RFI', '77', False)] * 1 +                    # un solo intento: no cuenta
                    [('CO', 'RFI', 'A9o', False), ('CO', 'RFI', 'A8o', True)] +
                    [('HJ', 'RFI', 'QJo', True)] * 4)
        peores = peores_zonas(intentos, cuantas=3)
        self.assertEqual([z for z, *_ in peores],
                         ['BTN · abrir (RFI) · fila de la K, suited', 'CO · abrir (RFI) · fila de la A, offsuit'])
        self.assertEqual(peores[0][1:], (3, 4))


class Estimado(unittest.TestCase):
    def test_tu_rejilla_es_la_real_con_tus_respuestas_encima(self):
        real = Rejilla(rejilla_con(AA='R', KK='R'))
        tu_pct, real_pct, vistas = porcentaje_estimado(real, {'KK': 'F', 'AKs': 'R', 'QQ': 'F'})
        self.assertAlmostEqual(real_pct, 100 * 12 / 1326)
        self.assertAlmostEqual(tu_pct, 100 * 10 / 1326)
        self.assertEqual(vistas, 3)
