# USD ArtVIP no Unreal e no Hermes — 21/10/2026

## Objetivo e ambiente

Continuacao autorizada do download da estante bookcase007 e mesa table 5.
Unreal instalado/respondendo: 5.8.3-58210709, laboratorio DirectorLab/porta 8011.
Estado inicial: /Game/Director/Cenas/L_sala, sem Play/pacotes pendentes.
Projeto cinematografico nao foi acessado. Artefatos, scripts de ensaio e backup
SQLite consistente: R:/CINF/BD/Director/importacao-20261021/.

## Primeiro teste conversacional

Hermes/Luna low, skill 0.5.14, sessao
`local-cbe0b7c1a701f7a3d510c9a7c898d33afcb037eafa54814b25e2303e0e07a0df`.
NAO ATENDIDO em 32,629 s: tentou combinar comandos com background, recusado pelo
terminal; depois copiou o caminho UNC com escapes invalidos no JSON. Nenhuma
inspecao chegou ao motor. Nao era falta de OpenUSD nem arquivo ausente.

Correcao dirigida: `inspecionar_usd` e `importar` podem selecionar arquivo pelo
ID SQL se houver exatamente um modelo elegivel registrado/presente. Ambiguidade
continua exigindo arquivo explicito; hash continua conferido. Skill 0.5.15 pede
sequenciar inclusive leituras que compartilham a trava do Unreal.

## Engenharia nativa utilizada

Confirmadas no editor as classes UsdStageImportOptions, UsdStageAssetImportFactory,
UsdStageImportFactory e UsdAssetUserData. Codigo instalado conferido em
Engine/Plugins/Importers/USDImporter/Source/USDStageImporter/Private/
USDStageAssetImportFactory.cpp e Public/USDStageImportOptions.h.
A factory recebe AssetImportTask.Options e chama o importador USD nativo.
Nao foi instalado plugin, alterado projeto ou convertido modelo pelo Blender.

`importar` aceita USD com `modo_usd:malhas` explicito. Importa assets sem atores,
mantem unidades da fonte e nao colapsa partes por kind. Nao promete montagem de
atores ou juntas Chaos. Dependencias ausentes recusam antes de importar.
Malhas retornam `prim_paths` nativos para rastrear partes/instanciamento; multiplos
prims podem compartilhar um asset. FTS atualiza somente o candidato afetado.

`inspecionar_usd` acrescenta AABB mundial em cm, no eixo nativo do USD e tempo
padrao, para comparar depois com o resultado real. Nao transforma AABB em prova
de ergonomia nem de adequacao ao pedido humano.

## Confirmacoes independentes

Ambos os USDs abriram pelo pxr instalado no Unreal: Z para cima, 1 metro/unidade,
18 prims Mesh, cinco juntas declaradas e nenhuma dependencia ausente.
Estante: quatro revolutas e uma fixa. Mesa: quatro prismaticas e uma fixa.
Nenhum script Python incluido no pacote baixado foi executado.

Estante importada como assets em /Game/Director/Acervo/ArtVIPBookcase007_20261021:
12 StaticMeshes e cinco materiais. Todas as malhas possuem pelo menos um convexo;
isso nao comprova colisao funcional. Identidade SQL original preservada.

Ensaio separado, temporario em codigo, usou a mesma factory com import_actors=True
no level exclusivo /Game/Director/Cenas/L_acervo_usd_20261021. Este ensaio nao e
uma funcionalidade de montagem adicionada ao Director. Gerou dois atores, 18
componentes de malha e zero PhysicsConstraintComponents. Componentes nao estavam
simulando fisica; nao chamar imobilidade de teste de estabilidade dinamica.

Dimensoes mundiais da estante:

| Eixo | Fonte USD (cm) | Montagem Unreal (cm) |
|---|---:|---:|
| X | 258,948771 | 258,948770 |
| Y | 29,770308 | 29,770299 |
| Z | 292,521366 | 292,521358 |

Conversao de escala aprovada no ensaio com tolerancia previamente usada de 2 cm.
Y foi refletido pelo motor, preservando dimensao. Isso compara fonte/importacao;
nao confirma tamanho desejado para uma sala ou medida fisica do fabricante.

Colisao interior REPROVADA no escopo amostrado: raio em x=-64,y=-15,z=250 ate185
com colisao simples comeca sobreposto ao corpo da estante; por triangulos, percorre
54,3 cm ate a prateleira em z=195,7. Em x=64, simples tambem comeca sobreposta,
enquanto por triangulos nao ha acerto no segmento. Portanto a colisao simples
obstrui regioes livres da geometria. Nao substituir silenciosamente por colisao
complexa para aprovar: corpos dinamicos e custo exigem ensaio proprio.

Registrados no SQL, com evidencia e escopo: escala_montagem_usd aprovada;
colisao_interior_nao_obstrutiva e juntas_chaos_geradas_pela_factory reprovadas.
Nao foram convertidas em aprovacao global do objeto.

## Testes e limites

Dez casos unitarios de operacao exercitados: nove passaram na primeira rodada;
uma assercao nova confundia R: com o UNC equivalente e foi corrigida. Esse caso
passou isoladamente; o caso de importacao USD tambem passou apos permitir ID sem
caminho. Sem relaxar verificacao de hash ou ambiguidade.

O fluxo pelo Hermes apos a correcao ainda sera medido; importar malhas nao basta
para declarar “estante utilizavel para guardar objetos” ou “mesa com gavetas”.
Articulacao funcional, estabilidade dinamica e conservacao de montagem pela
ferramenta objeto permanecem pendentes. Issue36 nao esta concluida.
