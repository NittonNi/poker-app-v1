import unittest

from rejilla.ejercicios import blanco
from rejilla.tests.utiles import contexto

UTG_ENTERA = ['55+ r', 'ATs+ r', 'KTs+ r', 'QTs+ r', 'JTs r', 'T9s r', '98s r', '87s r', '76s r',
              'AJo+ r', 'KQo r', 'fin']


class Rellenar(unittest.TestCase):
    def test_entera_y_bien(self):
        ctx = contexto(UTG_ENTERA)
        blanco.preguntar(ctx, 'UTG', 'RFI')
        texto = ctx.consola.texto
        self.assertEqual(ctx.sesion.marcador['Rejilla en blanco'], [1, 1])
        self.assertIn('Aciertos: 169 de 169', texto)
        self.assertIn('Abre tu versión: 12,4 % · la tabla: 12,4 %', texto)
        self.assertIn('R subir · F retirarse', texto)
        self.assertIn('1 mano → subir', texto)
        self.assertNotIn('pagar', texto)

    def test_a_medias_marca_los_fallos_y_compara_porcentajes(self):
        ctx = contexto(['55+ r', 'fin'])
        blanco.preguntar(ctx, 'UTG', 'RFI')
        texto = ctx.consola.texto
        self.assertEqual(ctx.sesion.marcador['Rejilla en blanco'], [0, 1])
        self.assertIn('10 manos → subir', texto)
        self.assertIn('Aciertos: 151 de 169', texto)
        self.assertIn('Abre tu versión: 4,5 % · la tabla: 12,4 %', texto)
        self.assertIn('AKs.*', texto)
        self.assertEqual(len([k for k in ctx.estado.tarjetas if k.startswith('6max|UTG|RFI|')]), 169)

    def test_la_accion_puede_ir_delante(self):
        ctx = contexto(['raise KQs-KTs', 'fin'])
        blanco.preguntar(ctx, 'UTG', 'RFI')
        self.assertIn('3 manos → subir', ctx.consola.texto)

    def test_lo_que_no_se_entiende_no_rompe(self):
        ctx = contexto(['KQs-Q9s r', 'AKs quizá', 'fin'])
        blanco.preguntar(ctx, 'UTG', 'RFI')
        texto = ctx.consola.texto
        self.assertIn('no están en la misma fila', texto)
        self.assertIn('falta la acción', texto)
        self.assertEqual(ctx.sesion.marcador['Rejilla en blanco'], [0, 1])

    def test_ver_y_borrar(self):
        ctx = contexto(['55+ r', 'borrar 66-55', 'ver', 'fin'])
        blanco.preguntar(ctx, 'UTG', 'RFI')
        texto = ctx.consola.texto
        self.assertIn('2 manos borradas', texto)
        self.assertIn('AA R AKs·', texto)
        self.assertIn('Aciertos: 149 de 169', texto)

    def test_con_varias_acciones_da_el_porcentaje_de_cada_una(self):
        ctx = contexto(['fin'])
        blanco.preguntar(ctx, 'BTN', 'vs_open_UTG')
        texto = ctx.consola.texto
        self.assertIn('Juega tu versión: 0,0 %', texto)
        self.assertIn('resube (3bet): tú 0,0 %', texto)
        self.assertIn('paga: tú 0,0 %', texto)


class Eleccion(unittest.TestCase):
    def test_respeta_filtros(self):
        ctx = contexto(pos='SB')
        for _ in range(10):
            self.assertEqual(blanco.elegir(ctx)[0], 'SB')
