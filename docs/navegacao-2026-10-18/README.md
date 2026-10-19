# Navegação: reprodução e correção candidata da #10

18/10/2026, Unreal 5.8.3-58210709, código-base publicado `ccb4b67`.
Trabalho autorizado no Unreal e no desenvolvimento, sem usar Qwen, Hermes ou Blender.
**Não instalado no operador publicado. A #10 continua aberta até revisão/integração.**

## Como foram separados os casos

As três plantas/fichas de 17/10 foram lidas antes de testar. Recriar o arranjo leste–oeste
com o código atual não reproduziu sua falha de carga. Recriar o norte–sul antigo foi
recusado corretamente: a folha de porta_b invade mesa_b na configuração histórica.
Não foi retirada essa validação para produzir aprovação.

Foram então duplicados no laboratório os mapas binários históricos leste–oeste e
norte–sul, com destinos novos. Os arquivos fonte conservaram seus SHA256. As novas
variações válidas usam a porta_b para fora, sem interpenetrar a mesa. Os níveis de teste
e suas plantas locais não substituem o estado compartilhado do operador.

## Causas e evidências

### 1. Carga encerrada não significa navegação reconstruída

Na cópia histórica leste–oeste, o trajeto não existia após a carga e a espera. Depois
de `RebuildNavigation`, ficou completo nos dois sentidos, com 730 cm. A malha estava
disponível e sem trava antes da reconstrução: esperar mais não era a solução.

O código instalado da Epic remove `AsyncLoadLock` com `NoRebuild` e limpa as áreas
pendentes na conclusão da carga (`NavigationSystem.cpp`, ticker de `RegisterDelayedUnlock`).
Isso explica por que pedir build cedo ou apenas esperar pode deixar a consulta sem rota.
O novo `reconstruir` aguarda prontidão antes de solicitar o build; não força a retirada
de trava interna nem altera resoluções. Não se afirma que todo mapa reaberto precisa disso.
O prazo limita a espera por prontidão entre respostas; não cancela uma chamada MCP já
em andamento se o editor parar de responder. Cancelamento de processo/agente continua em #38.

### 2. Precisão do vão e alinhamento dos tiles são problemas distintos

Na cópia norte–sul, reconstruir com células de 19 cm ainda devolveu caminho parcial:
ida terminava em y=684; volta, em y=760. A cápsula de raio 34/meia altura 88 passava.
Refinar a região com HIGH=5/2 cm permitiu cruzar o vão, mas surgiu interrupção em y=988.

O gerador Recast calcula tamanho efetivo por `TruncToInt(TileSizeUU / CellSize)`.
Com TileSizeUU=1000, os perfis 38/19 cm produziam tiles efetivos de 988 cm, e o HIGH=5
produzia 1000 cm. A interrupção observada coincide com essa borda. A documentação da Epic
recomenda tamanho de tile divisível pelas resoluções. Alinhar explicitamente o tile em
950 cm e refinar somente a região resolveu a rota nos dois sentidos: cerca de 743,6 cm,
com DEFAULT=19 cm preservado. O refinamento global também funcionou, mas não foi adotado
como padrão nem necessário para esta correção.

Fontes consultadas no ambiente instalado:

- `NavigationSystem/Private/NavMesh/RecastNavMeshGenerator.cpp`, cálculo de `walkableRadius`
  e de `tileSize`: voxelização/erosão do raio e discretização, diferentes de uma cápsula contínua.
- `NavigationSystem/Private/NavMesh/RecastNavMesh.cpp`, `PostEditChangeProperty`: mudar
  TileSizeUU normaliza as células. O primeiro teste de restauração expôs valores diferentes;
  a ordem foi corrigida para restaurar tile antes de restaurar os perfis exatos.
