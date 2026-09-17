import json
import random
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path

from rejilla.__main__ import elegir_ejercicio, main
from rejilla.tests.utiles import HOY, RAIZ, ConsolaGuion


def estado_tmp():
    return str(Path(tempfile.mkdtemp()) / 'rejilla.json')


def correr(argv, respuestas=(), teclas=()):
    consola = ConsolaGuion(respuestas, teclas)
    codigo = main(argv + ['--sin-color'], consola=consola, hoy=HOY)
    return codigo, consola.texto


class Modos(unittest.TestCase):
    def test_un_modo_suelto_acaba_con_informe_y_guarda(self):
        ruta = estado_tmp()
        codigo, texto = correr(['diferencial', '-n', '1', '--pos', 'HJ', '--estado', ruta], ['44 A5s-A4s 65s'])
        # con --pos HJ los saltos posibles son UTG→HJ y HJ→CO; si sale el segundo, la respuesta falla
        self.assertEqual(codigo, 0)
        self.assertIn('[Diferencial]', texto)
        self.assertIn('Resumen de la sesión', texto)
        self.assertIn('Diferencial: ', texto)
        self.assertTrue(json.loads(Path(ruta).read_text(encoding='utf-8'))['tarjetas'])

    def test_salir_a_mitad_da_el_informe(self):
        codigo, texto = correr(['repaso', '--estado', estado_tmp()])
        self.assertEqual(codigo, 0)
        self.assertIn('Tus tres zonas peores', texto)

    def test_ver_una_rejilla(self):
        codigo, texto = correr(['ver', 'UTG', 'RFI', '--estado', estado_tmp()])
        self.assertEqual(codigo, 0)
        self.assertIn('UTG · abrir (RFI) · 12,4 %', texto)
        self.assertIn('AA R AKsR', texto)

    def test_ver_todas_las_de_una_posicion(self):
        codigo, texto = correr(['ver', 'BB', '--estado', estado_tmp()])
        self.assertEqual(codigo, 0)
        self.assertIn('BB · contra subida de UTG', texto)
        self.assertIn('BB · contra subida de SB', texto)

    def test_informe_suelto(self):
        codigo, texto = correr(['informe', '--estado', estado_tmp()])
        self.assertEqual(codigo, 0)
        self.assertIn('Lo que jugarías tú frente a la tabla', texto)
        self.assertNotIn('Resumen de la sesión', texto)

    def test_filtros_que_no_dejan_nada(self):
        codigo, texto = correr(['fronteras', '--pos', 'BB', '--rama', 'RFI', '--estado', estado_tmp()])
        self.assertEqual(codigo, 1)
        self.assertIn('No hay ninguna rejilla', texto)

    def test_posicion_que_no_existe(self):
        codigo, texto = correr(['fronteras', '--pos', 'MP', '--estado', estado_tmp()])
        self.assertEqual(codigo, 2)
        self.assertIn('MP no es una posición', texto)

    def test_rangos_rotos(self):
        malo = Path(tempfile.mkdtemp()) / 'ranges.json'
        malo.write_text('{"version": 1, "6max": {"BB": {"RFI": []}}}', encoding='utf-8')
        codigo, texto = correr(['fronteras', '--rangos', str(malo), '--estado', estado_tmp()])
        self.assertEqual(codigo, 1)
        self.assertIn('BB · RFI', texto)


class Menu(unittest.TestCase):
    def test_ver_e_informe_desde_el_menu(self):
        codigo, texto = correr(['--estado', estado_tmp()], ['8', 'utg rfi', '9', '0'])
        self.assertEqual(codigo, 0)
        self.assertIn('Fronteras', texto)
        self.assertIn('UTG · abrir (RFI) · 12,4 %', texto)
        self.assertIn('Lo que jugarías tú frente a la tabla', texto)

    def test_opcion_que_no_existe(self):
        codigo, texto = correr(['--estado', estado_tmp()], ['x', '0'])
        self.assertEqual(codigo, 0)
        self.assertIn('Elige un número', texto)


class Repaso(unittest.TestCase):
    def test_fronteras_es_lo_que_mas_sale_y_luego_diferencial(self):
        rng = random.Random(3)
        cuenta = Counter(elegir_ejercicio(rng) for _ in range(2000))
        self.assertEqual([e for e, _ in cuenta.most_common(2)], ['fronteras', 'diferencial'])
        self.assertNotIn('blanco', cuenta)


class DesdeLaTerminal(unittest.TestCase):
    def test_python_m_rejilla_funciona(self):
        r = subprocess.run([sys.executable, '-m', 'rejilla', 'ver', 'CO', 'RFI', '--sin-color', '--estado', estado_tmp()],
                           cwd=RAIZ, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn('CO · abrir (RFI) · 23,4 %', r.stdout)
