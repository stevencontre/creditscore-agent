import unittest
from tests import _base  # noqa: F401
from creditscore.config import cargar_config
from creditscore.entorno import EntornoSimulado
from creditscore.escenarios import sol
from creditscore.percepcion import ModuloPercepcion, a_numero
from creditscore.registro import RegistroEventos


def percibir(s, setup=None):
    e = EntornoSimulado([s])
    if setup:
        setup(e)
    return ModuloPercepcion(e, cargar_config(), RegistroEventos()).percibir(s["id"])


class TestPercepcion(unittest.TestCase):
    def test_solicitud_valida_genera_5_features(self):
        p = percibir(sol("T1", 3e6, 9e5, 1, 60, 4))
        self.assertEqual(p.estado, "VALIDA")
        self.assertEqual(p.features.shape, (5,))
        self.assertAlmostEqual(p.dti, 0.3)

    def test_a_numero(self):
        self.assertEqual(a_numero("3000000"), 3000000.0)
        for malo in ["abc", None, True, float("nan"), float("inf")]:
            self.assertIsNone(a_numero(malo))

    def test_cadena_numerica_es_aceptada(self):
        s = sol("T2", "3000000", 9e5, 1, 60, 4)
        self.assertEqual(percibir(s).estado, "VALIDA")

    def test_pagos_no_entero_es_invalido(self):
        self.assertEqual(percibir(sol("T3", 3e6, 9e5, 2.5, 60, 4)).estado, "INVALIDA")

    def test_dti_inconsistente_es_fuera_de_dominio(self):
        p = percibir(sol("T4", 1e6, 5e7, 1, 60, 4))
        self.assertEqual(p.estado, "FUERA_DOMINIO")
        self.assertTrue(any(x.startswith("dti:") for x in p.problemas))

    def test_buro_caido_marca_incompleta_y_reintenta(self):
        reg = RegistroEventos()
        s = sol("T5", 3e6, 9e5, 1, 60, 4)
        e = EntornoSimulado([s]); e.buro_caido = True
        p = ModuloPercepcion(e, cargar_config(), reg).percibir("T5")
        self.assertEqual(p.estado, "INCOMPLETA")
        self.assertEqual(sum(1 for x in reg.eventos if x["evento"] == "SENSOR_FALLO"), 3)


if __name__ == "__main__":
    unittest.main()
