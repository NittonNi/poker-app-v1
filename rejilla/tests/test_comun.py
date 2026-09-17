import unittest
from unittest import mock

from rejilla.consola import Consola, Salir
from rejilla.ejercicios.comun import elegir, leer_accion, verbo
from rejilla.leitner import clave
from rejilla.tests.utiles import HOY, contexto


class Acciones(unittest.TestCase):
    def test_palabras_de_cada_accion(self):
        for texto, letra in (('r', 'R'), ('raise', 'R'), ('Subir', 'R'), ('dentro', 'R'), ('3bet', 'R'),
                             ('c', 'C'), ('pagar', 'C'), ('call', 'C'),
                             ('f', 'F'), ('fold', 'F'), ('fuera', 'F'),
                             ('a', 'A'), ('all-in', 'A'), ('allin', 'A')):
            self.assertEqual(leer_accion(texto), letra, texto)
        self.assertIsNone(leer_accion('quizá'))

    def test_verbo_segun_rama(self):
        self.assertEqual(verbo('RFI', 'R'), 'abre')
        self.assertEqual(verbo('vs_open_CO', 'R'), 'resube (3bet)')
        self.assertEqual(verbo('vs_3bet_SB', 'R'), 'hace 4bet')
        self.assertEqual(verbo('vs_open_CO', 'C'), 'paga')


class Elegir(unittest.TestCase):
    def test_nunca_elige_peso_cero_si_hay_otros(self):
        import random
        rng = random.Random(1)
        for _ in range(50):
            self.assertEqual(elegir(rng, ['a', 'b', 'c'], [0, 5, 0]), 'b')

    def test_todo_a_cero_elige_cualquiera(self):
        import random
        self.assertIn(elegir(random.Random(1), ['a', 'b'], [0, 0]), ['a', 'b'])


class Contexto(unittest.TestCase):
    def test_filtros_de_posicion_y_rama(self):
        self.assertEqual(contexto(pos='BTN', rama='RFI').ramas(), [('BTN', 'RFI')])
        self.assertEqual(contexto(pos='BTN', rama='vs_open').ramas(),
                         [('BTN', 'vs_open_UTG'), ('BTN', 'vs_open_HJ'), ('BTN', 'vs_open_CO')])
        self.assertEqual(len(contexto(rama='RFI').ramas()), 5)

    def test_anotar_pasa_por_leitner_la_sesion_y_el_disco(self):
        ctx = contexto()
        ctx.anotar('BTN', 'RFI', {'K7s': (False, 'F'), 'AA': (True, 'R')})
        k = clave('6max', 'BTN', 'RFI', 'K7s')
        self.assertEqual(ctx.estado.tarjetas[k]['caja'], 1)
        self.assertIn(('BTN', 'RFI', 'K7s', False), ctx.sesion.intentos)
        self.assertTrue(ctx.estado.ruta.exists())

    def test_la_sesion_devuelve_lo_fallado_unos_turnos_despues(self):
        s = contexto().sesion
        s.repetir_luego('fronteras', 'fila', dentro=2)
        self.assertIsNone(s.pendiente('fronteras'))
        s.avanzar()
        s.avanzar()
        self.assertEqual(s.pendiente('fronteras'), 'fila')
        self.assertIsNone(s.pendiente('fronteras'))


class ConsolaReal(unittest.TestCase):
    def test_salir_y_fin_de_entrada(self):
        with mock.patch('builtins.input', return_value='salir'):
            with self.assertRaises(Salir):
                Consola().preguntar('> ')
        with mock.patch('builtins.input', side_effect=EOFError):
            with self.assertRaises(Salir):
                Consola().preguntar('> ')
        with mock.patch('builtins.input', return_value='  K9s '):
            self.assertEqual(Consola().preguntar('> '), 'K9s')

    def test_tecla_sin_msvcrt_usa_la_linea_y_mide_el_tiempo(self):
        c = Consola(teclas_directas=False)
        with mock.patch('builtins.input', return_value='d'):
            tecla, segundos = c.tecla('> ', 3)
        self.assertEqual(tecla, 'd')
        self.assertLess(segundos, 1)
