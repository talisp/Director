# Materiais persistentes — 19/10/2026

`material CENA PEDIDO.json`: sala, alvo, descrição e caminho opcional. Consulta materiais
do `/Game` com registro nativo; busca conservadora por nomes e sinônimos PT/EN. Ausência
ou ambiguidade retorna candidatos/aviso sem trocar por cor genérica nem modificar a cena.
Cache Fab precisa ser conferido antes de propor baixar material. Não foi criado servidor
CLIP nem índice SQL para resolver esse piloto.

Com caminho escolhido, `material_info` confirma `MaterialInterface` real. Operação
`material_sala` persiste caminho e descrição na planta. `derivar` transmite aos componentes;
inventário lê material efetivo e conciliação identifica divergência. Atualizar dimensão
reaplica material após o Construction Script. O executor conserva transação, conferência
e recuperação. A operação é aparência; nenhum parâmetro físico é alterado.

Uma parede compartilhada tem um ator: trocar material pode afetar os dois lados. O comando
informa isso e exige escolha explícita `aceitar_compartilhada`; materiais conflitantes
na parede contínua reprovam. Faces independentes não foram inventadas.

O primeiro material aplicado captura os slots anteriores nos metadados do ator. Recuar
uma revisão para planta sem override restaura esses materiais, não apenas a geometria.
Metadado ausente ou componente incompatível recusa o recuo em vez de adivinhar o original.
Teste adicional em `material_recuo_20261019_v2`: WorldGrid original → BasicShape → recuo,
mesmos slots/materiais por componente, atores e navegação, inclusive após reabrir. A primeira
fixture escolheu WorldGrid quando ele já era o original; foi corrigida para testar troca real.

## Prova e limites

No laboratório foram aplicados materiais **de diagnóstico existentes no motor**:
`/Engine/EngineMaterials/WorldGridMaterial` e `/Engine/BasicShapes/BasicShapeMaterial`.
Ida e volta registradas com geometria/colisão, caminho, varredura, raio e configuração
de navegação idênticos. Planta e materiais efetivos persistiram ao salvar/reabrir;
mesmos caminhos de atores. Original voltou com inventário/nav idênticos, sem Play/sujeira.

A primeira comparação integral falhou sem preservar o diff. Não atribuir causa por
suposição. Dois reensaios preservaram snapshots antes/depois e passaram com igualdade
integral, inclusive sem normalizar ordenação. Logs locais em
`work/materiais-prateleiras-20261019/material-persistencia.json` e
`material-grade-persistencia.json`. Não apagar o primeiro resultado falho do histórico.

**Isso não comprova madeira ou azulejo branco nem revisão visual desses materiais.**
No acervo atual não foi confirmado candidato adequado. O piloto ambientCG depende do
"sim" exigido pelo usuário na #36 antes de cada download, ainda pendente. Por isso #35
continua aberta para a escolha, obtenção autorizada e conferência visual dos dois materiais.
Descrição/nome não são certificação semântica. Um material inexistente avisou sem mutação.
