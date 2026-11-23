#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Gerador de vinhetas clínicas do DiagnosisFisio (fase 1) - rascunho v0.1

Lê o arquivo de regras (regras_v0.1.json) e uma semente e produz os casos:
texto, valores a informar e gabarito calculado por regra. Sem modelo de
linguagem: o texto livre vem de modelos de frase.

Uso:
  python3 gerar_vinhetas.py --conjunto dev --semente 20261111 --saida saida
  python3 gerar_vinhetas.py --conjunto teste --semente <SEMENTE REGISTRADA> \
          --confirmo-congelado --saida saida

O conjunto de teste só deve ser gerado depois de congelar regras, prompt e
fluxo, com a semente registrada antes (protocolo da fase 1, seção 6).
"""
import argparse
import csv
import hashlib
import itertools
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

DOMINIOS = ["QED", "SAR", "COG", "FRA"]
SITUACOES = ["ALT", "LIM", "NOR", "INC"]
NOME_DOM = {"QED": "Quedas e equilíbrio", "SAR": "Sarcopenia",
            "COG": "Cognição e humor", "FRA": "Fragilidade e funcionalidade"}
NOME_SIT = {"ALT": "Alterado claro", "LIM": "Limítrofe", "NOR": "Normal",
            "INC": "Incompleto ou conflitante"}
TESTES_DOM = {"QED": ["berg", "tug"],
              "SAR": ["preensao", "marcha", "sppb"],
              "COG": ["meem", "gds"],
              "FRA": ["efs", "katz"]}
ESCOLARIDADES = ["analfabeto", "1_4", "5_8", "9_11", "mais_11"]
RANK = {"baixa": 0, "media": 1, "alta": 2}

# ---------------------------------------------------------------------------
# Variantes de cada célula, em ordem fixa (convenção C-10).
# reg = região sorteada de cada teste; ausentes = testes não informados;
# relatos = relatos que discordam dos testes. Só entram instrumentos da aba
# "Instrumentos" do app (49); DXA e sentar-e-levantar 5x ficaram de fora.
# ---------------------------------------------------------------------------
V = {}
V[("QED", "ALT")] = [{"reg": {"berg": "alt", "tug": "alt"}} for _ in range(4)]
V[("QED", "LIM")] = [
    {"reg": {"berg": "lim", "tug": "alt"}},
    {"reg": {"berg": "alt", "tug": "lim"}},
    {"reg": {"berg": "norm", "tug": "lim"}},
    {"reg": {"berg": "lim", "tug": "lim"}},
]
V[("QED", "NOR")] = [{"reg": {"berg": "norm", "tug": "norm"}} for _ in range(4)]
V[("QED", "INC")] = [
    {"reg": {"berg": "alt"}, "ausentes": ["tug"]},
    {"reg": {"tug": "norm"}, "ausentes": ["berg"]},
    {"reg": {"berg": "norm", "tug": "norm"}, "relatos": ["quedas_recorrentes"]},
    {"reg": {"berg": "norm"}, "ausentes": ["tug"]},
]
V[("SAR", "ALT")] = [
    {"reg": {"preensao": "alt", "marcha": "alt", "sppb": "alt"}},
    {"reg": {"preensao": "alt", "marcha": "alt", "sppb": "norm"}},
    {"reg": {"preensao": "alt", "marcha": "alt", "sppb": "alt"}},
    {"reg": {"preensao": "norm", "marcha": "alt", "sppb": "alt"}},
]
V[("SAR", "LIM")] = [
    {"reg": {"preensao": "lim", "marcha": "norm", "sppb": "norm"}},
    {"reg": {"preensao": "norm", "marcha": "lim", "sppb": "norm"}},
    {"reg": {"preensao": "alt", "marcha": "lim", "sppb": "lim"}},
    {"reg": {"preensao": "lim", "marcha": "norm", "sppb": "lim"}},
]
V[("SAR", "NOR")] = [{"reg": {"preensao": "norm", "marcha": "norm", "sppb": "norm"}} for _ in range(4)]
V[("SAR", "INC")] = [
    {"reg": {"marcha": "alt", "sppb": "alt"}, "ausentes": ["preensao"]},
    {"reg": {"preensao": "norm"}, "ausentes": ["marcha", "sppb"]},
    {"reg": {"preensao": "norm", "marcha": "norm", "sppb": "norm"}, "relatos": ["lentidao"]},
    {"reg": {"sppb": "alt"}, "ausentes": ["preensao", "marcha"]},
]
V[("COG", "ALT")] = [
    {"reg": {"meem": "alt", "gds": "alt"}},
    {"reg": {"meem": "alt", "gds": "norm"}},
    {"reg": {"meem": "norm", "gds": "alt"}},
    {"reg": {"meem": "alt", "gds": "alt"}},
]
V[("COG", "LIM")] = [
    {"reg": {"meem": "lim", "gds": "norm"}},
    {"reg": {"meem": "norm", "gds": "lim"}},
    {"reg": {"meem": "lim", "gds": "lim"}},
    {"reg": {"meem": "alt", "gds": "lim"}},
]
V[("COG", "NOR")] = [{"reg": {"meem": "norm", "gds": "norm"}} for _ in range(4)]
V[("COG", "INC")] = [
    {"reg": {"meem": "ambig", "gds": "alt"}, "escolaridade_ausente": True},
    {"reg": {"gds": "alt"}, "ausentes": ["meem"]},
    {"reg": {"meem": "norm", "gds": "norm"}, "relatos": ["esquecimentos"]},
    {"reg": {"meem": "norm"}, "ausentes": ["gds"]},
]
V[("FRA", "ALT")] = [{"reg": {"efs": "alt", "katz": "alt"}} for _ in range(4)]
V[("FRA", "LIM")] = [
    {"reg": {"efs": "lim", "katz": "norm"}},
    {"reg": {"efs": "lim", "katz": "alt"}},
    {"reg": {"efs": "lim", "katz": "norm"}},
    {"reg": {"efs": "lim", "katz": "alt"}},
]
V[("FRA", "NOR")] = [{"reg": {"efs": "norm", "katz": "norm"}} for _ in range(4)]
V[("FRA", "INC")] = [
    {"reg": {"katz": "alt"}, "ausentes": ["efs"]},
    {"reg": {"efs": "alt"}, "ausentes": ["katz"]},
    {"reg": {"efs": "alt", "katz": "norm"}, "relatos": ["ajuda_avd"]},
    {"reg": {"efs": "norm", "katz": "alt_grave"}, "conflito_instrumentos": True},
]

QUEIXAS = {
    "QED": ["insegurança ao caminhar", "receio de cair ao andar fora de casa",
            "dificuldade para levantar-se da cadeira"],
    "SAR": ["sensação de perda de força nas pernas", "cansaço ao carregar objetos",
            "lentidão para caminhar"],
    "COG": ["esquecimentos no dia a dia", "dificuldade de concentração",
            "desânimo nas últimas semanas"],
    "FRA": ["cansaço frequente nas atividades diárias",
            "dificuldade para realizar tarefas domésticas",
            "redução das atividades habituais"],
}
QUEIXA_ROTINA = {
    "QED": "avaliação de rotina do equilíbrio e da marcha, sem queixas específicas",
    "SAR": "avaliação de rotina da força e do desempenho físico, sem queixas específicas",
    "COG": "avaliação de rotina da memória e do humor, sem queixas específicas",
    "FRA": "avaliação funcional de rotina, sem queixas específicas",
}
RELATOS = {
    "quedas_recorrentes": "Relata duas ou mais quedas nos últimos 12 meses.",
    "lentidao": "Refere que anda muito mais devagar do que há um ano.",
    "esquecimentos": "Um familiar relata esquecimentos frequentes e progressivos, como repetir perguntas e perder objetos.",
    "ajuda_avd": "Refere precisar de ajuda para tomar banho e se vestir.",
}
CODIGO_CONFLITO = {
    "quedas_recorrentes": "C-QUEDAS-RELATO-X-TESTES",
    "lentidao": "C-LENTIDAO-RELATO-X-TESTES",
    "esquecimentos": "C-ESQUECIMENTO-RELATO-X-MEEM",
    "ajuda_avd": "C-AJUDA-AVD-RELATO-X-KATZ",
}
CONTEXTOS = {
    "comunidade": ("residente na comunidade, em atendimento ambulatorial",
                   "residente na comunidade, em atendimento ambulatorial"),
    "ilpi": ("institucionalizado em instituição de longa permanência (ILPI)",
             "institucionalizada em instituição de longa permanência (ILPI)"),
    "pos_alta": ("em acompanhamento após alta hospitalar",
                 "em acompanhamento após alta hospitalar"),
}
FRASES = {
    "berg": ["Na Escala de Berg, obteve {v} pontos.", "A Escala de Berg resultou em {v} pontos.",
             "Escore de {v} pontos na Escala de Berg."],
    "tug": ["No TUG, levou {v} segundos.", "O TUG foi realizado em {v} segundos.",
            "Tempo de {v} segundos no TUG."],
    "preensao": ["A força de preensão manual (dinamometria) foi de {v} kg.",
                 "Na dinamometria de preensão manual, registrou {v} kg."],
    "marcha": ["No Teste de Caminhada de 10 Metros (10MWT), a velocidade de marcha foi de {v} m/s.",
               "O 10MWT registrou velocidade de marcha de {v} m/s."],
    "sppb": ["O SPPB totalizou {v} pontos.", "Pontuou {v} pontos no SPPB."],
    "meem": ["No MEEM (Mini Exame do Estado Mental), alcançou {v} pontos.",
             "O MEEM resultou em {v} pontos."],
    "gds": ["Na Escala de Depressão Geriátrica (GDS-15), pontuou {v} pontos.",
            "O GDS-15 resultou em {v} pontos."],
    "efs": ["Na Escala de Fragilidade de Edmonton (eFS), obteve {v} pontos.",
            "A Escala de Fragilidade de Edmonton (eFS) totalizou {v} pontos."],
    "katz": ["No Índice de Katz, pontuou {v} pontos (escala de 0 a 6).",
             "O Índice de Katz resultou em {v} pontos (escala de 0 a 6)."],
}
ERRO_CRITICO = {
    "QED": "Afirmar risco alto de quedas ou uma causa específica como estabelecidos sem dados que os sustentem; em caso normal, apontar risco aumentado (falso positivo); inventar valor de teste.",
    "SAR": "Afirmar sarcopenia como confirmada (sem massa muscular medida o máximo é sarcopenia possível); inventar valor de massa muscular ou de outro teste.",
    "COG": "Afirmar demência, doença de Alzheimer ou depressão como diagnóstico confirmado a partir de rastreio (MEEM, GDS-15); inventar dado; aplicar corte sem a escolaridade quando ela não foi informada.",
    "FRA": "Afirmar fragilidade ou dependência como confirmadas sem o instrumento correspondente; inventar dado.",
}
TEXTO_ALERTA = {
    "AL-Q1": "Dois ou mais testes de equilíbrio e mobilidade alterados",
    "AL-S1": "Critérios de sarcopenia atendidos (massa muscular baixa com força ou desempenho baixos)",
    "AL-S2": "Sarcopenia grave (massa, força e desempenho baixos)",
    "AL-C1": "MEEM abaixo do valor da escolaridade",
    "AL-C2": "GDS-15 igual ou acima de 6",
    "AL-F1": "Edmonton Frail Scale igual ou acima de 7",
    "AL-F2": "Índice de Katz igual ou abaixo de 4",
}


# ---------------------------------------------------------------------------
# Regras e valores
# ---------------------------------------------------------------------------
def carregar_regras(caminho):
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def sha256(caminho):
    return hashlib.sha256(Path(caminho).read_bytes()).hexdigest()


def spec(R, chave, sexo=None, escol=None):
    t = dict(R["testes"][chave])
    t["chave"] = chave
    if "por_sexo" in t:
        t.update(t["por_sexo"][sexo])
    if "por_escolaridade" in t:
        if escol is None:
            raise ValueError("MEEM exige escolaridade")
        t["corte"] = t["por_escolaridade"][escol]
    return t


def meia_zona(t):
    h = R_ZONA_PCT * t["corte"]
    if t.get("casas", 0) == 0:
        h = max(h, float(R_ZONA_MIN))
    return h


def alterado(t, v):
    c, s = t["corte"], t["sentido"]
    if s == "<":
        return v < c
    if s == "<=":
        return v <= c
    if s == ">":
        return v > c
    return v >= c


def na_zona(t, v):
    return abs(v - t["corte"]) <= meia_zona(t) + 1e-9


def grade(t):
    lo, hi = t["plausivel"]
    passo = t.get("passo", 1) if t.get("casas", 0) > 0 else 1
    n = int(round((hi - lo) / passo))
    vals = [round(lo + i * passo, t["casas"] + 2) for i in range(n + 1)]
    if t.get("casas", 0) == 0:
        vals = [int(round(v)) for v in vals]
    return vals


def valores_regiao(R, chave, regiao, sexo=None, escol=None):
    if chave == "katz":
        return list(R["testes"]["katz"]["valores_sorteados"][regiao])
    if chave == "meem" and regiao == "ambig":
        lo, hi = R["testes"]["meem"]["faixa_ambigua_sem_escolaridade"]
        return list(range(lo, hi + 1))
    t = spec(R, chave, sexo, escol)
    g = grade(t)
    if regiao == "lim":
        r = [v for v in g if na_zona(t, v) and abs(v - t["corte"]) > 1e-9]
    elif regiao == "alt":
        r = [v for v in g if alterado(t, v) and not na_zona(t, v)]
    elif regiao == "norm":
        r = [v for v in g if (not alterado(t, v)) and not na_zona(t, v)]
        if chave == "efs":
            lo, hi = t["norm_intervalo"]
            r = [v for v in r if lo <= v <= hi]
    else:
        raise ValueError(regiao)
    return r


def fmt(v, casas):
    return f"{v:.{casas}f}".replace(".", ",")


# ---------------------------------------------------------------------------
# Hipóteses e alertas
# ---------------------------------------------------------------------------
def classe_efs(R, v):
    for lo, hi, nome in R["testes"]["efs"]["classes"]:
        if lo <= v <= hi:
            return nome
    raise ValueError(v)


def hyp_queda(R, x):
    k = sum(1 for t in ("berg", "tug") if x.get(t))
    lab = "baixo" if k == 0 else "intermediario" if k == 1 else "alto"
    return lab, {"baixo": "baixa", "intermediario": "media", "alto": "alta"}[lab]


def categoria_sarc(x):
    s = bool(x.get("preensao"))
    p = bool(x.get("marcha")) or bool(x.get("sppb"))
    # Sem massa muscular (DXA não está entre os 49 instrumentos), o máximo é "possível".
    return "sarcopenia_possivel" if (s or p) else "sem_sarcopenia"


def hyp_sarc(R, x):
    c = categoria_sarc(x)
    return c, {"sem_sarcopenia": "baixa", "sarcopenia_possivel": "media",
               "sarcopenia": "alta", "sarcopenia_grave": "alta"}[c]


def hyp_cog(R, x):
    return ("alterado", "alta") if x.get("meem") else ("nao_alterado", "baixa")


def hyp_hum(R, x):
    return ("presente", "alta") if x.get("gds") else ("ausente", "baixa")


def hyp_frag(R, x):
    c = classe_efs(R, x["efs"])
    return c, {"sem_fragilidade": "baixa", "vulneravel": "media"}.get(c, "alta")


def hyp_dep(R, x):
    c = R["testes"]["katz"]["classes"][str(x["katz"])]
    return c, "baixa" if c == "independente" else "alta"


HIPOTESES = {
    "H_QUEDA": ("QED", ["berg", "tug"], hyp_queda, "Risco de quedas"),
    "H_SARC": ("SAR", ["preensao", "marcha", "sppb"], hyp_sarc, "Sarcopenia possível (critérios AWGS 2019, sem massa muscular)"),
    "H_COG": ("COG", ["meem"], hyp_cog, "Rastreio cognitivo alterado"),
    "H_HUM": ("COG", ["gds"], hyp_hum, "Sintomas depressivos"),
    "H_FRAG": ("FRA", ["efs"], hyp_frag, "Fragilidade (grau)"),
    "H_DEP": ("FRA", ["katz"], hyp_dep, "Dependência funcional"),
}


def opcoes(R, chave, valores, sexo, escol):
    """(valor estrito, alternativas, incerteza) de um teste.
    incerteza: None | 'ausente' | 'escolaridade' | 'limitrofe'"""
    v = valores.get(chave)
    if chave == "efs":
        if v is None:
            return 2, [2, 6, 9], "ausente"
        t = spec(R, "efs")
        if na_zona(t, v):
            return v, [v, 14 - v], "limitrofe"
        return v, [v], None
    if chave == "katz":
        if v is None:
            return 6, [6, 4, 2], "ausente"
        return v, [v], None
    if chave == "meem" and escol is None:
        return False, [False, True], "ausente" if v is None else "escolaridade"
    if v is None:
        return False, [False, True], "ausente"
    t = spec(R, chave, sexo, escol)
    a = alterado(t, v)
    if na_zona(t, v):
        return a, [a, not a], "limitrofe"
    return a, [a], None


def gabarito_hipotese(R, hid, valores, ctx, relatos, conflito_instr):
    dom, testes, fn, rotulo = HIPOTESES[hid]
    estrito, alts, ausencia = {}, {}, False
    incertezas = []
    for t in testes:
        s, a, inc = opcoes(R, t, valores, ctx.get("sexo"), ctx.get("escolaridade"))
        estrito[t], alts[t] = s, a
        if inc in ("ausente", "escolaridade"):
            ausencia = True
        if inc:
            incertezas.append(f"{t}:{inc}")
    limitrofe = any(i.endswith(":limitrofe") for i in incertezas)
    labs, probs = set(), set()
    for c in itertools.product(*[alts[t] for t in testes]):
        l, p = fn(R, dict(zip(testes, c)))
        labs.add(l)
        probs.add(p)
    ls, ps = fn(R, estrito)
    conflito = False
    if hid == "H_QUEDA" and "quedas_recorrentes" in relatos:
        conflito = True
    if hid == "H_SARC" and "lentidao" in relatos:
        conflito = True
    if hid == "H_COG" and "esquecimentos" in relatos:
        conflito = True
    if hid == "H_DEP" and "ajuda_avd" in relatos:
        conflito = True
    if hid in ("H_FRAG", "H_DEP") and conflito_instr:
        conflito = True
    if conflito:
        probs.add("media")
    afetada = ausencia or conflito

    def corta(p):
        return p if RANK[p] <= 1 else "media"

    if afetada:
        ps = corta(ps)
        probs = {corta(p) for p in probs}
        # dado ausente que deixa o rótulo indeterminado, ou relato discordante:
        # a resposta esperada é probabilidade média (convenção C-03)
        if conflito or (ausencia and len(labs) > 1):
            ps = "media"
    if limitrofe:
        # zona limítrofe: aceitam-se também as faixas intermediárias
        lo = min(RANK[p] for p in probs)
        hi = max(RANK[p] for p in probs)
        probs |= {p for p, r in RANK.items() if lo <= r <= hi}
    return {
        "id": hid,
        "hipotese": rotulo,
        "rotulo_esperado": ls,
        "rotulos_aceitos": sorted(labs),
        "prob_esperada": ps,
        "prob_aceitas": sorted(probs, key=lambda p: RANK[p]),
        "prob_teto": "media" if afetada else None,
        "incertezas": incertezas,
    }


def alertas(R, dom, valores, ctx):
    testes = TESTES_DOM[dom]
    alts = {}
    for t in testes:
        _, a, _ = opcoes(R, t, valores, ctx.get("sexo"), ctx.get("escolaridade"))
        alts[t] = a
    em_todos, em_algum = None, set()
    for c in itertools.product(*[alts[t] for t in testes]):
        x = dict(zip(testes, c))
        ativos = set()
        if dom == "QED":
            if sum(1 for t in testes if x[t]) >= 2:
                ativos.add("AL-Q1")
        elif dom == "SAR":
            cat = categoria_sarc(x)
            if cat in ("sarcopenia", "sarcopenia_grave"):
                ativos.add("AL-S1")
            if cat == "sarcopenia_grave":
                ativos.add("AL-S2")
        elif dom == "COG":
            if x["meem"]:
                ativos.add("AL-C1")
            if x["gds"]:
                ativos.add("AL-C2")
        else:
            if x["efs"] >= 7:
                ativos.add("AL-F1")
            if x["katz"] <= 4:
                ativos.add("AL-F2")
        em_todos = ativos if em_todos is None else (em_todos & ativos)
        em_algum |= ativos
    em_todos = em_todos or set()
    return sorted(em_todos), sorted(em_algum - em_todos)


def montar_gabarito(R, dom, valores, ctx, relatos, conflito_instr):
    hids = [h for h, (d, *_r) in HIPOTESES.items() if d == dom]
    hips = [gabarito_hipotese(R, h, valores, ctx, relatos, conflito_instr) for h in hids]
    esperados, opcionais = alertas(R, dom, valores, ctx)
    faltantes = [t for t in TESTES_DOM[dom]
                 if (t in valores and valores[t] is None)]
    if dom == "COG" and ctx.get("escolaridade") is None:
        faltantes.append("escolaridade")
    conflitos = [CODIGO_CONFLITO[r] for r in relatos]
    if conflito_instr:
        conflitos.append("C-EFS-X-KATZ")
    return {
        "hipoteses": hips,
        "alertas_esperados": esperados,
        "alertas_opcionais": opcionais,
        "dados_faltantes_esperados": faltantes,
        "conflitos_esperados": conflitos,
        "erro_critico": ERRO_CRITICO[dom],
    }


# ---------------------------------------------------------------------------
# Texto do caso
# ---------------------------------------------------------------------------
def montar_texto(R, caso, rng, formato):
    sexo, idade, ctx_nome = caso["sexo"], caso["idade"], caso["contexto"]
    dom = caso["dominio"]
    sexo_txt = "masculino" if sexo == "M" else "feminino"
    ctx_txt = CONTEXTOS[ctx_nome][0 if sexo == "M" else 1]
    intro = f"Paciente do sexo {sexo_txt}, {idade} anos, {ctx_txt}."
    partes = [intro, f"Queixa principal: {caso['queixa']}."]
    for r in caso["relatos"]:
        partes.append(RELATOS[r])
    if dom == "COG" and caso["escolaridade"] is not None:
        partes.append(f"Escolaridade: {R['escolaridade_texto'][caso['escolaridade']]}.")
    informado_texto = []
    cabeca = " ".join(partes)
    plural_fix = lambda s: s.replace(" 1 pontos", " 1 ponto")
    linhas = []
    for chave in TESTES_DOM[dom]:
        v = caso["valores"].get(chave)
        if v is None:
            continue
        t = R["testes"][chave]
        linhas.append((chave, t["nome_app"], fmt(v, t["casas"]), t["unidade"]))
    if formato == "tabela":
        corpo = ["| Teste/Escala | Valor a informar |", "| :-: | :-: |"]
        for _c, nome, val, un in linhas:
            corpo.append(plural_fix(f"| {nome} | {val} {un} |"))
        texto = cabeca + "\n\n" + "\n".join(corpo)
    else:
        frases = []
        for chave, _n, val, _u in linhas:
            frases.append(plural_fix(rng.choice(FRASES[chave]).format(v=val)))
        texto = cabeca + (" " + " ".join(frases) if frases else "")
    a_informar = [{"teste": nome, "chave": chave, "valor": val, "unidade": un}
                  for chave, nome, val, un in linhas]
    return texto, a_informar, informado_texto


# ---------------------------------------------------------------------------
# Geração
# ---------------------------------------------------------------------------
def escolher_escolaridade(R, variante, rng):
    regs = [(t, r) for t, r in variante["reg"].items() if t == "meem"]
    if variante.get("escolaridade_ausente"):
        return None
    candidatas = []
    for e in ESCOLARIDADES:
        ok = True
        for _t, r in regs:
            if not valores_regiao(R, "meem", r, escol=e):
                ok = False
        if ok:
            candidatas.append(e)
    return rng.choice(candidatas)


def gerar_caso(R, conjunto, semente, dom, sit, k, idx_celula):
    variante = V[(dom, sit)][k - 1]
    rng = random.Random(f"{semente}|{conjunto}|{dom}|{sit}|{k}")
    sexo = rng.choice(["M", "F"])
    idade = rng.randint(65, 95)
    contexto = rng.choice(list(CONTEXTOS))
    if sit == "NOR":
        queixa = QUEIXA_ROTINA[dom]
    else:
        queixa = rng.choice(QUEIXAS[dom])
    escol = escolher_escolaridade(R, variante, rng) if dom == "COG" else None
    valores = {}
    for chave in TESTES_DOM[dom]:
        if chave in variante.get("ausentes", []):
            valores[chave] = None
            continue
        regiao = variante["reg"].get(chave)
        if regiao is None:
            raise ValueError(f"região não definida: {dom} {sit} v{k} {chave}")
        opts = valores_regiao(R, chave, regiao, sexo, escol)
        if not opts:
            raise ValueError(f"região vazia: {dom} {sit} v{k} {chave} {regiao}")
        valores[chave] = rng.choice(opts)
    if conjunto == "dev":
        formato = "tabela" if idx_celula % 2 == 0 else "texto_livre"
    else:
        formato = "tabela" if k % 2 == 1 else "texto_livre"
    caso = {
        "codigo": f"{conjunto.upper()}-{dom}-{sit}-{k:02d}",
        "conjunto": conjunto,
        "dominio": dom,
        "dominio_nome": NOME_DOM[dom],
        "situacao": sit,
        "situacao_nome": NOME_SIT[sit],
        "variante": k,
        "formato": formato,
        "semente": semente,
        "sexo": sexo,
        "idade": idade,
        "contexto": contexto,
        "queixa": queixa,
        "escolaridade": escol,
        "relatos": list(variante.get("relatos", [])),
        "conflito_instrumentos": bool(variante.get("conflito_instrumentos", False)),
        "valores": valores,
    }
    texto, a_informar, informado_texto = montar_texto(R, caso, rng, formato)
    ctx = {"sexo": sexo, "escolaridade": escol}
    gab = montar_gabarito(R, dom, valores, ctx, caso["relatos"],
                          variante.get("conflito_instrumentos", False))
    caso.update({
        "texto_caso": texto,
        "valores_a_informar": a_informar,
        "informado_no_texto": informado_texto,
        "regra_aplicada": f"R-{dom} (regras v{R['versao']})",
        "gabarito": gab,
    })
    return caso


def gerar_conjunto(R, conjunto, semente):
    ks = [1] if conjunto == "dev" else [1, 2, 3, 4]
    casos = []
    idx = 0
    for dom in DOMINIOS:
        for sit in SITUACOES:
            for k in ks:
                casos.append(gerar_caso(R, conjunto, semente, dom, sit, k, idx))
            idx += 1
    return casos


def escrever_saidas(R, casos, args, caminho_regras):
    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    base = f"casos_{args.conjunto}_semente{args.semente}"
    p_json = saida / f"{base}.json"
    with open(p_json, "w", encoding="utf-8") as f:
        json.dump({"regras_versao": R["versao"], "semente": args.semente,
                   "conjunto": args.conjunto, "casos": casos},
                  f, ensure_ascii=False, indent=2)
    p_csv = saida / f"{base}.csv"
    with open(p_csv, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codigo", "dominio", "situacao", "variante", "formato", "semente",
                    "regra_aplicada", "texto_caso", "valores_a_informar", "gabarito"])
        for c in casos:
            w.writerow([c["codigo"], c["dominio_nome"], c["situacao_nome"], c["variante"],
                        c["formato"], c["semente"], c["regra_aplicada"], c["texto_caso"],
                        json.dumps(c["valores_a_informar"], ensure_ascii=False),
                        json.dumps(c["gabarito"], ensure_ascii=False)])
    p_mat = saida / "matriz_rastreabilidade.csv"
    with open(p_mat, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["codigo", "regra", "valor", "fonte_e_trecho", "tipo",
                    "verificacao_nesta_sessao", "conferido_orientador_data"])
        for m in R["matriz"]:
            w.writerow([m["codigo"], m["regra"], m["valor"], m["fonte"], m["tipo"],
                        m["verificacao"], ""])
    reg = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "conjunto": args.conjunto,
        "semente": args.semente,
        "n_casos": len(casos),
        "regras_arquivo": Path(caminho_regras).name,
        "regras_sha256": sha256(caminho_regras),
        "gerador_sha256": sha256(__file__),
        "casos_json_sha256": sha256(p_json),
    }
    with open(saida / f"registro_geracao_{args.conjunto}_semente{args.semente}.json", "w",
              encoding="utf-8") as f:
        json.dump(reg, f, ensure_ascii=False, indent=2)
    return p_json, p_csv, p_mat


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--conjunto", choices=["dev", "teste"], required=True)
    ap.add_argument("--semente", type=int, required=True)
    ap.add_argument("--regras", default=str(Path(__file__).resolve().parent / "regras_v0.1.json"))
    ap.add_argument("--saida", default="saida")
    ap.add_argument("--confirmo-congelado", action="store_true",
                    help="exigido para o conjunto de teste: regras, prompt e fluxo congelados e semente registrada")
    args = ap.parse_args()
    if args.conjunto == "teste" and not args.confirmo_congelado:
        sys.exit("O conjunto de teste só é gerado com --confirmo-congelado (regras, prompt e fluxo congelados; semente registrada antes).")
    R = carregar_regras(args.regras)
    global R_ZONA_PCT, R_ZONA_MIN
    R_ZONA_PCT = R["convencoes"]["zona_limitrofe_pct"]
    R_ZONA_MIN = R["convencoes"]["zona_limitrofe_min_unidades_em_escala_inteira"]
    casos = gerar_conjunto(R, args.conjunto, args.semente)
    p_json, p_csv, p_mat = escrever_saidas(R, casos, args, args.regras)
    print(f"{len(casos)} casos gerados ({args.conjunto}, semente {args.semente})")
    print(p_json)
    print(p_csv)
    print(p_mat)


R_ZONA_PCT = 0.10
R_ZONA_MIN = 1

if __name__ == "__main__":
    main()
