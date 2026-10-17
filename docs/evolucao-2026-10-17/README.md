# Director — entrega, evidências e pendências de 17/10/2026

Este registro complementa o [PR #11](https://github.com/talisp/Director/pull/11).
A entrega de código está no commit `56be177`, integrado à `main` por `aaa1420`.
Há um único Director; o laboratório e as cenas de ensaio são ambientes de verificação.
Este complemento publica dados e acompanhamento; não executa novos testes no Unreal.

## O que foi entregue

| Capacidade | Estado e limite |
|---|---|
| Ajuda e erros de CLI | Ajuda offline; erros estruturados; JSON compacto com escape ASCII |
| `observar` | Planta versus dados reais; caixas, componentes, colisão e física. Caixa não comprova passagem livre |
| `assets` | Busca nominal em `/Game`; não importa do Fab, não faz busca semântica nem integra um asset à planta |
| `medir` | Raios, cápsulas, caminhos e estado da navegação pelo motor |
| Prontidão de navegação | Considera trava nativa e existência de malha; não comprova conectividade |
| Perfil Hermes | Retirados cartões repetidos; complemento mantém reparo de `clarify`; skill v0.3.1 |
| Proteções | Mantidos isolamento, trava de acesso ao Unreal, identidade, conciliação e recuperação |

Fontes: `director/__main__.py`, `director/consultas.py`, `director/editor/director_tools/ops.py`
(`inventory`, `assets_find`, `measure`), `director/nucleo/executor.py` (`_esperar_nav`, `_efetivar`)
e `hermes/`. Templates versionados não incluem credenciais nem os arquivos pessoais do perfil instalado.

## Evidências publicadas

- [evidencias.json](evidencias.json): extratos selecionados de registros locais, com consultas e resultados positivos e negativos.
- [fichas-norte-sul.json](fichas-norte-sul.json): fichas de construção e alteração dos dois arranjos determinísticos.
- [planta-qwen.json](planta-qwen.json): resultado declarativo da cena escolhida pelo Qwen; arquivo de referência, não ficha de operações.

Os extratos não substituem todos os logs nem constituem reprodução independente.
Não foram publicados dumps de conversas, credenciais, endereços privados, assets binários ou plantas de outros trabalhos.
Os registros brutos permanecem locais em `work/testes_20261017/`.

### Ambiente e ponto de partida

Windows, Unreal `5.8.3-58210709+++UE5+Release-5.8`, projeto de laboratório.
Baseline de código `1f5e729`, com alterações locais anteriores no perfil Hermes e em cenas;
portanto, não foi um checkout limpo daquele commit.
Modelo observado: `qwen3.8-flash-next-q8_0`, servido remotamente pelo Strata.
8080 era o endpoint encaminhado para o modelo; 8081 era o acesso web do Strata.
Essas são observações de 17/10, não garantia de disponibilidade futura.

### Testes determinísticos e interface

| Ensaio | Resultado observado |
|---|---|
| A: salas 4 × 4 m; corredor 1,5 × 3 m | Largura real 150 cm; cápsula livre; parede lateral bloqueia; caminho parcial |
| A: ampliar corredor em 30 cm | Largura 180 cm; salas, mesas e portas preservadas; nenhum ator recriado; caminho ainda parcial |
| B: origem e salas diferentes; corredor 1,8 × 3 m | Largura real 180 cm; cápsula livre; caminho parcial |
| B: ampliar em 30 cm | Largura 210 cm; partes preservadas; nenhum ator recriado; caminho ainda parcial |
| Repetir alteração, nos dois arranjos | Nenhuma ação adicional; inventário idêntico |
| Reduzir corredor para 40 cm, nos dois arranjos | Recusado; cena intacta |
| Interface nova, no arranjo leste–oeste | 150 cm livres, cápsula livre, parede bloqueando; caminho completo após reconstrução nativa |

49 testes do Director e 4 do complemento Hermes passaram na entrega.
São testes de núcleo/interface e regressão do complemento, não 53 pedidos humanos atendidos.
Verificação de preservação: inventário da cena original igual antes/depois, sem Play nem pacotes pendentes ao final.
Isso não é uma comparação binária de todos os arquivos do projeto.

### Ensaio real do Qwen, antes da nova interface

Pedido: duas salas de 4 × 4 m, corredor com 1,5 m de largura e 3 m de comprimento,
duas portas abertas de 1 m e uma mesa em cada sala, sem bloquear circulação.
O modelo escolheu orientação leste–oeste; não recebeu a solução geométrica do avaliador.

| Rodada | Chamadas de ferramenta | Duração registrada | Resultado |
|---|---:|---:|---|
| Inicial, limite de 16 turnos | 16 | 224.996 ms | Leu comandos e oito arquivos; planejou, não construiu e pediu sinal para continuar apesar da autorização |
| Continuação da mesma sessão | 13 | 589.215 ms | Construiu e consultou resultados; terminou com saída 0 |

A continuação foi solicitada pelo avaliador; não foi uma correção geométrica fornecida ao modelo.
O modelo corrigiu seus próprios parâmetros de cápsula e um destino de caminho que incidia sobre uma mesa.
Verificação independente: dois raios de 75 cm, cápsula de raio 34 cm/meia altura 88 cm livre
e trajeto completo de 730 cm entre os pontos escolhidos. A planta conferia com o inventário.

Leitura retrospectiva: primeira rodada não atendeu; ao fim da continuação, a construção foi produzida
e os critérios espaciais consultados passaram. A persistência da navegação após reabrir não passou sem reconstrução.
Não é uma bateria formal de PA, não demonstra taxa de generalização e não testa uma nova correção contextual ditada pelo usuário.
A interface nova foi validada por testes e chamadas ao motor; **não houve nova rodada completa do Qwen após sua instalação**.

### Falhas de navegação ainda abertas

1. Durante `AsyncLoadLock`, o motor dizia não estar construindo, mas estava bloqueado. O indicador foi corrigido.
2. Depois de reabrir o arranjo leste–oeste, a consulta retornou caminho inexistente; reconstrução nativa permitiu o trajeto.
3. No arranjo norte–sul, esperar e reconstruir não bastou. Remover apenas a porta não resolveu;
   remover a parede sul da segunda sala junto com a porta produziu caminho completo de 737,2 cm.
   Reaplicar vão de 100 cm e aumentar para 120 cm não resolveu nos ensaios registrados.

O item 3 localiza uma relação problemática entre parede, vão e navegação; não comprova a causa exata.
Raio nativo de navegação observado: 35 cm; altura: 144 cm; geração dinâmica e atualização automática habilitada.
A cápsula de teste é outra consulta; não representa todos os personagens nem substitui teste de caminhada.
Ver [#10](https://github.com/talisp/Director/issues/10).

## Como preparar uma reprodução

Não executar no projeto cinematográfico. Usar uma cena nova no laboratório, sem Play ou alterações pendentes.
Para o caso norte–sul, extrair uma ficha de construção de `fichas-norte-sul.json` e aplicá-la
com `python -m director fazer NOME_NOVO ficha.json`; o arquivo agregado não é uma ficha executável.
No caso A, consultar caminho de `[200,300,1]` a `[200,830,1]`; na ablação independente registrada,
o destino foi `[300,1030,1]`. São consultas distintas, ambas identificadas nos registros.
Usar os parâmetros de B para variar a origem e dimensões; não reutilizar coordenadas de A sem transformação.
As consultas exatas do Qwen e da interface estão em `evidencias.json`.

Separar medições antes/depois de liberar a trava e antes/depois da reconstrução nativa.
Registrar configuração de navegação e versões dos Blueprints; a reprodução ainda precisa confirmar
quanto esses estados locais influenciaram a falha. As ablações são diagnóstico, não correção aceitável do cenário.
Restaurar a cena inicial ao final. Este documento não iniciou essa reprodução.

## Pipeline e acompanhamento

| Ordem | Próximo resultado esperado | Acompanhamento |
|---|---|---|
| 1 | Medir ciclo Qwen → execução → observação → correção com a interface nova, poucas variações e limite de custo | [#4](https://github.com/talisp/Director/issues/4) |
| 2 | Explicar e corrigir navegação nas duas orientações e após reabrir | [#10](https://github.com/talisp/Director/issues/10) |
| 3 | Melhorar composição e alteração espacial local sem macro por construção | [#12](https://github.com/talisp/Director/issues/12) |
| 4 | Reutilizar assets ou compor objetos funcionais com identidade e colisão verificáveis | [#13](https://github.com/talisp/Director/issues/13) |
| 5 | Preservar conhecimento com procedência, sem promover todo experimento a ferramenta | [#14](https://github.com/talisp/Director/issues/14) |
| Apoio | Evoluir pesquisa de GitHub por gargalos e testes concretos, com triagem econômica | [#15](https://github.com/talisp/Director/issues/15) |

Pendências de operação: escrita de arquivo no aplicativo [#6](https://github.com/talisp/Director/issues/6),
divergência automática da skill [#7](https://github.com/talisp/Director/issues/7),
áudio efetivo [#16](https://github.com/talisp/Director/issues/16) e
recuperação/redundância do encaminhamento 8080 [#17](https://github.com/talisp/Director/issues/17).
Habilitar ferramentas, sincronizar uma skill ou restaurar uma conexão uma vez não resolve essas quatro pendências.

Concluídos: retirada dos cartões artificiais [#8](https://github.com/talisp/Director/issues/8)
e interface de consultas [#9](https://github.com/talisp/Director/issues/9).
A política histórica de [#3](https://github.com/talisp/Director/issues/3) foi substituída;
a issue de paredes compartilhadas [#2](https://github.com/talisp/Director/issues/2) não comprova navegação geral.

## O que não foi implementado

Planejador espacial novo, adoção de projetos externos, alteração de `director-research`,
memória/registro automático de aprendizagem e escalada automática para Sol/Claude Code.
Animação corporal, IK, Sequencer e exportação de vídeo não entram neste ciclo.
As issues acima registram direção e critérios de aceitação; não são resultados entregues nem autorização para executar baterias caras.
