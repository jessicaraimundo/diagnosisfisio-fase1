#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verificador dos casos gerados (etapa 3, conferência automática) - rascunho v0.1

Escrito separadamente do gerador: não importa nenhum código dele. Lê só o
arquivo de regras e o arquivo de casos; recalcula o gabarito de cada caso com
frações exatas e tabelas de decisão, e compara com o gabarito gravado. Também
faz verificações estruturais (escalas, corte exato, estrato, texto x valores,
vazamento do diagnóstico no texto, cobertura das células).

Uso:
  python3 verificar_vinhetas.py --casos saida/casos_dev_semente20261111.json \
       --regras regras_v0.1.json [--regerar]

Limite declarado: o verificador e o gerador foram escritos pelo mesmo autor
(com a mesma assistência de IA) a partir das mesmas regras. A independência é
de código, não de pessoa.
"""
import argparse
import itertools
import json
import re
import subprocess
import sys
import tempfile
from collections import Counter
from fractions import Fraction as Fr
from pathlib import Path

DOMINIOS = ["QED", "SAR", "COG", "FRA"]
SITUACOES = ["ALT", "LIM", "NOR", "INC"]
TESTES = {"QED": ["berg", "tug"], "SAR": ["preensao", "marcha", "sppb"],
          "COG": ["meem", "gds"], "FRA": ["efs", "katz"]}
ORDEM = {"baixa": 0, "media": 1, "alta": 2}
PALAVRA = {"berg": "Berg", "tug": "TUG", "preensao": "preensão",
           "marcha": "10MWT", "sppb": "SPPB", "meem": "MEEM", "gds": "GDS",
           "efs": "Edmonton", "katz": "Katz"}
VAZAMENTO = ["sarcopeni", "fragil", "demênc", "alzheimer", "depress", "diagnóst", "normal",
             "alterad", "risco", "vulnerab", "dependênc"]
NOMES_PERMITIDOS = ["Escala de Fragilidade de Edmonton", "Escala de Depressão Geriátrica"]


def fr(x):
    return Fr(str(x))


# ---------------------------------------------------------------------------
class Regras:
    def __init__(self, caminho):
        self.d = json.loads(Path(caminho).read_text(encoding="utf-8"))
        self.pct = fr(self.d["convencoes"]["zona_limitrofe_pct"])
        self.minimo = fr(self.d["convencoes"]["zona_limitrofe_min_unidades_em_escala_inteira"])

    def corte(self, t, sexo, escol):
        e = self.d["testes"][t]
        if "por_sexo" in e:
            return fr(e["por_sexo"][sexo]["corte"])
        if "por_escolaridade" in e:
            return None if escol is None else fr(e["por_escolaridade"][escol])
        return fr(e["corte"])

    def plausivel(self, t, sexo):
        e = self.d["testes"][t]
        if "por_sexo" in e:
            return [fr(x) for x in e["por_sexo"][sexo]["plausivel"]]
        return [fr(x) for x in e["plausivel"]]

    def meia_zona(self, t, c):
        h = self.pct * c
        if self.d["testes"][t].get("casas", 0) == 0:
            h = max(h, self.minimo)
        return h

    def alterado(self, t, v, c):
        s = self.d["testes"][t]["sentido"]
        return {"<": v < c, "<=": v <= c, ">": v > c, ">=": v >= c}[s]


def estado(R, t, v, sexo, escol):
    """'aus' | 'esc' (sem escolaridade) | (alterado:bool, limitrofe:bool)"""
    if v is None:
        return "aus"
    if t == "meem" and escol is None:
        return "esc"
    c = R.corte(t, sexo, escol)
    v = fr(v)
    return (R.alterado(t, v, c), abs(v - c) <= R.meia_zona(t, c))


# ---------------------------------------------------------------------------
# Tabelas de decisão (reescritas, sem reaproveitar o gerador)
TAB_QUEDA = {0: ("baixo", "baixa"), 1: ("intermediario", "media"), 2: ("alto", "alta")}
# Sem DXA (fora dos 49 instrumentos do app), a sarcopenia só pode ser "possível" ou ausente.
TAB_SARC = {(sf, pf): (("sarcopenia_possivel", "media") if (sf or pf) else ("sem_sarcopenia", "baixa"))
            for sf, pf in itertools.product([False, True], repeat=2)}
TAB_COG = {True: ("alterado", "alta"), False: ("nao_alterado", "baixa")}
TAB_HUM = {True: ("presente", "alta"), False: ("ausente", "baixa")}


def classe_efs(R, v):
    for lo, hi, nome in R.d["testes"]["efs"]["classes"]:
        if lo <= v <= hi:
            return nome
    raise ValueError(v)


PROB_FRAG = {"sem_fragilidade": "baixa", "vulneravel": "media", "leve": "alta", "moderada": "alta", "grave": "alta"}


def mundos(R, t, v, sexo, escol):
    """(mundo estrito, lista de mundos possíveis, tipos de incerteza)."""
    if t == "efs":
        if v is None:
            return 2, [2, 6, 9], {"aus"}
        c = fr(R.d["testes"]["efs"]["corte"])
        if abs(fr(v) - c) <= R.meia_zona("efs", c):
            return v, [v, int(2 * c - v)], {"lim"}
        return v, [v], set()
    if t == "katz":
        if v is None:
            return 6, [6, 4, 2], {"aus"}
        return v, [v], set()
    e = estado(R, t, v, sexo, escol)
    if e == "aus":
        return False, [False, True], {"aus"}
    if e == "esc":
        return False, [False, True], {"aus"}
    alt, lim = e
    return alt, ([alt, not alt] if lim else [alt]), ({"lim"} if lim else set())


def avaliar(R, hid, x):
    if hid == "H_QUEDA":
        return TAB_QUEDA[sum(1 for t in ("berg", "tug") if x[t])]
    if hid == "H_SARC":
        return TAB_SARC[(bool(x["preensao"]), bool(x["marcha"]) or bool(x["sppb"]))]
    if hid == "H_COG":
        return TAB_COG[bool(x["meem"])]
    if hid == "H_HUM":
        return TAB_HUM[bool(x["gds"])]
    if hid == "H_FRAG":
        c = classe_efs(R, x["efs"])
        return c, PROB_FRAG[c]
    if hid == "H_DEP":
        c = R.d["testes"]["katz"]["classes"][str(x["katz"])]
        return c, ("baixa" if c == "independente" else "alta")
    raise KeyError(hid)


HIP_DOM = {"H_QUEDA": ("QED", ["berg", "tug"]),
           "H_SARC": ("SAR", ["preensao", "marcha", "sppb"]),
           "H_COG": ("COG", ["meem"]), "H_HUM": ("COG", ["gds"]),
           "H_FRAG": ("FRA", ["efs"]), "H_DEP": ("FRA", ["katz"])}
RELATO_HIP = {"quedas_recorrentes": "H_QUEDA", "lentidao": "H_SARC",
              "esquecimentos": "H_COG", "ajuda_avd": "H_DEP"}
CONFLITO_COD = {"quedas_recorrentes": "C-QUEDAS-RELATO-X-TESTES", "lentidao": "C-LENTIDAO-RELATO-X-TESTES",
                "esquecimentos": "C-ESQUECIMENTO-RELATO-X-MEEM", "ajuda_avd": "C-AJUDA-AVD-RELATO-X-KATZ"}


def recalcular(R, c):
    dom, val = c["dominio"], c["valores"]
    sexo, escol = c["sexo"], c["escolaridade"]
    relatos, conf_instr = c["relatos"], c.get("conflito_instrumentos", False)
    hips = []
    for hid, (d, ts) in HIP_DOM.items():
        if d != dom:
            continue
        estrito, mund, tipos = {}, {}, set()
        for t in ts:
            s, m, tp = mundos(R, t, val.get(t), sexo, escol)
            estrito[t], mund[t] = s, m
            tipos |= tp
        rots, probs = set(), set()
        for comb in itertools.product(*[mund[t] for t in ts]):
            r, p = avaliar(R, hid, dict(zip(ts, comb)))
            rots.add(r)
            probs.add(p)
        r0, p0 = avaliar(R, hid, estrito)
        conflito = any(RELATO_HIP[r] == hid for r in relatos) or (conf_instr and hid in ("H_FRAG", "H_DEP"))
        ausencia = "aus" in tipos
        if conflito:
            probs.add("media")
        clip = lambda p: p if ORDEM[p] <= 1 else "media"
        if ausencia or conflito:
            p0 = clip(p0)
            probs = {clip(p) for p in probs}
            if conflito or (ausencia and len(rots) > 1):
                p0 = "media"
        if "lim" in tipos:
            lo, hi = min(ORDEM[p] for p in probs), max(ORDEM[p] for p in probs)
            probs |= {p for p, o in ORDEM.items() if lo <= o <= hi}
        hips.append({"id": hid, "rotulo_esperado": r0, "rotulos_aceitos": sorted(rots),
                     "prob_esperada": p0, "prob_aceitas": sorted(probs, key=lambda p: ORDEM[p]),
                     "prob_teto": "media" if (ausencia or conflito) else None})
    # alertas
    ts = TESTES[dom]
    mund = {t: mundos(R, t, val.get(t), sexo, escol)[1] for t in ts}
    todos, algum = None, set()
    for comb in itertools.product(*[mund[t] for t in ts]):
        x = dict(zip(ts, comb))
        a = set()
        if dom == "QED" and sum(1 for t in ts if x[t]) >= 2:
            a.add("AL-Q1")
        if dom == "SAR":
            cat = TAB_SARC[(bool(x["preensao"]), bool(x["marcha"]) or bool(x["sppb"]))][0]
            if cat in ("sarcopenia", "sarcopenia_grave"):
                a.add("AL-S1")
            if cat == "sarcopenia_grave":
                a.add("AL-S2")
        if dom == "COG":
            if x["meem"]:
                a.add("AL-C1")
            if x["gds"]:
                a.add("AL-C2")
        if dom == "FRA":
            if x["efs"] >= 7:
                a.add("AL-F1")
            if x["katz"] <= 4:
                a.add("AL-F2")
        todos = a if todos is None else todos & a
        algum |= a
    todos = todos or set()
    faltantes = [t for t in ts if t in val and val[t] is None]
    if dom == "COG" and escol is None:
        faltantes.append("escolaridade")
    conflitos = [CONFLITO_COD[r] for r in relatos] + (["C-EFS-X-KATZ"] if conf_instr else [])
    return {"hips": {h["id"]: h for h in hips}, "alertas_esperados": sorted(todos),
            "alertas_opcionais": sorted(algum - todos), "dados_faltantes_esperados": faltantes,
            "conflitos_esperados": conflitos}


def comparar(c, rec):
    erros = []
    g = c["gabarito"]
    gh = {h["id"]: h for h in g["hipoteses"]}
    if set(gh) != set(rec["hips"]):
        erros.append(f"hipóteses diferentes: {sorted(gh)} x {sorted(rec['hips'])}")
    for hid, r in rec["hips"].items():
        h = gh.get(hid)
        if not h:
            continue
        for campo in ("rotulo_esperado", "prob_esperada", "prob_teto"):
            if h[campo] != r[campo]:
                erros.append(f"{hid}.{campo}: gravado {h[campo]!r} x recalculado {r[campo]!r}")
        for campo in ("rotulos_aceitos", "prob_aceitas"):
            if sorted(h[campo]) != sorted(r[campo]):
                erros.append(f"{hid}.{campo}: gravado {h[campo]} x recalculado {r[campo]}")
    for campo in ("alertas_esperados", "alertas_opcionais", "dados_faltantes_esperados", "conflitos_esperados"):
        if sorted(g[campo]) != sorted(rec[campo]):
            erros.append(f"{campo}: gravado {g[campo]} x recalculado {rec[campo]}")
    return erros


# ---------------------------------------------------------------------------
def numero_texto(v, casas):
    return f"{float(v):.{casas}f}".replace(".", ",")


def checagens_estruturais(R, c):
    erros = []
    dom, sit, val = c["dominio"], c["situacao"], c["valores"]
    sexo, escol = c["sexo"], c["escolaridade"]
    # escalas e plausibilidade, valor exato no corte
    estados = {}
    for t, v in val.items():
        if v is None:
            estados[t] = "aus"
            continue
        e = R.d["testes"][t]
        lo, hi = [fr(x) for x in e["escala"]]
        if not (lo <= fr(v) <= hi):
            erros.append(f"{t}={v} fora da escala {lo}-{hi}")
        if t == "katz":
            estados[t] = (fr(v) <= 4, False)
            if fr(v) in (5, 3):
                erros.append("Katz 5 ou 3 não deveria ser sorteado")
            continue
        if t == "meem" and escol is None:
            estados[t] = "esc"
            continue
        c_ = R.corte(t, sexo, escol)
        if t != "efs":
            plo, phi = R.plausivel(t, sexo)
            if not (plo <= fr(v) <= phi):
                erros.append(f"{t}={v} fora da faixa de plausibilidade")
        if fr(v) == c_:
            erros.append(f"{t}={v} igual ao corte")
        estados[t] = estado(R, t, v, sexo, escol)
    # estrato
    pres = {t: s for t, s in estados.items() if s not in ("aus", "esc")}
    tem_lim = any(s[1] for s in pres.values())
    tem_alt = any(s[0] and not s[1] for s in pres.values())
    todos_norm = all((not s[0]) and (not s[1]) for s in pres.values())
    incompleto = (any(s in ("aus", "esc") for s in estados.values()) or bool(c["relatos"])
                  or c.get("conflito_instrumentos", False))
    if sit == "NOR" and not (todos_norm and not incompleto):
        erros.append("NOR: nem todos os valores são normais fora da zona, ou há dado ausente/relato")
    if sit == "ALT" and not (tem_alt and not tem_lim and not incompleto):
        erros.append("ALT: sem valor alterado claro, ou há valor limítrofe/ausente/relato")
    if sit == "LIM" and not (tem_lim and not incompleto):
        erros.append("LIM: sem valor limítrofe, ou há dado ausente/relato")
    if sit == "INC" and not incompleto:
        erros.append("INC: nada ausente ou conflitante")
    # EFS normal só de 0 a 4 (convenção C-06); EFS 5 nunca
    if val.get("efs") == 5:
        erros.append("EFS 5 não é sorteado (C-06)")
    # texto x valores
    txt = c["texto_caso"]
    for t, v in val.items():
        e = R.d["testes"][t]
        if v is None:
            if PALAVRA[t].lower() in txt.lower():
                erros.append(f"{t} ausente, mas o texto menciona '{PALAVRA[t]}'")
            continue
        s = numero_texto(v, e["casas"])
        if not re.search(r"(?<![\d,])" + re.escape(s) + r"(?![\d]|,\d)", txt):
            erros.append(f"valor de {t} ({s}) não aparece no texto")
    if escol is None and dom == "COG" and "escolaridade" in txt.lower():
        erros.append("escolaridade ausente, mas o texto a menciona")
    if escol is not None and dom == "COG":
        if R.d["escolaridade_texto"][escol] not in txt:
            erros.append("escolaridade informada não aparece no texto")
    for r in c["relatos"]:
        pass  # a presença do relato é conferida pelo comparador de conflitos
    # formato
    tem_tabela = "| Teste/Escala |" in txt
    if c["formato"] == "tabela" and not tem_tabela:
        erros.append("formato 'tabela' sem tabela")
    if c["formato"] == "texto_livre" and "|" in txt:
        erros.append("formato 'texto_livre' com tabela")
    # vazamento do diagnóstico
    limpo = txt
    for n in NOMES_PERMITIDOS:
        limpo = limpo.replace(n, "")
    for pal in VAZAMENTO:
        if pal in limpo.lower():
            erros.append(f"texto contém termo que pode vazar o gabarito: '{pal}'")
    # valores_a_informar coerentes com os valores
    inf = {i["chave"]: i["valor"] for i in c["valores_a_informar"]}
    for t, v in val.items():
        if v is None and t in inf:
            erros.append(f"{t} ausente, mas está em valores_a_informar")
        if v is not None and t not in inf:
            erros.append(f"{t} presente, mas não está em valores_a_informar")
    return erros


def checagens_conjunto(casos, conjunto):
    erros = []
    por_celula = Counter((c["dominio"], c["situacao"]) for c in casos)
    esperado = 1 if conjunto == "dev" else 4
    for d in DOMINIOS:
        for s in SITUACOES:
            if por_celula[(d, s)] != esperado:
                erros.append(f"célula {d}-{s}: {por_celula[(d, s)]} casos (esperado {esperado})")
    codigos = Counter(c["codigo"] for c in casos)
    for k, n in codigos.items():
        if n > 1:
            erros.append(f"código repetido: {k}")
    fmt = Counter(c["formato"] for c in casos)
    if conjunto == "dev" and (fmt["tabela"] != 8 or fmt["texto_livre"] != 8):
        erros.append(f"formatos no conjunto dev: {dict(fmt)} (esperado 8/8)")
    if conjunto == "teste":
        for d in DOMINIOS:
            for s in SITUACOES:
                f = Counter(c["formato"] for c in casos if (c["dominio"], c["situacao"]) == (d, s))
                if f["tabela"] != 2 or f["texto_livre"] != 2:
                    erros.append(f"célula {d}-{s}: formatos {dict(f)} (esperado 2/2)")
    return erros


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--casos", required=True)
    ap.add_argument("--regras", required=True)
    ap.add_argument("--regerar", action="store_true",
                    help="regera o conjunto com o gerador e compara o conteúdo (reprodutibilidade)")
    args = ap.parse_args()
    R = Regras(args.regras)
    # Só instrumentos da aba "Instrumentos" do app (49): cada teste das regras precisa estar mapeado a um deles.
    sem_mapa = [t for t, e in R.d["testes"].items() if "instrumento_app" not in e]
    fora = sorted(set(R.d["testes"]) - {"berg", "tug", "preensao", "marcha", "sppb", "meem", "gds", "efs", "katz"})
    if sem_mapa or fora:
        print("[REGRAS] teste sem instrumento do app ou fora da lista permitida:", sem_mapa, fora)
        sys.exit(1)
    dados = json.loads(Path(args.casos).read_text(encoding="utf-8"))
    casos = dados["casos"]
    total_erros = 0
    print(f"Verificando {len(casos)} casos ({dados['conjunto']}, semente {dados['semente']}, regras v{dados['regras_versao']})")
    for c in casos:
        errs = comparar(c, recalcular(R, c)) + checagens_estruturais(R, c)
        if errs:
            total_erros += len(errs)
            print(f"[REPROVADO] {c['codigo']}")
            for e in errs:
                print("   -", e)
    erros_c = checagens_conjunto(casos, dados["conjunto"])
    for e in erros_c:
        print("[CONJUNTO]", e)
    total_erros += len(erros_c)
    if args.regerar:
        gerador = Path(__file__).resolve().parent / "gerar_vinhetas.py"
        with tempfile.TemporaryDirectory() as tmp:
            cmd = [sys.executable, str(gerador), "--conjunto", dados["conjunto"], "--semente",
                   str(dados["semente"]), "--regras", args.regras, "--saida", tmp]
            if dados["conjunto"] == "teste":
                cmd.append("--confirmo-congelado")
            subprocess.run(cmd, check=True, capture_output=True)
            novo = json.loads((Path(tmp) / f"casos_{dados['conjunto']}_semente{dados['semente']}.json")
                              .read_text(encoding="utf-8"))
        if novo["casos"] != casos:
            print("[REPRODUTIBILIDADE] a regeração com a mesma semente deu casos diferentes")
            total_erros += 1
        else:
            print("Reprodutibilidade: a mesma semente gerou exatamente os mesmos casos.")
    print()
    print("Distribuição dos gabaritos (rótulo esperado por hipótese):")
    dist = Counter()
    for c in casos:
        for h in c["gabarito"]["hipoteses"]:
            dist[(h["id"], h["rotulo_esperado"], h["prob_esperada"])] += 1
    for k in sorted(dist):
        print(f"   {k[0]:8s} {k[1]:20s} {k[2]:6s} {dist[k]}")
    print()
    if total_erros:
        print(f"RESULTADO: {total_erros} problema(s). Corrigir regra ou gerador, não o caso isolado.")
        sys.exit(1)
    print(f"RESULTADO: {len(casos)} casos aprovados na conferência automática.")


if __name__ == "__main__":
    main()
