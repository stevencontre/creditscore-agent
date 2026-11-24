"""Experimento sintético: selección por validación, prueba independiente."""
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score, f1_score, brier_score_loss
from sklearn.model_selection import train_test_split
from .simulador import generar_solicitudes
from .fabrica import features_de
from .modelo import ModeloRiesgo

def comparar(semilla=2026):
    s=generar_solicitudes(5000,np.random.default_rng(semilla))
    X=np.array([features_de(t) for t in s]); y=np.array([t["_default"] for t in s])
    tr,rest=train_test_split(np.arange(len(y)),test_size=.30,random_state=semilla,stratify=y)
    va,te=train_test_split(rest,test_size=.5,random_state=semilla,stratify=y[rest])
    filas=[]; errores=[]
    for nombre, candidatos in [
        ("Regresión logística", [(str(l),ModeloRiesgo(l)) for l in [.1,1,10]]),
        ("Random Forest", [(str(d),RandomForestClassifier(n_estimators=100,max_depth=d,random_state=semilla,n_jobs=1)) for d in [4,8,12]])]:
        def fit(m):
            return m.entrenar(X[tr],y[tr]) if isinstance(m,ModeloRiesgo) else m.fit(X[tr],y[tr])
        def pred(m,idx):
            p=m.predict_proba(X[idx]); return p if p.ndim==1 else p[:,1]
        opciones=[(roc_auc_score(y[va],pred(fit(m),va)),param,m) for param,m in candidatos]
        auc,param,m=max(opciones,key=lambda t:t[0])
        p=pred(m,te)
        filas.append({"Modelo":nombre,"Parámetro":param,"AUC validación":auc,"AUC prueba":roc_auc_score(y[te],p),"F1 (0.5)":f1_score(y[te],p>=.5),"Brier":brier_score_loss(y[te],p)})
        for i,prob in zip(te,p):
            if int(prob>=.5)!=y[i]:
                errores.append({"Modelo":nombre,"Caso":s[i]["id"],"Observado":int(y[i]),"Probabilidad":float(prob),"Tipo":"Falso positivo" if prob>=.5 else "Falso negativo"})
    p=np.full(len(te),y[tr].mean())
    filas.insert(0,{"Modelo":"Frecuencia histórica","Parámetro":"—","AUC validación":.5,"AUC prueba":.5,"F1 (0.5)":f1_score(y[te],p>=.5),"Brier":brier_score_loss(y[te],p)})
    return filas,errores
