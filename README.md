[README.md](https://github.com/user-attachments/files/35288101/README.md)
# DiagnosisFisio: material da fase 1 (gerador de vinhetas e registro)

Protótipo de apoio à triagem funcional em fisioterapia gerontológica, com agente conversacional e modelo de linguagem de grande porte. Material de pesquisa da dissertação de mestrado profissional de Jessica Raimundo da Silva (PPGINFOS/UFSC).

O DiagnosisFisio é um apoio à triagem. A decisão diagnóstica é sempre do fisioterapeuta.

**Pré-registro público da fase 1 (OSF):** https://osf.io/gdt5j/ · DOI https://doi.org/10.17605/OSF.IO/GDT5J (registrado em 18/11/2026).

## O que há neste repositório

Todos os arquivos ficam na raiz, sem subpastas.

| Arquivos | Conteúdo |
|---|---|
| `gerar_vinhetas.py`, `verificar_vinhetas.py`, `plano_execucoes.py`, `regras_v0.1.json`, `LEIA-ME.md` | Gerador de vinhetas, verificador, plano de execuções e regras clínicas (Python 3), com o LEIA-ME do gerador |
| `texto_do_registro_fase1.md`, `registro_de_congelamento_e_hashes.md`, `prompt_sistema_versao_15811ed0.txt` | Texto do pré-registro, registro de congelamento (sementes e hashes) e instrução de sistema da versão congelada do fluxo (`15811ed0`) |
| `casos_dev_semente20261111.csv`, `casos_dev_semente20261111.json`, `registro_geracao_dev_semente20261111.json` | 16 casos de desenvolvimento (semente 20261111) e o registro da geração |
| `cortes_app_x_fontes_2026-11-11.csv` | Planilha com os pontos de corte do aplicativo e a situação da conferência de cada fonte |
| `SHA256SUMS.txt` | Assinatura digital (SHA-256) dos demais arquivos do repositório |

Observação: os documentos `LEIA-ME.md` e `registro_de_congelamento_e_hashes.md` citam caminhos com subpastas (por exemplo `02_Gerador_de_vinhetas/`). Neste repositório os mesmos arquivos estão na raiz; os conteúdos e os hashes são idênticos aos registrados.

## Conjunto de teste (64 casos): não incluído por enquanto

Os 64 casos de teste e seus gabaritos serão publicados **depois** da conclusão da fase 1, para que não entrem em dados de treino de modelos de linguagem antes da avaliação. Eles podem ser reproduzidos exatamente com o código deste repositório:

```
python3 gerar_vinhetas.py --conjunto teste --semente 10899 --confirmo-congelado --saida saida
python3 verificar_vinhetas.py --casos saida/casos_teste_semente10899.json --regras regras_v0.1.json --regerar
sha256sum saida/casos_teste_semente10899.json
```

O hash esperado do arquivo de casos é `549d3deb65327d215e27cdbeb286eef9edc9c530e0d5ef689cfb2740c52d9d93`, o mesmo registrado antes da geração (17/11/2026, 15:40, horário de Brasília). O plano das 384 execuções usa a semente 11272 (`plano_execucoes.py`).

## Como conferir a integridade

Numa pasta com o repositório, em Linux ou macOS: `sha256sum -c SHA256SUMS.txt`. No Windows (PowerShell): `Get-FileHash -Algorithm SHA256 <arquivo>`. Os hashes de `gerar_vinhetas.py`, `regras_v0.1.json`, `plano_execucoes.py` e `verificar_vinhetas.py` são os registrados em 17/11/2026.

## Limites declarados

- Todos os casos são fictícios, gerados por programa a partir de regras transcritas de consensos publicados. Não há dados de pacientes nem de participantes.
- O estudo mede conformidade com regras publicadas e com convenções declaradas da autora, e não acurácia clínica.
- O gerador e o verificador têm a mesma autoria e as mesmas regras: a independência entre eles é de código, não de pessoa. Não há conferente externo nas etapas de avaliação.
- O código do gerador, do verificador e do plano de execuções, e textos de apoio, foram escritos com assistência de IA (Claude).

## Situação (17/11/2026)

Casos de teste e plano de execuções gerados e verificados; execuções e julgamento ainda não feitos. Piloto anterior (3 vinhetas, 15 execuções, 23/10/2026): exploratório, relatado à parte. Fase 2 (fisioterapeutas): depende de aprovação do CEP e não faz parte deste material.

## Segurança

Este repositório não contém senhas, chaves de API, tokens nem endereços de webhook. Confira antes de adicionar novos arquivos.

## Licença e citação

A definir pela autora (sugestão: MIT para o código e CC BY 4.0 para os textos). Citar o registro: DOI 10.17605/OSF.IO/GDT5J.
