# Retomada nativa do acervo — 22/10/2026

Base publicada: 5cdaeb0, Unreal 5.8.3. Escopo autorizado: retomar pipeline com
Luna no Hermes, orcamento limitado e sem tentativas repetitivas. Nesta primeira
entrega nao houve inferencia; somente duas fontes ArtVIP ja baixadas.

Backup SQLite consistente e snapshot de atores/transformacoes anteriores em
`R:/CINF/BD/Director/pipeline-20261022/`. Cena original: L_sala. Ensaios no level
separado `/Game/Director/Ensaios/Acervo20261022/L_AcervoNativo`.

## Coletor v2 e montagem

`preparar` sem importar executou o OpenUSD do Unreal, registrou variantes v2 e
fichas vigentes; repeticao reutilizou as inspecoes. A consulta de partes com
limite 1 preserva contagem total e pai; detalhe seletivo permanece disponivel.
O importador USD nativo com import_actors=true foi usado apenas no ensaio:
nao foi acrescentada uma operacao de montagem ao Director.

| Fonte | Dimensoes USD (cm) | Componentes montados | Maior erro dimensional (cm) | Constraints |
|---|---|---:|---:|---:|
| table4 | 200 x 55,83366 x 80,5 | 13 | 0,0000001342 | 0 |
| bookcase007 | 258,94877 x 29,77031 x 292,52137 | 18 | 0,000009495 | 0 |

Tolerancia previamente adotada: 2 cm por eixo; ambas passaram. Isto compara
AABB fonte/montagem no tempo padrao. Nao comprova ergonomia, todas as rotacoes
individuais, articulacoes Chaos ou estabilidade dinamica. Partes e matrizes
foram coletadas; a identidade de cada instancia compartilhando um StaticMesh
ainda exige cuidado ao associar prim_paths.

## Colisao: falha reproduzida, uma alternativa pronta testada

Na estante, raios verticais em x=+/-64, y=-15, z=250->185 iniciam sobrepostos na
colisao simples. Pela geometria complexa, x=64 fica livre e x=-64 alcanca a
prateleira apos 54,3 cm. Confirma o bloqueio falso ja observado em 21/10.

Testamos **uma unica configuracao nativa** em copias das duas malhas envolvidas:
StaticMeshEditorSubsystem.set_convex_decomposition_collisions, maximo 8 hulls,
16 vertices/hull, precisao 50.000. Originals preservados; copias em
`/Game/Director/Acervo/Colisao20261022`. Retorno true e cinco convexos por malha
nao corrigiram os quatro raios amostrados. Nao alteramos parametros repetidamente,
nao promovemos true a aprovacao e nao trocamos silenciosamente para colisao complexa.

Consequencia: a estante continua inadequada para interacoes no interior nesse
escopo. O operador deve escolher outro candidato quando essa capacidade for
necessaria. Corrigir a montagem/colisao requer experimento proprio; nao bloquear
todos os pedidos de cena tentando resolver esta unica estante.

## Checkpoint e proximo bloco

Item 1 do pipeline: evidencia nativa adicionada para dois objetos; falta a prova
completa por parte/variante importada. Item 2: problema funcional confirmado e
alternativa nativa limitada reprovada; articulacao continua pendente.
Proximo: pedido pequeno no Hermes/Luna com modelo existente e adequado, seguido
de correcao local e preservacao. Reusar a revisao/ensaios/identidade existentes
antes de adicionar representacao nova. Materiais, PA, Topview e pendencias
operacionais conservam seus criterios na #48.
