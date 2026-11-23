#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Plano de execuções da fase 1 do DiagnosisFisio - rascunho v0.1

Monta a lista das 384 execuções (64 casos x 3 repetições x 2 condições) em
ordem embaralhada e dividida em sessões (dias). Não chama nenhum modelo e não
lê o conteúdo dos casos: usa só os códigos (TESTE-<DOM>-<SIT>-<01..04>).

Regras do plano:
  - As duas condições (A e B) de um mesmo caso e repetição ficam na MESMA
    sessão, em ordem aleatória (A antes de B ou B antes de A), para que
    mudanças entre dias (modelo, cota) não se confundam com a condição.
  - Cada sessão recebe o mesmo número de pares (caso x repetição), com os
    16 estratos (4 domínios x 4 situações) distribuídos por igual.
  - Cada execução tem um sessionId próprio e fixo (conversa nova).
  - A semente do plano é DIFERENTE da semente dos casos e deve ser registrada
    antes de gerar o plano.

Uso:
  python3 plano_execucoes.py --semente <SEMENTE_DO_PLANO> --sessoes 4 --saida plano

Saídas: plano_execucoes_<semente>.csv e registro_plano_<semente>.json (hash).
"""
import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

DOMINIOS = ["QED", "SAR", "COG", "FRA"]
SITUACOES = ["ALT", "LIM", "NOR", "INC"]
VARIANTES = [1, 2, 3, 4]
REPETICOES = [1, 2, 3]
CONDICOES = ["A", "B"]


def montar_pares():
    """Um par = (caso, repetição). Retorna lista com estrato e código."""
    pares = []
    for dom in DOMINIOS:
        for sit in SITUACOES:
            for k in VARIANTES:
                for rep in REPETICOES:
                    pares.append({
                        "estrato": f"{dom}-{sit}",
                        "codigo": f"TESTE-{dom}-{sit}-{k:02d}",
                        "rep": rep,
                    })
    return pares


def distribuir(pares, n_sessoes, rng):
    """Distribui os pares nas sessões mantendo os estratos equilibrados."""
    por_estrato = {}
    for p in pares:
        por_estrato.setdefault(p["estrato"], []).append(p)
    sessoes = [[] for _ in range(n_sessoes)]
    # Sorteia, para cada estrato, a ordem de entrada e distribui em rodízio.
    # O ponto de partida do rodízio muda a cada estrato para que sessões
    # não fiquem sistematicamente com o resto da divisão.
    inicio = rng.randrange(n_sessoes)
    for estrato in sorted(por_estrato):
        lista = por_estrato[estrato][:]
        rng.shuffle(lista)
        for i, p in enumerate(lista):
            sessoes[(inicio + i) % n_sessoes].append(p)
        inicio = (inicio + len(lista)) % n_sessoes
    for s in sessoes:
        rng.shuffle(s)
    return sessoes


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--semente", type=int, required=True,
                    help="semente do plano (diferente da semente dos casos), registrada antes")
    ap.add_argument("--sessoes", type=int, required=True, help="número de sessões (dias)")
    ap.add_argument("--saida", default="plano")
    args = ap.parse_args()
    if not 1 <= args.sessoes <= 64:
        sys.exit("--sessoes deve ficar entre 1 e 64")

    rng = random.Random(args.semente)
    pares = montar_pares()
    sessoes = distribuir(pares, args.sessoes, rng)

    linhas = []
    n = 0
    for s_idx, pares_s in enumerate(sessoes, start=1):
        ordem = 0
        for p in pares_s:
            condicoes = CONDICOES[:]
            rng.shuffle(condicoes)
            for cond in condicoes:
                n += 1
                ordem += 1
                linhas.append({
                    "id_execucao": f"E{n:03d}",
                    "sessao": s_idx,
                    "ordem_na_sessao": ordem,
                    "codigo_caso": p["codigo"],
                    "estrato": p["estrato"],
                    "repeticao": p["rep"],
                    "condicao": cond,
                    "session_id": f"fase1-{p['codigo']}-r{p['rep']}-{cond}",
                    "data_hora_inicio": "",
                    "versao_fluxo_ativa": "",
                    "arquivo_resposta": "",
                    "n_mensagens": "",
                    "observacoes": "",
                })

    # Conferências internas
    assert len(linhas) == 384, len(linhas)
    assert len({l["session_id"] for l in linhas}) == 384
    chaves = {(l["codigo_caso"], l["repeticao"], l["condicao"]) for l in linhas}
    assert len(chaves) == 384
    sessao_do_par = {}
    for l in linhas:
        k = (l["codigo_caso"], l["repeticao"])
        sessao_do_par.setdefault(k, set()).add(l["sessao"])
    assert all(len(v) == 1 for v in sessao_do_par.values()), "A e B em sessões diferentes"

    saida = Path(args.saida)
    saida.mkdir(parents=True, exist_ok=True)
    csv_path = saida / f"plano_execucoes_{args.semente}.csv"
    campos = list(linhas[0].keys())
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=campos, delimiter=";")
        w.writeheader()
        w.writerows(linhas)

    resumo = {}
    for l in linhas:
        resumo.setdefault(l["sessao"], {"execucoes": 0, "A": 0, "B": 0})
        resumo[l["sessao"]]["execucoes"] += 1
        resumo[l["sessao"]][l["condicao"]] += 1
    registro = {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "semente_plano": args.semente,
        "sessoes": args.sessoes,
        "n_execucoes": len(linhas),
        "execucoes_por_sessao": resumo,
        "plano_csv_sha256": hashlib.sha256(csv_path.read_bytes()).hexdigest(),
        "plano_py_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    reg_path = saida / f"registro_plano_{args.semente}.json"
    reg_path.write_text(json.dumps(registro, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"{len(linhas)} execuções em {args.sessoes} sessão(ões)")
    for s, r in sorted(resumo.items()):
        print(f"  sessão {s}: {r['execucoes']} execuções (A={r['A']}, B={r['B']})")
    print(csv_path)
    print(reg_path)


if __name__ == "__main__":
    main()
