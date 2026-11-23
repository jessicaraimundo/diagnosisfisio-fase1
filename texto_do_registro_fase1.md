# DiagnosisFisio – Fase 1: avaliação técnica com vinhetas geradas por regras (pré-registro)

Texto preparado em 17/11/2026 para o formulário de registro do OSF. A estrutura segue, em linhas gerais, os campos de um pré-registro (informações do estudo, desenho, amostra, variáveis, análise, outros). Os nomes exatos dos campos do formulário podem variar: copie cada bloco para o campo equivalente.

Itens entre colchetes `[ ]` precisam ser preenchidos pela autora antes de registrar.

---

## 1. Descrição (resumo)

O DiagnosisFisio é um protótipo de apoio à triagem funcional em fisioterapia gerontológica: o fisioterapeuta informa os valores de testes aplicados em um idoso, e um modelo de linguagem sugere hipóteses com grau de probabilidade, sinais de alerta e justificativa. A decisão diagnóstica é sempre do fisioterapeuta.

Este registro descreve a fase 1 da avaliação: um estudo técnico, descritivo, sobre casos fictícios (sintéticos) gerados por um programa a partir de regras clínicas transcritas de consensos publicados. Para cada caso, o programa produz o texto e a resposta esperada (gabarito) derivada da regra. O sistema completo (condição A) e o mesmo modelo sem instrução de sistema (condição B) são executados sobre 64 casos, 3 vezes cada. As respostas são julgadas quanto à concordância com o gabarito e à ocorrência de erros críticos e maiores.

O estudo não envolve participantes humanos nem dados de pacientes. Mede a conformidade do sistema com regras publicadas e com convenções declaradas da autora; não mede acurácia clínica. Esta é a validação analítica, no sentido do IMDRF N41 (2017). A fase 2, com fisioterapeutas, depende de aprovação do CEP e não faz parte deste registro.

## 2. Perguntas de pesquisa

Não há hipótese confirmatória nem direcional. O estudo é descritivo e estima proporções com intervalos de confiança.

1. Em que proporção dos casos o DiagnosisFisio completo (A) produz hipóteses e sinais de alerta concordantes com o gabarito? Por domínio e por situação clínica.
2. Com que frequência ocorrem os erros E1 a E8 (E1 a E4, críticos; E5 a E8, maiores), inclusive o falso positivo em casos normais?
3. Como A se compara a B (o mesmo modelo, sem instrução de sistema) nos mesmos casos?
4. Qual a concordância entre o extrator automático e a autora, e qual a repetibilidade da autora na classificação dos erros?

## 3. Desenho

**Tipo.** Avaliação técnica sobre casos sintéticos. Não há randomização de participantes. A ordem das execuções é sorteada por programa, com semente registrada.

**Sistema avaliado (congelado em 17/11/2026).**
- Fluxo n8n `9TI6HcPuutgaRvoA`, versão `15811ed0` (identificador completo `15811ed0-e3e7-4ddd-85c3-be70ac8a48d2`).
- Modelo: gemini-3.6-flash. Temperatura: 1,0, nas condições A e B.
- Aplicativo: Lovable (interface) e Supabase (dados e autenticação).
- Instrução de sistema da versão congelada: arquivo `prompt_sistema_versao_15811ed0.txt` (10.799 caracteres, 0 links), lido da versão ativa do n8n em 17/11/2026, SHA-256 `6cf67c4cff310a98b773f51855da5aa0868d48c24e824ef24e05e7ddb10a19c7`..

**Condições.**
- A: DiagnosisFisio completo, com coleta guiada: o sistema pede cada teste, e os valores são informados no campo estruturado do aplicativo.
- B: o mesmo modelo, com a mesma configuração do nó, sem instrução de sistema, com todos os dados do caso em uma única mensagem e a mesma frase final pedindo as hipóteses.
- A e B recebem a entrada de modos diferentes (A é interativo, B recebe tudo de uma vez). A comparação mede o conjunto instrução de sistema mais roteiro de coleta contra o modelo puro com os mesmos dados.

