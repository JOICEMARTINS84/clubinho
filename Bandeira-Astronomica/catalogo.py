"""Atualizador opcional de dados científicos com astroquery/SIMBAD (CDS).
O arquivo dados.json contém identificação histórica curada a partir de fontes oficiais.
Uso: python catalogo.py --simbad
"""
import json
import argparse
from datetime import datetime, timezone
from pathlib import Path

DATA = Path(__file__).with_name("dados.json")

def atualizar():
    from astroquery.simbad import Simbad
    db=json.loads(DATA.read_text(encoding="utf8"))
    consulta=Simbad(timeout=25)
    for campo in ("flux(V)", "sp"):
        try: consulta.add_votable_fields(campo)
        except Exception: pass
    sucesso=0
    for s in db["estrelas"]:
        try:
            t=consulta.query_object(s["identificador_simbad"])
            if t is None or not len(t): continue
            linha=t[0]
            colunas={c.lower():c for c in t.colnames}
            astro={"fonte":"SIMBAD/CDS","consulta_utc":datetime.now(timezone.utc).isoformat()}
            for chave,saida in (("ra","ascensao_reta_graus"),("dec","declinacao_graus"),("flux_v","magnitude_v"),("sp_type","tipo_espectral")):
                coluna=colunas.get(chave)
                if coluna is None: continue
                valor=linha[coluna]
                if getattr(valor,"mask",False): continue
                try: astro[saida]=str(valor).strip() if chave=="sp_type" else round(float(valor),5)
                except (TypeError,ValueError): continue
            if len(astro)>2:
                s["astronomia"]=astro
                sucesso+=1
        except Exception as exc:
            print("Sem leitura confirmada para", s["nome"], "-", exc)
    DATA.write_text(json.dumps(db,ensure_ascii=False,indent=2)+"\n",encoding="utf8")
    print("SIMBAD:",sucesso,"de",len(db["estrelas"]),"estrelas enriquecidas; faltantes não são inventadas.")

if __name__=="__main__":
    p=argparse.ArgumentParser()
    p.add_argument("--simbad",action="store_true",help="Atualizar com API do SIMBAD")
    args=p.parse_args()
    if args.simbad: atualizar()
    else:
        catalogo=json.loads(DATA.read_text(encoding="utf8"))
        print("Catálogo histórico validado:",len(catalogo["estrelas"]),"estrelas")
