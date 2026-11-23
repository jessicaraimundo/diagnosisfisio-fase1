# Registro de congelamento, sementes e assinaturas digitais (hashes) – fase 1

Preparado em 17/11/2026. Fonte: registros de geração gravados pelos programas e registro do projeto de 17/11/2026.

## 1. Sementes (registradas antes de gerar)

Registro em 17/11/2026, 15:39 (horário de Brasília). Nenhum caso do conjunto de teste havia sido gerado até esse momento.

| Item | Valor informado | Valor usado nos programas |
|---|---|---|
| Semente dos casos do conjunto de teste (64 casos) | 010899 | 10899 |
| Semente do plano de execuções (384 execuções) | 011272 | 11272 |
| Semente do conjunto de desenvolvimento (16 casos) | 20261111 | 20261111 |
| Número de sessões | 1 | 1 |

Os zeros à esquerda não existem para o Python (`int("010899") = 10899`).

## 2. Fluxo congelado

n8n `9TI6HcPuutgaRvoA`, versão `15811ed0` (identificador completo `15811ed0-e3e7-4ddd-85c3-be70ac8a48d2`), modelo gemini-3.6-flash, temperatura 1,0 (A e B). Fluxo B: a publicar apenas durante a rodada, com registro do identificador da versão publicada.

Instrução de sistema da versão ativa `15811ed0` (campo System Message do nó "Assistente de Diagnóstico"), lida do n8n em 17/11/2026, 23:54 (horário de Brasília): arquivo `prompt_sistema_versao_15811ed0.txt`, 10.799 caracteres (10.799 bytes, só ASCII), 83 linhas, 0 links. SHA-256 `6cf67c4cff310a98b773f51855da5aa0868d48c24e824ef24e05e7ddb10a19c7`.

## 3. Geração do conjunto de teste

- 17/11/2026, 15:40 (Brasília), 18:40 UTC.
- `python3 gerar_vinhetas.py --conjunto teste --semente 10899 --confirmo-congelado` → 64 casos.
- `verificar_vinhetas.py --regerar` → 64 de 64 aprovados; reprodutibilidade confirmada (mesma semente, mesmos casos).
- Estrutura conferida: 16 células × 4 casos; 32 em tabela e 32 em texto livre; códigos `TESTE-<DOM>-<SIT>-<01..04>`.
- `plano_execucoes.py --semente 11272 --sessoes 1` → 384 execuções (192 A e 192 B).

## 4. Hashes (SHA-256)

**Gravados nos registros de geração em 17/11/2026, às 15:40 (18:40 UTC):**

| Arquivo | SHA-256 |
|---|---|
| `02_Gerador_de_vinhetas/regras_v0.1.json` | `0ae412e0d52a788c219476bbcdba610b24fd61d898e428de8353e06f3cb28c0c` |
| `02_Gerador_de_vinhetas/gerar_vinhetas.py` | `2b4e7918637297a39dc2a6fa1fec782eabb3c419e45e99dfcb8b341a811cb022` |
| `03_Conjunto_de_teste/casos_teste_semente10899.json` | `549d3deb65327d215e27cdbeb286eef9edc9c530e0d5ef689cfb2740c52d9d93` |
| `03_Conjunto_de_teste/plano_execucoes_11272.csv` | `ce478cecaa0a664f9890c08192d0424108795a737f8b3a8764bed0393f8bed4a` |
| `02_Gerador_de_vinhetas/plano_execucoes.py` | `b221d5cffd429d55026cd8a6098953694518dab2a2534dca4cad03d059e29293` |

**Calculados em 17/11/2026, à noite, ao montar este pacote** (não estavam nos registros de 15:40; os arquivos têm data de modificação anterior, e o conjunto de teste foi conferido contra o pacote gerado às 15:40):

| Arquivo | SHA-256 |
|---|---|
| `02_Gerador_de_vinhetas/verificar_vinhetas.py` | `377a824bf1e45eb78025065bd20c8d74cc7d3695c4b1edf75c9a4d8fde1fdce3` |
| `03_Conjunto_de_teste/casos_teste_semente10899.csv` | `2b0884e3bb9178ca62ff018a1ee4e74c87e287854937d2d37f336ebf25a6d610` |
| `03_Conjunto_de_teste/matriz_rastreabilidade.csv` | `88ce24adbf027359c18380421f1563321d01ce069a2d4f5dc8a4ea4d5212bcd6` |

**Conjunto de desenvolvimento (gerado em 12/11/2026):**

| Arquivo | SHA-256 |
|---|---|
| `04_Conjunto_de_desenvolvimento/casos_dev_semente20261111.json` | `50778a006afcab4da438650a8b4d9f17b080dd9c71c7bd940de7e3ed6b12709a` |

A lista completa dos arquivos do pacote está em `SHA256SUMS.txt`, na raiz.

## 5. Como conferir

Numa pasta com o pacote, em Linux ou macOS:

```
sha256sum -c SHA256SUMS.txt
```

No Windows (PowerShell): `Get-FileHash -Algorithm SHA256 <arquivo>` e comparar com a tabela. Para refazer os 64 casos:

```
python3 gerar_vinhetas.py --conjunto teste --semente 10899 --confirmo-congelado --saida saida
python3 verificar_vinhetas.py --casos saida/casos_teste_semente10899.json --regras regras_v0.1.json --regerar
```

O resultado deve ser idêntico ao arquivo registrado.

## 5b. Registro no OSF

Primeira tentativa (17/11/2026, 23:56): o arquivamento falhou no OSF (erro ao copiar arquivos) e o registro foi apagado pelo próprio OSF, sem publicação. Segunda tentativa, com o mesmo rascunho e o mesmo conteúdo: enviada em 18/11/2026, 00:01 (horário de Brasília; 03:01 UTC), pedido de publicação imediata e sem embargo, endereço https://osf.io/gdt5j/ . Poucos minutos depois, o registro estava público (status "accepted"), com DOI https://doi.org/10.17605/OSF.IO/GDT5J . O arquivo `prompt_sistema_versao_15811ed0.txt` foi anexado ao registro.

## 6. Pendente antes de executar

1. Leitura dos 64 casos pela autora. `[pendente]`
2. Ensaio de automação (3 execuções) e escolha final entre 64 e 48 casos. `[pendente]`
3. Publicar o fluxo B só durante a rodada e registrar o identificador da versão. `[pendente]`
4. Não alterar o fluxo A depois do início.
