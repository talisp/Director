# Pesquisa dirigida por gargalo

Antes de aprofundar um projeto para evoluir o Director, vincule a pesquisa a uma decisão:
issue, pedido humano representativo, commit do Director observado, capacidade existente e
hipótese. `fila.py gargalo URL ARQUIVO.json` grava esse vínculo na fila já existente.
Não modificar o foco original do usuário nem iniciar uma segunda fila.

1. Triagem curta: código/algoritmo/inspiração/pronto, licença, manutenção e dependências.
   Conferir equivalente nativo instalado e o que já está no Director antes de portar.
2. Fixar orçamento do lote em repositórios, chamadas e bytes; medir consumo. Se for preciso
   ultrapassar um limite autorizado, registrar `partial ... decisao` e pedir ampliação.
   Contexto longo continua não sendo motivo de parada. Não contar chamadas ou tokens como qualidade.
3. Inspecionar produtor, representação e consumidor do resultado; segunda decisão da LLM
   precisa de prova, não só nome de função. Determinismo matemático não implica sucesso humano.
4. Teste mínimo offline primeiro, depois laboratório quando necessário. Uma variação antes
   de promover a ficha a `verificado_no_ensaio`; código lido sozinho continua `proposta`.
5. `FICHA_OPERADOR.json`: problema/issue/pedido/commits, arquivos/funções, licença/fontes,
   capacidade existente, acréscimo, hipótese, teste, evidências tipadas, variação, limites,
   recuperação, dependências, orçamento e instrução curta ao operador.
6. `verificar_ficha.py` valida a forma, não a veracidade das alegações. Se houve vínculo de
   gargalo, o finish exige ficha válida e mesmo issue/pedido/commit do vínculo. Os relatórios,
   checkpoints, rubrica e painel anteriores continuam obrigatórios; estudos antigos sem
   vínculo não ganham exigência retroativa. Não reabrir avaliações só para preencher um campo.

Pesquisa não dá autorização de integração. A ficha deve dizer `integracao_autorizada:false`.
Uma técnica descoberta pelo próprio operador também começa como proposta com procedência.
Recorrer a modelo de fronteira é escalonamento futuro, não dependência desta pesquisa.
