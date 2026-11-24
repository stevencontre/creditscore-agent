"""Auditoría descriptiva posterior: no modifica el agente ni sus umbrales."""
import sys, json
from pathlib import Path
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, f1_score, brier_score_loss
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"src"))
from creditscore.simulador import generar_solicitudes
from creditscore.fabrica import features_de
from creditscore.modelo import ModeloRiesgo

def ejecutar():
    s=generar_solicitudes(5000,np.random.default_rng(2026))
    X=np.array([features_de(t) for t in s]); y=np.array([t["_default"] for t in s])
    tr,rest=train_test_split(np.arange(len(y)),test_size=.30,random_state=2026,stratify=y)
    va,te=train_test_split(rest,test_size=.5,random_state=2026,stratify=y[rest])
    modelos=[ModeloRiesgo(l).entrenar(X[tr],y[tr]) for l in [.1,1,10]]
    m=max(modelos,key=lambda m:roc_auc_score(y[va],m.predict_proba(X[va])))
    p=m.predict_proba(X[te]); obs=y[te]
    ingresos=np.array([t["formulario"]["ingresos_mensuales"] for t in s])
    corte=float(np.median(ingresos[tr]))
    filas=[]
    for nombre,mask in [("Total",np.ones(len(te),dtype=bool)),("Ingreso hasta mediana",ingresos[te]<=corte),("Ingreso superior a mediana",ingresos[te]>corte)]:
        a,b=obs[mask],p[mask]; pred=b>=.5
        filas.append(dict(grupo=nombre,n=len(a),positivos=int(a.sum()),auc=float(roc_auc_score(a,b)),f1=float(f1_score(a,pred,zero_division=0)),brier=float(brier_score_loss(a,b)),fnr=float(((a==1)&~pred).sum()/(a==1).sum()),fpr=float(((a==0)&pred).sum()/(a==0).sum())))
    return dict(semilla=2026,corte_ingreso_cop=corte,umbral=.5,nota="Auditoría exploratoria posterior, no prueba de equidad demográfica.",resultados=filas)
if __name__=="__main__":
    r=ejecutar()
    destino=Path(__file__).resolve().parents[1]/"experiments"/"subgrupos_2026.json"
    destino.parent.mkdir(exist_ok=True)
    destino.write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding="utf-8")
    print(json.dumps(r,ensure_ascii=False,indent=2))
