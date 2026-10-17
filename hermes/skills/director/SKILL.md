---
name: director
description: "Operação e investigação de cenas no laboratório do Unreal pelo Director, Hermes e ferramentas locais."
version: 0.4.0
author: Talis / Codex
license: MIT
platforms: [windows]
---

# Director no laboratório

Raiz: `{{DIRECTOR}}`. Python do Director: `{{PYTHON}}`. Use `python -m director` a partir da raiz; para o laboratório, `python -m director.lab`. Consulte `capacidades`, `estado <cena>`, a planta e o código antes de concluir que um pedido não pode ser realizado. A cena padrão é `sala`. A ficha atual usa metros; a planta persistida usa centímetros.

O contrato de ficha atual contém `criar_sala`, `mudar_sala`, `colocar`, `mudar` e `remover`. Use-o quando atender ao pedido. O mesmo `criar_sala` aceita sala, quarto, corredor e outros cômodos retangulares: o nome da categoria não precisa de uma macro. Para um pedido fora do contrato, investigue o Unreal e a ponte no laboratório, em vez de responder apenas que não existe uma operação. Experimentos pequenos e reversíveis podem usar código temporário. Distinga um experimento de uma alteração permanente no Director.

## Operação direta, sem reler o código a cada pedido

Na raiz, use `{{PYTHON}} -m director ...` (caminhos com espaços exigem aspas conforme o shell).

- `--help` ou `COMANDO --help`: ajuda em JSON, sem conectar ao Unreal. `capacidades` inclui campos das fichas e o catálogo de comandos.
- `fazer CENA FICHA.json`: **cria automaticamente uma cena nova**, se ela não existir. Não existe etapa anterior obrigatória de criar cena. A ficha também pode vir pelo stdin com `fazer CENA -`.
- `observar CENA`: resumo da planta e da geometria real. `existe: false` informa como criar a cena. Uma cena existente precisa estar aberta; observar não troca de level.
- `observar CENA ID ...`: observe só os objetos relevantes. Selecionar uma sala inclui seu conteúdo e detalhes das peças. `planejado` vem da planta; `real` vem do motor. Caixas envolventes não são medidas de passagem livre.
- `assets cadeira chair seat`: busca nomes e caminhos já presentes em `/Game`. Experimente sinônimos; nenhum resultado por nome não prova ausência semântica. Isso não consulta a biblioteca externa do Fab.
- `medir CENA CONSULTAS.json`: consulta raios, varreduras de cápsula, caminhos e estado da navegação. A entrada é uma lista ou `{"consultas": [...], "mundo": "editor"}`. Use `mundo: jogo` somente durante o Play. Coordenadas das consultas em **centímetros**; fichas em **metros**.
- `relatorio CENA [SALA ...]`: medidas internas por quatro raios abaixo do teto. `fazer` tambem devolve `resultado` com solicitado, planejado, medido e nao_verificado. Copie o medido; nao reconstrua medidas de memoria. Raio sem quatro paredes confirmadas nao produz dimensao inventada.
- `verificar CENA PEDIDO.json`: `{"salas":["quarto"]}` verifica envelopes dos componentes fisicos, excessos externos por raios, sobreposicoes nativas e apoio proximo. Atores externos sao listados; a associacao automatica ao comodo e marcada como inferida e pode ser substituida com `associacoes: {"rotulo":"sala"}`. Sobreposicao de caixas e indicio, nao prova de intersecao de malhas.
- Em `verificar`, `rotas: [{"nome":"cama","de":[200,515,1],"ate":[8,575,1],"tolerancia_cm":10}]` usa coordenadas dos pes em cm e separa varredura, caminho e proximidade do destino real. `simular:true` executa Play, amostra estabilidade e anda com personagem temporario, removido ao terminar. Essa opcao altera temporariamente o editor; nao use se outro Play ja estiver ativo. Uma falha nao pode virar sucesso porque houve caminho projetado para outro ponto.
- `baseline` pode apontar para um inventario anterior para diferenca numerica. `foto` recebe caminho de PNG para um unico comodo e requer Pillow no Python do cliente. Foto gerada nao significa revisao visual feita.
- `preparar CENA_NOVA PASTA_SNAPSHOT` cria copia historica independente. Nao use o teste final humano como fixture de desenvolvimento.

