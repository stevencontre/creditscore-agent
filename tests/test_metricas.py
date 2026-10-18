import unittest
from tests import _base  # noqa: F401
import numpy as np
from creditscore.metricas import auc_roc, brier, ece, psi


class TestMetricas(unittest.TestCase):
    def test_auc_valor_conocido(self):
        self.assertAlmostEqual(auc_roc([0, 0, 1, 1], [0.1, 0.4, 0.35, 0.8]), 0.75)

    def test_auc_empates_y_extremos(self):
        self.assertAlmostEqual(auc_roc([0, 1, 0, 1], [0.5, 0.5, 0.5, 0.5]), 0.5)
        self.assertEqual(auc_roc([0, 0, 1, 1], [0.1, 0.2, 0.8, 0.9]), 1.0)
        self.assertEqual(auc_roc([0, 0, 1, 1], [0.9, 0.8, 0.2, 0.1]), 0.0)
        self.assertTrue(np.isnan(auc_roc([1, 1], [0.2, 0.3])))

    def test_brier_y_ece(self):
        self.assertAlmostEqual(brier([1, 0], [1.0, 0.0]), 0.0)
        self.assertAlmostEqual(ece([1, 1, 0, 0], [0.9, 0.9, 0.1, 0.1]), 0.1)

    def test_psi_identica_es_cero_y_cambio_es_positivo(self):
        r = np.random.default_rng(0).random(2000)
        self.assertAlmostEqual(psi(r, r), 0.0, places=6)
        self.assertGreater(psi(r, np.clip(r + 0.3, 0, 1)), 0.2)


if __name__ == "__main__":
    unittest.main()