**Casos.**
- 4 domínios: quedas e equilíbrio; sarcopenia; cognição e humor; fragilidade e funcionalidade.
- 4 situações: alterado claro; limítrofe; normal; incompleto ou conflitante.
- 16 células. Conjunto de desenvolvimento: 1 caso por célula (16 casos, semente 20261111). Conjunto de teste: 4 casos por célula (64 casos, semente 10899).
- Instrumentos usados: Berg, TUG, dinamometria, velocidade de marcha em 10 metros (10MWT), SPPB, MEEM, GDS-15, Edmonton Frail Scale e Índice de Katz (9 dos 49 instrumentos da aba do aplicativo).
- Sem massa muscular por DXA, a sarcopenia só pode ser "possível" (probabilidade média) ou ausente; "sarcopenia" e "sarcopenia grave" não são alcançáveis. O EWGSOP2 não foi usado, e só o AWGS 2019 está conferido.
- Metade dos casos em formato de tabela e metade em texto livre. O texto livre é montado por modelos de frase, sem modelo de linguagem.
- Convenções da autora, declaradas como tais: zona limítrofe de 10% do corte; faixas de probabilidade esperada (todos os critérios atendidos = alta, 70% ou mais; parte = média, 40% a 69%; nenhum = baixa, menos de 40%); dado ausente ou conflitante dá no máximo probabilidade média; valores iguais ao corte não são sorteados.

**Repetições e execuções.** 3 repetições por caso e condição: 64 × 3 × 2 = 384 execuções (192 A e 192 B). Cada execução é uma conversa nova.

**Recuo registrado antes da execução.** Se o ensaio de automação mostrar que 64 casos é inviável, o teste usa os 3 primeiros casos de cada célula (48 casos, 288 execuções). Essa regra não depende de nenhum resultado.

**Ordem.** Plano sorteado por programa (`plano_execucoes.py`), semente 11272, em 1 sessão. A e B do mesmo caso e repetição ficam na mesma sessão, em ordem aleatória. Cada execução tem identificador de sessão próprio. Se uma execução falhar e precisar ser refeita, usa-se o sufixo `-retry1` e registra-se a observação.

**Execução.** Automatizada, ainda não testada: um agente de IA opera o aplicativo no navegador (condição A), e um fluxo gêmeo ou um programa chama o modelo pela API (condição B). A transcrição de cada execução é guardada e conferida por programa contra os valores do caso. O agente não digita senhas nem cria contas.

## 4. Dados existentes

- Os 64 casos de teste e o plano de 384 execuções foram gerados em 17/11/2026 (15:40, horário de Brasília) e verificados pelo programa de verificação (64 de 64 aprovados) **antes** deste registro.
- Nenhuma execução do sistema sobre o conjunto de teste foi feita e nenhuma resposta do sistema a esses casos foi vista até este registro.
- Estado da leitura dos casos pela autora no momento do registro: nenhum dos 64 casos de teste foi lido pela autora até este registro (informado em 17/11/2026)..
- O conjunto de desenvolvimento (16 casos) foi gerado em 12/11/2026.
- Existe um piloto anterior: 3 vinhetas escolhidas pela autora, 15 execuções em 23/10/2026 (fluxo `909643e5`). O gabarito do piloto foi mantido depois de conhecidas as respostas, mas o piloto é exploratório e nunca é somado a esta fase.
- As sementes dos casos (010899) e do plano (011272) foram registradas em 17/11/2026, às 15:39, antes da geração.

## 5. Conferência dos casos (antes de qualquer execução)

