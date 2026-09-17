import unittest

from rejilla.informe import informe
from rejilla.leitner import clave
from rejilla.tests.utiles import HOY, contexto


class Informe(unittest.TestCase):
    def test_marcador_de_la_sesion(self):
        ctx = contexto()
        ctx.sesion.anotar('Fronteras', True)
        ctx.sesion.anotar('Fronteras', False)
        texto = '\n'.join(informe(ctx.rangos, ctx.estado, ctx.sesion))
        self.assertIn('Fronteras: 1 de 2', texto)

    def test_tres_zonas_peores(self):
        ctx = contexto()
        ctx.sesion.intentos += ([('BTN', 'RFI', 'K7s', False)] * 3 + [('BTN', 'RFI', 'K6s', True)] +
                                [('CO', 'RFI', 'A9o', False)] * 2 + [('UTG', 'RFI', '55', False), ('UTG', 'RFI', '44', True)] +
                                [('HJ', 'RFI', '44', False), ('HJ', 'RFI', '33', True), ('HJ', 'RFI', '22', True)])
        lineas = informe(ctx.rangos, ctx.estado, ctx.sesion)
        texto = '\n'.join(lineas)
        self.assertIn('1. CO · abrir (RFI) · fila de la A, offsuit: 2 fallos de 2', texto)
        self.assertIn('2. BTN · abrir (RFI) · fila de la K, suited: 3 fallos de 4', texto)
        self.assertIn('3. UTG · abrir (RFI) · parejas: 1 fallo de 2', texto)
        self.assertNotIn('HJ · abrir (RFI) · parejas', texto)

    def test_sin_fallos(self):
        ctx = contexto()
        self.assertIn('Ninguna zona con fallos', '\n'.join(informe(ctx.rangos, ctx.estado, ctx.sesion)))

    def test_tabla_de_porcentajes_por_posicion(self):
        ctx = contexto()
        ctx.estado.registrar(clave('6max', 'UTG', 'RFI', 'KTs'), False, 'F', HOY)
        ctx.estado.registrar(clave('6max', 'BB', 'vs_open_SB', 'AA'), True, 'R', HOY)
        lineas = informe(ctx.rangos, ctx.estado, ctx.sesion)
        utg = next(l for l in lineas if l.strip().startswith('UTG · abrir'))
        self.assertEqual(utg.split()[3:], ['12,1', '%', '12,4', '%', '-0,3', '1/169'])
        self.assertTrue(any(l.strip().startswith('BTN · abrir') for l in lineas))       # sin contestar, sale igual
        self.assertTrue(any('BB · contra subida de SB' in l for l in lineas))          # con respuestas, sale
        self.assertFalse(any('BTN · contra subida de CO' in l for l in lineas))        # sin respuestas, no

    def test_sin_sesion_las_zonas_salen_de_todo_lo_guardado(self):
        ctx = contexto()
        for _ in range(3):
            ctx.estado.registrar(clave('6max', 'BTN', 'RFI', 'K7s'), False, 'F', HOY)
        texto = '\n'.join(informe(ctx.rangos, ctx.estado))
        self.assertIn('BTN · abrir (RFI) · fila de la K, suited: 3 fallos de 3', texto)
        self.assertNotIn('Resumen de la sesión', texto)
