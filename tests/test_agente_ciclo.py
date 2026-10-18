import unittest
from tests import _base  # noqa: F401
import numpy as np
from creditscore.escenarios import correr_escenarios
from creditscore.fabrica import construir, features_de
from creditscore.simulador import generar_solicitudes


class TestCiclo(unittest.TestCase):
    def test_orden_percepcion_decision_accion(self):
        c = construir(2026)
        c["agente"].evaluar(c["prueba"][0]["id"])
        tipos = [e["evento"] for e in c["registro"].eventos]
        i = {t: tipos.index(t) for t in ("EVALUACION_INICIO", "PERCEPCION", "DECISION", "ACCION", "EVALUACION_COMPLETA")}
        self.assertTrue(i["EVALUACION_INICIO"] < i["PERCEPCION"] < i["DECISION"] < i["ACCION"] < i["EVALUACION_COMPLETA"])
        self.assertIn("AUDITORIA", tipos)
        self.assertTrue(all(e["timestamp"] for e in c["registro"].eventos))

    def test_todos_los_escenarios_cumplen(self):
        fallos = [f["id"] for f in correr_escenarios() if not f["cumple"]]
        self.assertEqual(fallos, [])

    def test_reproducibilidad_misma_semilla(self):
        salidas = []
        for _ in range(2):
            c = construir(7, guardar_eventos=False)
            salidas.append([(r["accion"], r["p_default"]) for r in (c["agente"].evaluar(t["id"]) for t in c["prueba"][:100])])
        self.assertEqual(salidas[0], salidas[1])

    def test_aprendizaje_detecta_deriva_y_recalibra(self):
        c = construir(11, guardar_eventos=False)
        a, ent = c["agente"], c["entorno"]
        d = generar_solicitudes(800, np.random.default_rng(5), prefijo="DD", deriva=1.0)
        for t in d:
            ent.registrar_solicitud(t); a.evaluar(t["id"]); a.registrar_resultado_observado(t["id"])
        r = a.revisar_aprendizaje()
        self.assertTrue(r["deriva"])
        self.assertEqual(r["accion"], "recalibrado")
        self.assertIn("recal1", c["modelo"].version)

    def test_sin_datos_suficientes_no_recalibra(self):
        c = construir(11, guardar_eventos=False)
        r = c["agente"].revisar_aprendizaje()
        self.assertEqual(r["accion"], "datos_insuficientes")


if __name__ == "__main__":
    unittest.main()