1. Conferência automática: um segundo programa (`verificar_vinhetas.py`), escrito à parte do gerador, recalcula o gabarito de cada caso com frações exatas e tabelas de decisão e compara com o gabarito gravado. Qualquer divergência reprova o caso.
2. Leitura pela autora, que é fisioterapeuta: cada caso é plausível e o texto é coerente com os valores? (sim ou não, com comentário).
3. Critério de aceitação: um caso é aceito se passa na conferência automática e a autora o julga plausível. Casos reprovados são listados e não substituídos um a um.
4. Critério de parada: se 7 ou mais dos 64 casos forem reprovados (mais de 10%), a regra ou o gerador é corrigido e um novo conjunto é gerado com nova semente; o primeiro conjunto e o motivo da troca são relatados.

Limite: o gerador e o verificador têm a mesma autoria e as mesmas regras; a independência é de código, não de pessoa. Um erro na regra aparece nos dois.

## 6. Variáveis medidas

**Por resposta, parte objetiva** (extraída pelo extrator e comparada ao gabarito por programa):
- Concordância das hipóteses com o gabarito: totalmente, parcialmente ou não identificou.
- Sinais de alerta esperados: sim, parcialmente ou não.
- Se o sistema reconheceu a falta de dados (casos incompletos).
- Regra de contagem: uma hipótese só conta como presente se afirmada como hipótese, e não apenas citada como alerta. "Provável" e "possível" significam não confirmado.

**Por resposta, parte clínica** (só a autora):
- E1 diagnóstico confirmado sem dados que o sustentem (crítico).
- E2 dado inventado (crítico).
- E3 recomendação inadequada ou fora do escopo (crítico).
- E4 falso positivo em caso normal (crítico).
- E5 interpretação incorreta de corte (maior).
- E6 hipótese extra sem suporte (maior).
- E7 contradição interna (maior).
- E8 não apontar dado ausente ou conflito (maior).

**Medidas derivadas:** taxa de omissão (hipóteses esperadas ausentes), taxa de falso positivo nos casos normais e proporção de casos incompletos em que o sistema reconheceu a falta de dados.

## 7. Julgamento

- **Extrator.** Um modelo de linguagem diferente do avaliado, com versão fixa, lê cada resposta em ordem embaralhada e preenche uma ficha (hipóteses citadas, probabilidade declarada, alertas, pedido de dados faltantes). Um programa compara a ficha com o gabarito.
- **Verificação do extrator.** Em 60 respostas, a autora preenche a ficha à mão, de forma independente. Critério proposto para manter o extrator, fixado antes: concordância de pelo menos 90% com a autora nos campos da ficha e kappa ponderado de pelo menos 0,70 para a concordância das hipóteses, com intervalo de confiança. Se não for atingido, o extrator é descartado e a autora preenche as fichas das 384 respostas à mão, ou o número de casos é reduzido.
- **Parte clínica.** A autora é a única juíza clínica e também desenvolveu o sistema (limite declarado). Ela julga as 384 respostas em sessões de no máximo 20, com código e em ordem aleatória, depois de uma calibração com respostas de treino que não entram na análise.
- **Repetibilidade.** Depois de pelo menos 14 dias, a autora reclassifica 30 respostas quanto aos erros E1 a E8, e relata-se a concordância dela consigo mesma.
- **Cegamento.** As respostas são apresentadas com código, em ordem aleatória. O cegamento à condição (A ou B) é imperfeito, porque as respostas têm estilos diferentes, e isso é relatado.

## 8. Análise planejada

- **Unidade de análise: o caso.** As 3 repetições não são independentes. Cada caso recebe a classificação mais frequente entre as 3 repetições (em empate, a menos favorável). Para erros, conta-se se ocorreu em pelo menos uma repetição. Os resultados por execução também são informados, com essa ressalva.
- **Desfecho principal:** proporção de casos com concordância "totalmente", por condição, com intervalo de Wilson de 95%.
- **Subgrupos previstos:** os 4 domínios e as 4 situações. Não há outros.
- **A contra B:** pares em que A acertou e B não, e o inverso, e a diferença de proporções com intervalo por bootstrap sobre os casos. Sem teste de significância como critério de conclusão.
- **Erros:** contagem por tipo (E1 a E8) e por gravidade, com o limite superior de Wilson quando não houver ocorrência.
- **Concordância:** porcentagem por campo e kappa ponderado entre extrator e autora; kappa da autora consigo mesma na reclassificação. O kappa é instável para eventos raros, então o número de divergências também é informado.
- **Fases separadas:** piloto, fase 1 e fase 2 são relatadas separadamente, sem somar.

