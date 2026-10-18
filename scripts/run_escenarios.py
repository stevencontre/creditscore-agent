"""Ejecuta los 17 escenarios deterministas y guarda logs/escenarios.csv, escenarios.json y escenarios_eventos.jsonl."""
import _ruta  # noqa: F401
import csv, json
from pathlib import Path
from creditscore.config import RAIZ
from creditscore.escenarios import correr_escenarios

if __name__ == "__main__":
    d = RAIZ / "logs"; d.mkdir(exist_ok=True)
    log = d / "escenarios_eventos.jsonl"
    if log.exists():
        log.unlink()
    filas = correr_escenarios(ruta_log=log)
    with open(d / "escenarios.json", "w", encoding="utf-8") as f:
        json.dump(filas, f, indent=2, ensure_ascii=False)
    with open(d / "escenarios.csv", "w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(filas[0]), delimiter=";"); w.writeheader(); w.writerows(filas)
    for r in filas:
        print(f"{r['id']} [{'OK' if r['cumple'] else 'FALLA'}] {r['escenario']}")
    print(f"\n{sum(r['cumple'] for r in filas)}/{len(filas)} escenarios cumplen lo esperado. Log: {log}")
