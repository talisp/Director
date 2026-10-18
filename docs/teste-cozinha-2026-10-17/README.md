# Teste integrado da cozinha pelo Hermes

Pedido do usuario: cozinha simples sem mesa, anexa a sala existente, e aumentar a mesa da sala.
Rodada executada pelo Codex apos a entrega do Claude no PR #41. Sem novo planejador, banco de dados ou download de acervo.

## Versao efetivamente usada

- Checkout `Director-correcoes`, commit `a733517`, com os mesmos fontes de `origin/main` (`4fe6b36`) no inicio.
- Perfil Hermes `director`, Qwen `qwen3.8-flash-next-q8_0`, servido pelo Strata.
- Skill instalada 0.5.0: contem a fonte atual mais notas locais anteriores de navegacao; nao foi sobrescrita.
  SOUL e complemento coincidem com esse checkout. O editor carregava `director_tools.ops` desse checkout e foi recarregado.
- Unreal `5.8.3-58210709+++UE5+Release-5.8`, laboratorio, cena `hermes_quarto_final`.
  Inicio revisao 71, conciliada e sem pacotes pendentes. O checkout antigo `Director` nao foi usado para operar a cena.

## Resultado e preservacao

Cozinha interna de **300 x 300 cm**, a oeste da sala, com porta de 90 cm aberta.
Nao ha mesa nova. O Hermes reutilizou a malha de pia do projeto e compôs bancada, substituto de geladeira
e cooktop de formas simples. O cooktop foi registrado sobre a bancada, com altura obtida do apoio.
As pecas da cozinha ficaram fixas, com colisao, e estaveis na amostra de Play.

Mesa existente: **120 x 80 -> 160 x 90 cm**, mesma altura de 75 cm e mesmo centro.
Nenhum ID controlado anterior foi removido ou teve seu ator recriado; a unica alteracao na planta dos objetos
anteriores foi a dimensao da mesa. Copo e prato permaneceram apoiados. Quarto, banheiro e corredor nao foram reconstruidos.

**Ressalva:** para satisfazer a verificacao, o Hermes adotou/converteu a cadeira externa antiga para `cadeira_mesa`
fixa. Isso e uma operacao extra: a identidade dos atores controlados anteriores foi preservada,
mas nao se pode afirmar preservacao integral de todos os atores externos. Esse comportamento fica para #4.
O modelo tambem chamou a parede compartilhada de norte em sua resposta; geometricamente e leste da cozinha/oeste da sala.

## Duas falhas pontuais corrigidas

1. **#42 — bounds de marcadores:** `inventory(detalhes=True)` incluia um Billboard de 256 cm.
   Mesa real 160 x 90 x 75 cm era apresentada como 256 x 256 x 256. A consulta nativa com apenas componentes
   com colisao retornou a medida correta. O inventario agora usa esse envelope e explica seu limite.
   Geometria visual sem colisao nao e representada por essa caixa.
2. **#43 — mesa fixa:** o verificador exigia simulacao dinamica da `BP_Mesa`, embora o proprio Director
   a construa como apoio fixo com colisao. Esse padrao agora e respeitado. Exigencia dinamica explicita continua valendo,
   mesas instaveis continuam reprovadas e a regra dos objetos dinamicos nao foi afrouxada.
   Nao foram ligados corpos independentes nos cinco componentes nem recriada a mesa.

O Hermes terminou antes desses reparos declarando a reprovacao da mesa, sem anunciar um veredito falso.
O Codex fez a reverificacao posterior; nao houve uma segunda rodada completa do Qwen com o codigo corrigido.

## Medicoes

| Etapa | Resultado |
|---|---|
| Primeira verificacao do Hermes | REPROVADO: chegadas a 12,5/35,6 cm e exigencia dinamica de mesa/cadeira antigas |
| Segunda verificacao do Hermes | Rotas a 7,9/7,9 cm; REPROVADO apenas pela mesa fixa |
| Reverificacao apos reparos | APROVADO no escopo consultado: chegadas a 7,3/7,9 cm, limite mantido em 10 cm |
| Envelope real da mesa apos reparo | 160 x 90 x 75 cm |
| Janela da inspecao/reverificacao posterior | Zero avisos GetMass; nao e contagem retroativa de todo o teste Hermes |
| Testes automaticos | 97 Director + 11 guarda antes; 100 Director depois, incluindo 3 regressoes novas |

