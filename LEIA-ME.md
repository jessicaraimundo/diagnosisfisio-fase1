# Gerador de vinhetas da fase 1 (DiagnosisFisio) — rascunho v0.1

Estado: **RASCUNHO, regras não congeladas.** Gerado em 11/11/2026. Só o conjunto de desenvolvimento (16 casos) foi gerado. O conjunto de teste (64 casos) **não** foi gerado.

## Arquivos

| Arquivo | Para que serve |
|---|---|
| `regras_v0.1.json` | Cortes, direção de cada corte, faixas plausíveis, convenções da autora e matriz de rastreabilidade (regra → fonte → trecho → conferido). É o único lugar onde os números clínicos aparecem. |
| `gerar_vinhetas.py` | Gera os casos a partir das regras e de uma semente. Texto por modelos de frase, sem modelo de linguagem. |
| `verificar_vinhetas.py` | Segundo script, escrito à parte: recalcula o gabarito de cada caso com frações exatas e tabelas de decisão, e confere escalas, corte exato, estrato, texto × valores, vazamento do diagnóstico, cobertura das 16 células e equilíbrio de formatos. |
| `saida/casos_dev_semente20261111.json` / `.csv` | Os 16 casos de desenvolvimento com texto, valores e gabarito. |
| `saida/matriz_rastreabilidade.csv` | Regra → fonte → situação de conferência. |
| `saida/registro_geracao_dev_semente20261111.json` | Versões e hashes (sha256) das regras, do gerador e dos casos. |

## Como rodar

```
python3 gerar_vinhetas.py --conjunto dev --semente 20261111 --saida saida
python3 verificar_vinhetas.py --casos saida/casos_dev_semente20261111.json --regras regras_v0.1.json --regerar
```

Só precisa de Python 3 (biblioteca padrão). `--regerar` gera de novo com a mesma semente e confirma que o resultado é idêntico.

O conjunto de teste exige `--conjunto teste --confirmo-congelado`. A trava existe para você só gerar depois de congelar regras, prompt e fluxo e registrar a semente.

## Convenções usadas (suas, a confirmar)

- Zona limítrofe: ±10% do corte (mínimo de 1 unidade em escalas inteiras). Nunca se sorteia o valor exato do corte.
- Probabilidade: baixa / média / alta. Com dado ausente ou conflitante, o teto é **média**.
- Caso limítrofe: o gabarito aceita os dois lados do corte e as probabilidades intermediárias.
- Só entram instrumentos da aba "Instrumentos" do app (49: 24 com corte e 25 sem corte único; lista em `regras_v0.1.json`, campo `instrumentos_app_49`). Usados: Berg, TUG, Dinamometria, 10MWT, SPPB, MEEM, GDS-15, eFS e Katz. Retirados por não estarem nos 49: Teste de Sentar-e-Levantar 5x e DXA.
- Sem DXA, a sarcopenia só pode ser "possível" (média) ou ausente; "sarcopenia" e "sarcopenia grave" não são alcançáveis, e os alertas AL-S1 e AL-S2 não ocorrem. O risco de quedas passa a usar só Berg e TUG (0 alterado = baixa, 1 = média, 2 = alta).
- A velocidade de marcha é apresentada como "Teste de Caminhada de 10 Metros (10MWT)", nome do app.
- O EWGSOP2 ficou de fora de propósito (só o AWGS 2019 está verificado).
- Alertas: "esperados" (aparecem em qualquer leitura do caso) e "opcionais" (aparecem só em um dos lados de um valor limítrofe). Alerta fora dessas listas é E2 ou E6.

## Situação das fontes (conferência de 11/11/2026, pelo PubMed e por textos completos acessíveis)

