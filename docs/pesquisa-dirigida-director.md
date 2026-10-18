# Evolucao proposta da director-research

Baseline lido: skill 0.2.1 do perfil pesquisador. Ela ja possui fila, checkpoints,
proveniencia, rubrica e teste do retorno a LLM. Nao reconstruir essa infraestrutura.
O perfil pesquisador em andamento nao foi alterado nem reiniciado nesta rodada.

## Complemento para a proxima rodada

Antes de aprofundar um repositorio, registrar um **gargalo do Director**, sua issue,
o commit observado e um pedido representativo. Pesquisar para mudar uma decisao
concreta: a nota geral do repositorio nao substitui esse foco.

1. Triagem curta: problema atendido, mecanismo localizado no codigo, licenca,
   dependencias/custo, equivalente nativo ou ja existente no Director. Sem rodar
   benchmark/dataset inteiro para descobrir se o projeto sequer serve.
2. Aprofundar o candidato relevante ao proximo bloco do pipeline. O texto original
   do foco dado pelo usuario permanece preservado na fila existente.
3. Separar codigo copiavel, algoritmo portavel, inspiracao e solucao pronta. Preferir
   reaproveitar um backend existente quando o ganho esta nas restricoes/casos de teste.
4. Entregar uma ficha curta ao operador, ligada a evidencias completas e versoes:
   problema, precondicoes, capacidade existente, hipotese, procedimento, resultado
   esperado/obtido, limites, recuperacao e quando pedir ajuda. Nao incluir receita
   especifica de casa como se fosse uma capacidade geral.
5. Demonstrar uma variacao antes de promover o aprendizado. Dados do plano, do motor,
   relato do autor e inferencia do pesquisador devem ficar separados.
6. Definir custo por lote ANTES de pesquisar (repositorios, chamadas/tempo/dados),
   registrar consumo e retomar dos checkpoints. Para mudar o comportamento de parada
   da fila, atualizar e testar seus validadores; nao contornar a regra atual criando
   um finish ficticio ou uma segunda fila/scheduler.

Formato curto sugerido (sem novo banco):

```text
gargalo / issue / pedido / commit_Director
repo / commit / arquivos_funcoes / licenca_verificada
classe: codigo | algoritmo | inspiracao | pronto
o_que_ja_existe / acrescimo_necessario
hipotese / teste_aceitacao / observado / evidencias
variacao / limites / recuperacao / custo_medido
estado: proposta | verificado_no_ensaio (integracao nao autorizada por esta nota)
```

## Exemplo conferido: salas por adjacencia

Gargalo #12/#33. Pesquisa verificada em 18/10/2026:
[SceneSmith room_placement.py](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/floor_plan_agents/tools/room_placement.py).
SHA256 do arquivo: c98fb85a85995bd4e9a0fd2d8fe74dc5cd5d72cb32977dbec645c901633ac4bc.
GitHub indica MIT, repositorio nao arquivado; main observado em 67cc408, commit de
20/05/2026. Pushed_at 20/06/2026 nao e a data do commit main nem prova de manutencao futura.

`place_rooms` / `_place_rooms_attempt` ordenam dependencias, montam adjacencias reversas
e buscam candidatos por backtracking com timeout. `_score_placement` rejeita adjacencias
nao satisfeitas com salas ja colocadas; compactacao e estabilidade entram na pontuacao.
`best_layout is None` pode ocorrer por prazo: nao transformar isso em prova de impossibilidade.
Esta inspecao e de codigo, nao execucao independente do SceneSmith nem validacao de todo o projeto.

**Classificacao:** inspiracao/regras e casos, sem copiar seu resolvedor.
O Director ja tinha retangulos, paredes compartilhadas, CP-SAT e executor. A capacidade
nova cabe no backend existente. Essa comparacao foi confrontada com o incremento local,
nao usada para alegar que o codigo externo foi integrado.

**Prova local:** docs/composicao-salas.md; quatro comodos medidos, passagem sem porta,
variacao de tamanho/origem, cozinha aumentada com mesa e identidades preservadas.
Commit 223eb65, OR-Tools instalado 9.15.6755, Unreal 5.8.3. Nao houve dependencias
SceneSmith/Drake ou download de acervo. Esse resultado valida o nosso incremento,
nao os benchmarks ou a estabilidade geral do repositorio externo.

**Ficha para o Qwen:** use planejar com salas/adjacencias; aplique ficha_salas inteira,
respeitando revisao_base; adjacencia nao cria passagem; medir e testar rota no motor.
Se o solver nao encontrou no prazo, nao diga impossivel. Cantos existentes estao fixos;
incompatibilidade pede outra proposta, nao deslocamento silencioso. Retangulos/1cm/32salas
sao limites deste piloto; nao prometer terreno ou vila.

#15 permanece aberta para incorporar esse complemento ao protocolo/validadores da skill
e testa-lo em uma pesquisa real seguinte. A proposta esta pronta e versionada; nao ha
segunda instalacao com nome duplicado nem alteracao do pesquisador em execucao.