Os destinos foram corrigidos pelo Hermes entre a primeira e a segunda verificacao, mantendo tolerancia 10 cm.
A rota cozinha-sala atravessa a ligacao. A segunda rota vai de `[200,317,1]` a `[200,283,1]`, perto da mesa:
**nao comprova um percurso inteiro desde o corredor**, apesar do nome escolhido pelo modelo.
O teste nao verifica sentar, preparar comida ou abrir geladeira.

O inventario permaneceu identico durante a reverificacao do Codex. A cena foi salva depois da remocao
do personagem temporario; terminou fora do Play, sem pacotes pendentes. Uma captura superior foi inspecionada localmente;
nao constitui aprovacao estetica nem substitui as medidas.

## O que foi testado das seis entregas do PR #41

| Entrega | Evidencia desta rodada | Limite |
|---|---|---|
| Veredito | Reprovacao visivel, com causas; o modelo nao a omitiu | Precisou corrigir o padrao errado da mesa fixa |
| Planejamento | Suite com OR-Tools/Shapely passou | O pedido da cozinha nao exercitou o planejador ao vivo; sem alegacao de validacao completa |
| Guarda | 11 testes passaram; tarefa rodou sem cartoes repetidos | Nao se provocou sleep longo ou disputa real entre processos nesta rodada |
| sobre/fixo | Cooktop sobre bancada; pecas fixas estaveis no Unreal | Nao prova interacoes articuladas |
| GetMass | Zero avisos na janela posterior medida | Nao foram medidos CPU, FPS ou memoria |
| Skill 0.5.0 | Modelo consultou skill e distinguiu fontes dos objetos | Houve erro textual de orientacao e alteracao extra da cadeira |

## Biblioteca: proposta, sem implementacao

O indice JSON anterior tem seis entradas: cinco GLB Kenney e um FBX Fab, todos os arquivos presentes.
O checkout atual nao possui `work/biblioteca/indice.json`; `catalogo.atualizar` consulta apenas o caminho do checkout.
Assim, a busca nova nao enxerga aquele lote. Sinônimos e escala do Kenney tambem continuam pendentes na #27.

Ordem recomendada: estabilizar o caminho da biblioteca e validar esse lote; provar busca, escala e importacao;
depois experimentar um pequeno lote de uma base externa. Nao esperar resolver todas as issues para isso,
mas tambem nao criar SQL ou baixar acervos grandes para contornar falhas de descoberta e escala.
SQLite continua candidato, nao decisao implementada; a necessidade deve vir de volume/consultas medidos.

SceneSmith e SpatialLM estavam documentados na #36. Conferencia atual nas fontes:
[ArtVIP no SceneSmith](https://github.com/nepfaff/scenesmith#artvip-setup) vem em Drake SDFormat com colisao e embeddings;
isso nao comprova que suas articulacoes e colisores se tornam recursos nativos do Unreal por importar uma malha.
[SpatialLM](https://github.com/manycore-research/SpatialLM#spatiallm-dataset) oferece nuvens de pontos e anotacoes de interiores,
uma finalidade diferente de uma biblioteca de moveis prontos. Nenhum desses acervos grandes foi baixado nesta rodada.

## Evidencia e custo

[resultados.json](resultados.json) contem consultas, resultados positivos/negativos, preservacao e hashes dos registros locais.
Os logs brutos permanecem em `work/teste_cozinha_codex_20261017/`, sem publicar credenciais ou configuracoes pessoais.
O teste Hermes fez **32 chamadas**, em aproximadamente **10 min 33 s**. A soma entre chamadas foi 1.646.150 tokens
de entrada (1.596.346 reportados como cache) e 37.107 de saida; isso nao e o tamanho de uma unica janela de contexto
nem uma medicao de custo monetario. Nao foi repetida a rodada completa apos os reparos para economizar processamento.

Pendencias e observacoes registradas em #4, #27, #36, #38 e #39. Este teste nao encerra automaticamente essas issues.