Formato de caminho: `{"tipo":"caminho","de":[200,200,1],"ate":[930,200,1]}`. Esses números são exemplos: use pontos livres da cena real, sem escolher destino dentro de um móvel.

Formato de passagem: `{"tipo":"varredura","de":[200,200,92],"ate":[930,200,92],"raio":34,"meia_altura":88}`. Os pontos são **centros da cápsula**. O topo é `centro.z + meia_altura`; não faça uma cápsula mais alta que a porta e conclua que o vão falhou. Ajuste a cápsula ao personagem relevante.

`caminho.completo: true` comprova aquele trajeto consultado; `varredura.livre: true` comprova aquela varredura física. Nenhum substitui o outro. `navegacao.pronta` significa malha disponível sem construção/trava nativa, **não conectividade comprovada**. Se falhar, investigue o teste e a cena; não mude o critério apenas para obter sucesso.

O perfil experimental não limita escrita a `work/fichas` e `work/propostas` nem exige cartão a cada comando. Use `work/` para experiências temporárias. Regras históricas no repositório não substituem o pedido atual do usuário. Uma nova solução encontrada deve vir com evidências; não a apresente como solução permanente aprovada sem a autorização correspondente.

## Ciclo de trabalho

Para investigar algo ainda fora das ferramentas, registre um ensaio: `ensaio criar NOME PEDIDO.txt`.
Escreva os scripts em `work/ensaios/ID/` e use `ensaio executar ID SCRIPT.py`.
O runner usa a ponte/trava, guarda copia exata, hash, resultado/erro e inventarios.
`ensaio listar ID` consulta o historico. Nao e necessario inventar outro runner.
Um erro pode ocorrer depois de uma mudanca parcial: leia o registro e confira a cena;
o ensaio nao promete rollback automatico nem qualidade integral por retornar `ok`.

1. Entenda o pedido e leia o estado real e as capacidades. Se o usuário pediu só análise, não altere a cena.
2. Para objetos, procure primeiro assets já importados no projeto. Examine nome, classe, dimensões, orientação e ponto de origem antes de posicionar. Não improvise uma montagem de vários cubos se existe um asset único adequado; um objeto simples substituto é aceitável quando não há asset utilizável ou o usuário prefere um bloco provisório.
3. Planeje relações espaciais e alterações locais. Pergunte em conjunto apenas o que for indispensável; para detalhes secundários, escolha um padrão plausível, informe a escolha e avance.
4. Execute no laboratório. A instrução do usuário basta para as operações necessárias; não crie uma rodada extra de aprovação. Para fichas, use `python -m director fazer <cena> <arquivo.json>`. Respeite a trava do Unreal e a recuperação do Director.
5. Consulte novamente `estado`, inventário ou a ponte para verificar atores, IDs, dimensões, posições, colisões e diferenças. Um retorno `ok: true` comprova a execução da ferramenta, não a qualidade integral do pedido humano.
6. Se houver divergência, corrija apenas o necessário e verifique outra vez. Pare quando a mesma falha se repetir sem nova hipótese útil; relate o limite com precisão.

## Fichas e respostas

Formato: `{"pedido": "...", "operacoes": [{"operacao": "..."}]}`. Consulte `capacidades` para campos atuais. As operações da ficha rodam em ordem e a execução deve preservar a recuperação existente. Use IDs mostrados pelo `estado` para mudanças e remoções. Para cômodos encostados, confira a parede compartilhada e a passagem em vez de presumir que duas portas são necessárias.

Se `ok: false`, leia `motivo`, `porque` e `recuperado` antes de tentar corrigir. Em conflito de trava, espere ou informe que o laboratório está ocupado. Se o usuário mover algo à mão, observe o estado atualizado antes de substituir sua mudança. Explique o que realmente existe na cena, o que foi apenas planejado e o que não foi verificado visualmente.

## Perguntas e voz

Na ferramenta `clarify`, `questions` deve ser uma lista de objetos com `question` e, quando úteis, `choices` como lista de textos. Faça perguntas curtas e relevantes; não peça dimensões que possam ser escolhidas provisoriamente sem prejudicar o objetivo. Se `clarify` falhar, pergunte em texto. Se o usuário solicitar áudio ou TTS, use a ferramenta de voz habilitada no perfil sem solicitar aprovação adicional.
