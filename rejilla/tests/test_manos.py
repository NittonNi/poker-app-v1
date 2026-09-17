import unittest

from rejilla.manos import (FILAS, celda_de, combos, describir, describir_conjunto, expandir, fila_de,
                           leer_frontera, leer_mano_de_fila, mano_de, normalizar)


class Celdas(unittest.TestCase):
    def test_diagonal_parejas_arriba_suited_abajo_offsuit(self):
        self.assertEqual(mano_de(0, 0), 'AA')
        self.assertEqual(mano_de(1, 5), 'K9s')
        self.assertEqual(mano_de(5, 1), 'K9o')

    def test_celda_de_es_la_inversa(self):
        for i in range(13):
            for j in range(13):
                self.assertEqual(celda_de(mano_de(i, j)), (i, j))

    def test_combos_suman_1326(self):
        self.assertEqual(sum(combos(mano_de(i, j)) for i in range(13) for j in range(13)), 1326)
        self.assertEqual((combos('QQ'), combos('AKs'), combos('AKo')), (6, 4, 12))


class Normalizar(unittest.TestCase):
    def test_mayusculas_orden_y_diez(self):
        self.assertEqual(normalizar('k9s'), 'K9s')
        self.assertEqual(normalizar('9ks'), 'K9s')
        self.assertEqual(normalizar('10jo'), 'JTo')
        self.assertEqual(normalizar('tt'), 'TT')

    def test_rechaza_lo_que_no_es_una_mano(self):
        for malo in ('K9', 'KKs', 'Z9s', 'K9x', ''):
            with self.assertRaises(ValueError):
                normalizar(malo)


class Expandir(unittest.TestCase):
    def test_tramo_con_guion(self):
        self.assertEqual(expandir('KQs-K9s'), {'KQs', 'KJs', 'KTs', 'K9s'})

    def test_tramo_al_reves_da_lo_mismo(self):
        self.assertEqual(expandir('K9s-KQs'), expandir('KQs-K9s'))

    def test_mas_sube_hasta_la_carta_de_abajo_de_la_alta(self):
        self.assertEqual(expandir('ATo+'), {'AKo', 'AQo', 'AJo', 'ATo'})
        self.assertEqual(expandir('JJ+'), {'JJ', 'QQ', 'KK', 'AA'})

    def test_parejas_con_guion(self):
        self.assertEqual(expandir('99-66'), {'99', '88', '77', '66'})

    def test_sin_palo_son_las_dos(self):
        self.assertEqual(expandir('AK'), {'AKs', 'AKo'})

    def test_varias_con_espacios_y_comas(self):
        self.assertEqual(expandir('AKo, 22 A5s-A4s'), {'AKo', '22', 'A5s', 'A4s'})

    def test_tramo_que_mezcla_filas_es_error(self):
        for malo in ('KQs-Q9s', 'KQs-K9o', '99-K9s'):
            with self.assertRaises(ValueError):
                expandir(malo)


class Filas(unittest.TestCase):
    def test_hay_25_filas(self):
        self.assertEqual(len(FILAS), 25)

    def test_la_fila_va_de_la_mejor_a_la_peor(self):
        fila = fila_de('K9s')
        self.assertEqual(fila.manos[0], 'KQs')
        self.assertEqual(fila.manos[-1], 'K2s')
        self.assertEqual(fila.nombre, 'fila de la K, suited')
        self.assertEqual(fila_de('77').manos[0], 'AA')

    def test_cada_mano_esta_en_una_sola_fila(self):
        todas = [m for f in FILAS for m in f.manos]
        self.assertEqual(len(todas), 169)
        self.assertEqual(len(set(todas)), 169)


class Frontera(unittest.TestCase):
    def test_una_mano_sola_es_esa_y_todo_lo_de_encima(self):
        self.assertEqual(leer_frontera('K9s', fila_de('K9s')), {'KQs', 'KJs', 'KTs', 'K9s'})

    def test_varias_piezas_se_leen_tal_cual(self):
        fila = fila_de('ATs')
        self.assertEqual(leer_frontera('ATs+ A5s-A4s', fila), {'AKs', 'AQs', 'AJs', 'ATs', 'A5s', 'A4s'})

    def test_sin_palo_toma_el_de_la_fila(self):
        self.assertEqual(leer_frontera('k9', fila_de('K9s')), {'KQs', 'KJs', 'KTs', 'K9s'})
        self.assertEqual(leer_frontera('AJ+ A5-A4', fila_de('AJo')), {'AKo', 'AQo', 'AJo', 'A5o', 'A4o'})

    def test_nada(self):
        for texto in ('nada', '-', 'ninguna'):
            self.assertEqual(leer_frontera(texto, fila_de('72o')), set())

    def test_mano_de_otra_fila_es_error(self):
        with self.assertRaisesRegex(ValueError, 'Q9s no está en la fila de la K'):
            leer_frontera('Q9s', fila_de('K9s'))
        with self.assertRaisesRegex(ValueError, 'KQs, KJs no están en la fila de la T'):
            leer_frontera('KJs+', fila_de('T9s'))

    def test_describir_en_tramos(self):
        fila = fila_de('ATs')
        self.assertEqual(describir({'AKs', 'AQs', 'AJs', 'ATs', 'A5s', 'A4s'}, fila), 'ATs+ A5s-A4s')
        self.assertEqual(describir({'A8s'}, fila), 'A8s')
        self.assertEqual(describir({'AKs'}, fila), 'AKs')
        self.assertEqual(describir(set(), fila), 'nada')
        self.assertEqual(describir({'AA', 'KK', 'QQ', '55'}, fila_de('55')), 'QQ+ 55')


class ManoDeFila(unittest.TestCase):
    def test_una_mano_con_o_sin_palo(self):
        fila = fila_de('ATo')
        self.assertEqual(leer_mano_de_fila('at', fila), 'ATo')
        self.assertEqual(leer_mano_de_fila('ATo', fila), 'ATo')
        self.assertIsNone(leer_mano_de_fila('nada', fila))

    def test_otra_fila_o_varias_manos_es_error(self):
        fila = fila_de('ATo')
        for malo in ('ATs', 'KTo', 'AT AJ', 'AT+'):
            with self.assertRaises(ValueError):
                leer_mano_de_fila(malo, fila)


class DescribirConjunto(unittest.TestCase):
    def test_por_filas_en_orden_de_la_rejilla(self):
        manos = {'33', '22', 'A9s', 'A8s', 'KTo', 'KJo', 'KQo'}
        self.assertEqual(describir_conjunto(manos), '33-22 A9s-A8s KTo+')
        self.assertEqual(describir_conjunto(set()), 'nada')


if __name__ == '__main__':
    unittest.main()
