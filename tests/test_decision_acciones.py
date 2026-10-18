import unittest
from tests import _base  # noqa: F401
import numpy as np
from creditscore.config import cargar_config
from creditscore.decision import APROBAR, REVISION, ModuloDecision
from creditscore.fabrica import construir
from creditscore.memoria import MemoriaLargoPlazo
from creditscore.percepcion import construir_features


class TestDecision(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.c = construir(2026)

    def test_bandas_de_calificacion(self):
        d = ModuloDecision(cargar_config())
        self.assertEqual([d.calificar(p) for p in (0.01, 0.07, 0.15, 0.30, 0.9)], list("ABCDE"))

    def test_r3_desacuerdo_con_casos_similares_remite_a_revision(self):
        c = self.c
        x = construir_features(8e6, 8e5, 0, 120, 3)   # perfil de bajo riesgo: sin R3 el agente aprobaria
        mem = MemoriaLargoPlazo(5)
        for i in range(30):   # historial contradictorio: casos identicos que SI incumplieron
            mem.agregar(f"X{i}", x, "HISTORICO", "h", y=1)
        from creditscore.percepcion import Percepcion
        per = Percepcion("Z", {}, "VALIDA", [], dti=0.1, features=x)
        dec = ModuloDecision(cargar_config()).decidir(per, c["modelo"], mem)
        self.assertEqual(dec.accion, REVISION)
        self.assertIn("R3_INCERTIDUMBRE", dec.reglas)
        sin_hist = ModuloDecision(cargar_config()).decidir(per, c["modelo"], MemoriaLargoPlazo(5))
        self.assertEqual(sin_hist.accion, APROBAR)

    def test_probabilidades_en_rango_y_costos_presentes(self):
        x = construir_features(3e6, 9e5, 1, 60, 4)
        p = self.c["modelo"].predict_proba(x)
        self.assertTrue(0 < p < 1)

    def test_remision_incluye_factores_para_el_analista(self):
        c = construir(2026)
        from creditscore.escenarios import sol
        s = sol("F1", 2.8e6, 0.9e6, 1, 72, 4)
        c["entorno"].registrar_solicitud(s)
        r = c["agente"].evaluar("F1")
        self.assertEqual(r["accion"], REVISION)
        carga = c["entorno"].bandeja[-1]
        self.assertEqual(len(carga["factores"]), 3)
        self.assertIn("razon", carga)

    def test_error_interno_es_failsafe(self):
        c = construir(2026)
        c["agente"].decision.decidir = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom"))
        r = c["agente"].evaluar(c["prueba"][0]["id"])
        self.assertEqual(r["accion"], REVISION)
        self.assertIn("R0_ERROR_INTERNO", r["reglas"])
        self.assertTrue(any(e["evento"] == "ERROR_INTERNO" for e in c["registro"].eventos))


if __name__ == "__main__":
    unittest.main()