- [Epic — Navigation Mesh Resolutions](https://dev.epicgames.com/documentation/en-us/unreal-engine/navigation-mesh-resolutions-user-guide),
  consultada em 18/10/2026. O guia sustenta o uso de resoluções regionais; o funcionamento
  específico foi verificado nos mapas locais, não presumido da documentação.

O NavModifierVolume criado pelo método existente tinha bounds válidos e acionou HIGH.
A hipótese de volume vazio não se confirmou; não foi criado um substituto desse mecanismo.

## Mudanças preparadas

- `navegacao.py`: ação `reconstruir`, espera limitada por prazo_s de até 60 s; timeout
  antes da ação retorna nenhuma_alteracao. Não modifica perfil por tentar reconstruir.
- `editor/director_tools/nav_parametros.py`: valida todos os perfis antes de mudar qualquer
  malha, com tolerância ao float nativo. Mistura incompatível é recusada com uma proposta
  de tile. A proposta não é aplicada automaticamente.
- `ops.nav_config`: aceita tile_cm explícito; backup/restauração agora inclui tile e
  respeita o callback nativo. Não reduz raio nem apaga parede/porta para obter caminho.
- CLI e skill candidata 0.5.7 explicam uso e alcance. Essa skill não foi instalada.

Alterar tile_cm muda a grade de todo o level; escopo região não torna essa mudança local.
O perfil HIGH afeta também outros modificadores HIGH existentes. Os avisos expõem isso.
Reconstrução/configuração são explícitas: `estado` e `observar` continuam sem reparar a cena.

## Validação realizada

| Caso | Resultado |
|---|---|
| Histórico leste–oeste | Falha de carga reproduzida; reconstrução sem mudar perfis resolve ida/volta; salvar/reabrir e reconstruir continua válido |
| Histórico norte–sul | Parcial após rebuild; refino incompatível recusado sem alteração; tile alinhado + HIGH regional resolve ida/volta e reabertura |
| Caminhada real | Leste–oeste: 7,3/6,7 cm do destino. Norte–sul, candidato final: 7,5/6,7 cm. Todos parados; tolerância 10 cm |
| Variação norte–sul A | Corredor 150→180 cm; caminho completo nos dois sentidos e depois de salvar/reabrir; porta fechada bloqueia cápsula, aberta libera |
| Variação norte–sul B | Outra origem e salas de outras medidas; corredor 180→210 cm; mesmas verificações aprovadas |
| Variação leste–oeste | Corredor 150→180 cm, confirmado por dois raios de 90 cm; ida/volta, cápsula e reabertura aprovadas |
| Preservação | Identidades de todos os atores controlados mantidas nas expansões; demais objetos lógicos e mesas idênticos; restauração exata dos perfis/tile e remoção do modificador criado |

Depois dos ensaios, voltou-se ao level originalmente encontrado (`L_sala`) com inventário
integral idêntico, sem Play nem pacotes pendentes. Cópias de ensaio permanecem no laboratório.
Rebuild pode deixar o pacote do teste por salvar; isso não é alteração de geometria dos
atores. A comparação inicial incluiu indevidamente esse indicador e foi corrigida para
verificar geometria e atores separadamente; a restauração da cena original confere tudo.

[Extratos de consultas e resultados](evidencias.json). Scripts, hashes dos candidatos,
backups e logs brutos estão em `work/nav_20261018`, fora do Git. As funções candidatas
foram executadas em namespace temporário, usando as APIs do editor já registrado; não
se recarregou a implementação publicada do toolset para apontar ao desenvolvimento.

## Teste amanhã e limites

Regressão final: 143 testes Director e 13 da guarda aprovados. Os testes da guarda são
funções locais, sem iniciar ou acessar o serviço Hermes. A suíte inclui callback simulado
de normalização do tile e a função nativa real compilada sem Unreal para provar a ordem
de restauração e a recusa antes da primeira mutação. Não são 156 pedidos humanos atendidos.

Depois da revisão e atualização autorizada do operador, usar um JSON com
`{"acao":"reconstruir","prazo_s":20}` em `python -m director navegacao PEDIDO.json`.
Se precisar refino, diagnosticar os perfis e definir a região do caso; aceitar tile_cm
somente com seu alcance entendido. 950/5/2 são valores destes ensaios, não receita universal.
Conferir caminho nos dois sentidos, colisão, preservação e salvar/reabrir. `pronta` não é PA.

Atualização de 19/10: [dois ensaios reais pelo Hermes/GLM](hermes-glm-2026-10-19.md)
confirmaram reconstrução e correção após feedback, com adaptador explícito da candidata.

Ainda não verificados: seleção autônoma sem adaptador, comparação de custo de contexto, memória/FPS
e robustez em cenas grandes. Não se alegam animação corporal, generalização irrestrita ou
reparo automático de toda navegação apenas por estes testes.
