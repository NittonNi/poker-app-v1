import unittest

from rejilla.ejercicios import identifica
from rejilla.tests.utiles import contexto


class Preguntar(unittest.TestCase):
    def test_acierto(self):
        ctx = contexto(['co rfi'])
        identifica.preguntar(ctx, 'CO', 'RFI')
        self.assertEqual(ctx.sesion.marcador['Identifica'], [1, 1])
        self.assertIn('Bien: CO · abrir (RFI)', ctx.consola.texto)

    def test_vale_cualquiera_de_las_rejillas_iguales(self):
        ctx = contexto(['co open hj'])
        identifica.preguntar(ctx, 'BTN', 'vs_open_UTG')
        self.assertEqual(ctx.sesion.marcador['Identifica'], [1, 1])
        self.assertIn('la misma rejilla', ctx.consola.texto)

    def test_fallo_ensena_las_dos_con_las_diferencias(self):
        ctx = contexto(['hj rfi'])
        identifica.preguntar(ctx, 'UTG', 'RFI')
        texto = ctx.consola.texto
        self.assertEqual(ctx.sesion.marcador['Identifica'], [0, 1])
        self.assertIn('Era UTG · abrir (RFI)', texto)
        self.assertIn('4 manos distintas', texto)
        self.assertIn('HJ · abrir (RFI)', texto)

    def test_respuestas_que_no_valen_se_repiten(self):
        ctx = contexto(['patata', 'BB RFI', 'UTG rfi'])
        identifica.preguntar(ctx, 'UTG', 'RFI')
        self.assertEqual(ctx.sesion.marcador['Identifica'], [1, 1])
        self.assertIn('BB · RFI no está en ranges.json', ctx.consola.texto)

    def test_no_dice_la_rejilla_antes_de_preguntar(self):
        ctx = contexto(['utg rfi'])
        identifica.preguntar(ctx, 'UTG', 'RFI')
        antes = ctx.consola.salida[:ctx.consola.salida.index(next(l for l in ctx.consola.salida if 'Bien' in l))]
        self.assertFalse(any('UTG' in l for l in antes))


class Eleccion(unittest.TestCase):
    def test_lo_fallado_vuelve(self):
        ctx = contexto(['hj rfi'])
        identifica.preguntar(ctx, 'UTG', 'RFI')
        for _ in range(3):
            ctx.sesion.avanzar()
        self.assertEqual(identifica.elegir(ctx), ('UTG', 'RFI'))

    def test_una_por_grupo_de_rejillas_iguales(self):
        ctx = contexto()
        vistas = {identifica.elegir(ctx) for _ in range(300)}
        grupos = {tuple(ctx.rangos.grupo(p, r)) for p, r in vistas}
        self.assertEqual(len(vistas), len(grupos))