| Regra | Situação |
|---|---|
| MEEM, medianas de Brucki 2003 (20 / 25 / 26,5 / 28 / 29) | **Valores conferidos** (433 saudáveis). Decisão da autora: usar as medianas como referência. São medianas de pessoas saudáveis, então cerca de metade dos saudáveis fica abaixo por definição. Descrever como "abaixo da referência normativa", não como diagnóstico de déficit cognitivo. |
| Berg < 45 | **Dentro da faixa publicada, sem consenso.** Revisão sistemática (Lima 2018): cortes de 45 a 51; Santos 2011: 49; 48 em outra citação. O 45 é o limite inferior e fica registrado como escolha da autora. A fonte citada na dissertação (Miyamoto 2004) não foi conferida. |
| TUG ≥ 13,5 s | **Origem conferida em fonte secundária** (Barry 2014, texto completo: o corte vem de Shumway-Cook 2000). Evidência preditiva fraca (sens. 0,32; espec. 0,73): descrever como corte convencional. Shumway-Cook 2000 não foi lido no texto completo. |
| Sentar-e-levantar 5x > 15 s | **Retirado do gerador** (não está nos 49 instrumentos do app). Fonte conferida no resumo: Buatois 2010. |
| AWGS 2019: preensão 28/18 kg, marcha 1,0 m/s, SPPB ≤ 9 | **Conferido no resumo.** DXA (7,0/5,4) retirado do gerador; "sarcopenia grave" não é mais usada. |
| GDS-15 ≥ 6 | **Conferido no resumo.** Paradela 2005: melhor corte 5/6 (sens. 81%, espec. 71%); Almeida e Almeida 1999 traz 4/5, 5/6 e 6/7. |
| Edmonton 0-4 / 5-6 / 7-8 / 9-10 / ≥ 11 | **Conferido no texto completo** (Fabrício-Wehbe 2009, versão em espanhol). O artigo de Rolfson 2006 (texto completo lido) traz os itens e o máximo de 17, mas não as faixas. |
| Katz 6 / 4 / ≤ 2 | **Convenção, sem corte validado.** Duarte 2007 (lido): o índice original não tem pontuação nem corte; as categorias vêm da versão do Hartford Institute (1998). |

Pendências de leitura: texto completo de Shumway-Cook 2000, Miyamoto 2004 e AWGS 2019 (item "grave").

Alinhamento app x gerador (12/11/2026): o prompt do n8n (versão publicada 54fe9d5b) e a aba "Instrumentos" usam os mesmos cortes do gerador: eFS ≥ 7, SPPB ≤ 9, 10MWT < 1,0 m/s, Berg < 45, TUG ≥ 13,5 s, dinamometria por sexo (AWGS 2019) e MEEM por escolaridade. Katz ≤ 4 entra no gabarito como alerta funcional, mas é convenção de uso; Barthel, Tinetti, FRT, DGI e FSST também são convenção de uso e não entram no gabarito. A planilha `cortes_app_x_fontes_2026-11-11.csv` lista os 24 cortes do app e a situação de cada um.

## Limites do verificador

Gerador e verificador foram escritos pela mesma autoria (com a mesma assistência de IA), a partir das mesmas regras. A independência é de **código**, não de **pessoa**. Por isso a sua leitura de todos os casos continua necessária. Um erro na regra aparece nos dois scripts.

Testes feitos em 11/11/2026, repetidos depois da restrição aos 49 instrumentos: 40 sementes de desenvolvimento sem falha; 3 conjuntos descartáveis de 64 casos em pasta temporária (só passa/falha, conteúdo não lido nem guardado) sem falha; 3 alterações propositais num caso (gabarito, valor fora de escala e termo que vaza o diagnóstico) foram todas detectadas.

## Pendências para você

- Escolher e registrar a semente do conjunto de teste **antes** de gerar (a de desenvolvimento, 20261111, não deve ser reutilizada).
- Ler os 16 casos de desenvolvimento e o gabarito de cada um.
- Congelar regras, prompt e fluxo; só então gerar os 64.
- No conjunto de desenvolvimento só a variante 1 de cada célula é usada; as variantes de conflito (relato × testes, EFS × Katz) só entram no conjunto de teste.