Precisão que o desenho permite (limite superior do intervalo de Wilson de 95% com zero ocorrências):

| Base | N | Limite superior |
|---|---|---|
| Uma célula (domínio × situação) | 4 casos | 49,0% |
| Um domínio ou uma situação | 16 casos | 19,4% |
| Todos os casos de uma condição | 64 casos | 5,7% |
| Todas as execuções de uma condição (não independentes) | 192 | 2,0% |

Zero ocorrências em 64 casos é compatível com uma taxa real de até cerca de 6%. Excluir uma taxa acima de 1% exigiria cerca de 380 casos sem falha, o que está além deste estudo.

## 9. Exclusões e dados faltantes

- Execuções interrompidas por erro técnico e execuções com valor digitado divergente são descartadas, refeitas (sufixo `-retry1`) e contadas.
- Se o fornecedor mudar a versão do modelo durante a coleta, isso é anotado e as execuções afetadas são identificadas.

## 10. Limites

- Como o gerador e o julgamento usam as mesmas regras, o estudo mede conformidade com regras publicadas e com convenções da autora, e não acurácia clínica. Não há validação clínica independente.
- Casos fictícios e estruturados são mais regulares do que pacientes reais.
- Juíza única, que também construiu o sistema.
- Faixas de probabilidade, zona limítrofe e alertas esperados são convenções da autora.
- Contaminação: os cortes vêm de consensos públicos que o modelo pode ter visto.
- Extrator automático com vieses conhecidos, usado só na parte objetiva e com critério definido antes.
- Modelo de terceiros: o resultado vale para a versão e a data registradas.
- Escopo restrito: não há testes de emergência, pedido de dose nem entrada maliciosa.
- Precisão limitada por célula e para eventos raros.

## 11. Decisões e mudanças em relação à proposta inicial do protocolo

Registradas aqui para que o registro seja fiel ao que será feito.

1. **17/11/2026 – conferências.** A proposta inicial previa conferência humana externa da transcrição das regras, de 16 casos (1 por célula) e das fichas de 60 respostas. Por decisão da autora, nenhuma etapa de avaliação tem conferente externo. As conferências ficam com o segundo programa e com a autora, e a verificação do extrator é feita só pela autora. Consequência: não há segundo avaliador humano em nenhuma parte.
2. **Instrumentos do gerador.** O sentar-e-levantar 5x e a massa muscular por DXA foram retirados porque não estão nos 49 instrumentos do aplicativo. Por isso a sarcopenia só pode ser possível ou ausente.
3. **Temperatura.** Fixada em 1,0, nas condições A e B.
4. **Delineamento anterior (fase 1b: 7 vinhetas × 10 repetições × 2 condições).** Substituído por este e não será executado. Os critérios de erros E1 a E8 foram mantidos.

## 12. Ética e dados

- A fase 1 não envolve participantes nem dados de pacientes. Todos os casos são fictícios.
- A fase 2, com fisioterapeutas, não faz parte deste registro e depende de aprovação do CEP. Nenhum convite nem coleta antes da aprovação.
- Uso de assistência de IA (Claude) na escrita do código do gerador, do verificador e do plano de execuções, e na redação de textos de apoio. Declarado.

## 13. Autoria

- Autora: Jessica Raimundo da Silva (mestrado profissional, PPGINFOS/UFSC).
- Declaração de interesse: a autora desenvolveu o sistema que avalia.
