

from collections import Counter
from fractions import Fraction
import math, random, re, unicodedata

BOS, EOS = "<s>", "</s>"

MINI_MATILDA = [
    "la ingeniería sí es para mujeres",
    "la ingeniería no es para mujeres",
    "las mujeres estudian ingeniería",
    "mujeres en ingeniería ciencia y tecnología",
    "matilda y las mujeres en ingeniería",
]


def normalizar(texto: str) -> str:
    """Minúsculas, NFC, sin URLs/correos ni líneas de índice ('.....')."""
    texto = unicodedata.normalize("NFC", texto).lower()
    lineas = []
    for linea in texto.splitlines():
        if "....." in linea:
            continue
        linea = re.sub(r"(https?://\S+|www\.\S+)", " ", linea)
        linea = re.sub(r"\S+@\S+", " ", linea)
        lineas.append(linea)
    return "\n".join(lineas)


def tokenizar(oracion: str) -> list:
    """Solo palabras alfabéticas en minúscula (incluya tildes y ñ)."""
    return re.findall(r"[a-záéíóúüñ]+", unicodedata.normalize("NFC", oracion).lower())


def preparar_corpus(texto: str, min_palabras: int = 3) -> list:
    """Texto crudo -> lista de oraciones tokenizadas."""
    texto = normalizar(texto)
    corpus = []
    for fragmento in re.split(r"[.!?;\n]+", texto):
        tokens = tokenizar(fragmento)
        if len(tokens) >= min_palabras:
            corpus.append(tokens)
    return corpus


def _a_tokens(oracion):
    """Acepta una oración como texto o como lista de palabras."""
    if isinstance(oracion, str):
        return tokenizar(oracion)
    return list(oracion)


class ModeloNGrama:
    def __init__(self, usar_fin: bool = True):
        self.usar_fin = usar_fin
        self.c1, self.c2, self.c3, self.h3 = Counter(), Counter(), Counter(), Counter()
        self.h2 = Counter()   # c(h): veces que h es contexto de un bigrama

    def _fin(self):
        return [EOS] if self.usar_fin else []

    def entrenar(self, oraciones):          # Ej. 3.8 — llene c1, c2, c3, h3
        self.c1, self.c2, self.c3, self.h3 = Counter(), Counter(), Counter(), Counter()
        self.h2 = Counter()
        for oracion in oraciones:
            palabras = _a_tokens(oracion)
            bi = [BOS] + palabras + self._fin()
            tri = [BOS, BOS] + palabras + self._fin()
            for t in bi:
                self.c1[t] += 1
            for i in range(len(bi) - 1):
                self.c2[(bi[i], bi[i + 1])] += 1
                self.h2[bi[i]] += 1
            for i in range(len(tri) - 2):
                self.c3[(tri[i], tri[i + 1], tri[i + 2])] += 1
                self.h3[(tri[i], tri[i + 1])] += 1
        return self

    @property
    def V(self):                            # número de tipos (incl. <s>, </s>)
        return len(self.c1)

    @property
    def N(self):                            # número de tokens (incl. <s>, </s>)
        return sum(self.c1.values())

    def p_unigrama(self, w):                # c(w) / N
        if self.N == 0:
            return Fraction(0)
        return Fraction(self.c1[w], self.N)

    def p_mle(self, w, h):                  # c(h w) / c(h)
        if self.h2[h] == 0:
            return Fraction(0)
        return Fraction(self.c2[(h, w)], self.h2[h])

    def p_laplace(self, w, h):              # (c(h w) + 1) / (c(h) + V)
        return Fraction(self.c2[(h, w)] + 1, self.h2[h] + self.V)

    def p_mle_tri(self, w, h1, h2):         # Ej. 3.1
        if self.h3[(h1, h2)] == 0:
            return Fraction(0)
        return Fraction(self.c3[(h1, h2, w)], self.h3[(h1, h2)])

    def p_laplace_tri(self, w, h1, h2):     # Ej. 3.6
        return Fraction(self.c3[(h1, h2, w)] + 1, self.h3[(h1, h2)] + self.V)

    def p_interpolada(self, w, h, l1=Fraction(1, 2), l2=Fraction(1, 2)):  # Ej. 3.7
        return Fraction(l1) * self.p_unigrama(w) + Fraction(l2) * self.p_mle(w, h)

    def prob_oracion(self, oracion, metodo="mle"):   # Ej. 3.2  ("mle" | "laplace")
        padded = [BOS] + _a_tokens(oracion) + self._fin()
        f = self.p_mle if metodo == "mle" else self.p_laplace
        p = Fraction(1)
        for i in range(len(padded) - 1):
            p *= f(padded[i + 1], padded[i])
        return p

    def perplejidad(self, oraciones, metodo="laplace"):  # Ej. 3.11 (inf si P = 0)
        if isinstance(oraciones, str):
            oraciones = [oraciones]
        log_p, M = 0.0, 0
        for oracion in oraciones:
            palabras = _a_tokens(oracion)
            p = self.prob_oracion(palabras, metodo)
            if p == 0:
                return math.inf
            log_p += math.log(p)
            M += len(palabras) + (1 if self.usar_fin else 0)
        return math.exp(-log_p / M)

    def generar(self, semilla=None, max_palabras=25):    # Ej. 3.10
        rng = random.Random(semilla)
        actual, salida = BOS, []
        for _ in range(max_palabras):
            candidatos = sorted((w, c) for (h, w), c in self.c2.items() if h == actual)
            if not candidatos:
                break
            palabras = [w for w, _ in candidatos]
            pesos = [c for _, c in candidatos]
            siguiente = rng.choices(palabras, weights=pesos, k=1)[0]
            if siguiente == EOS:
                break
            salida.append(siguiente)
            actual = siguiente
        return " ".join(salida)

    def top_unigramas(self, k=15):          # Ej. 3.9
        return [(w, c) for w, c in self.c1.most_common() if w not in (BOS, EOS)][:k]

    def top_bigramas(self, k=15):           # Ej. 3.9
        return [(b, c) for b, c in self.c2.most_common()
                if BOS not in b and EOS not in b][:k]


def perplejidad_unigrama(entrenamiento, prueba):     # Ej. 3.12
    """Perplejidad de un modelo unigrama MLE: P(w) = c(w) / N."""
    cuentas = Counter(entrenamiento)
    N = len(entrenamiento)
    log_p = 0.0
    for w in prueba:
        if cuentas[w] == 0:
            return math.inf
        log_p += math.log(Fraction(cuentas[w], N))
    return math.exp(-log_p / len(prueba))