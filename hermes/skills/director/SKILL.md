---
name: director
description: "Operação e investigação de cenas no laboratório do Unreal pelo Director, Hermes e ferramentas locais."
version: 0.5.8
author: Talis / Codex
license: MIT
platforms: [windows]
---

# Director no laboratório

## Regras que valem acima de tudo (teste de 17/10)

- **Leia o `veredito` antes de qualquer coisa.** `planejar` e `verificar` começam com `veredito`
  (APROVADO, REPROVADO ou ERRO), `motivo` e `proxima_acao`. `ok: true` só diz que a ferramenta
  rodou. **Nunca diga ao usuário que algo passou sem `veredito: APROVADO`.** Se reprovou, diga
  o `motivo` com as palavras e os números dele e siga a `proxima_acao`.
- Leia tambem `diagnosticos`: aviso nao e excecao fatal, nem `ok:true` apaga avisos.
  Os grupos incluem mensagem original, contagem e trecho do log; a correlacao e apenas temporal.
  Explique o impacto e formule uma hipotese antes de corrigir. Repita so a verificacao afetada;
  sem hipotese nova, pare e relate o bloqueio. Se a ponte cair depois de mudar algo, confira o estado
  antes de repetir: nao prometa rollback de ensaio. Nunca afrouxe criterio apenas para aprovar.
- **Diga de onde veio cada objeto:** asset já existente no projeto (com o caminho), objeto
  composto pelo Director, ou reaproveitado de um ensaio anterior. Não diga "importado do Fab"
  sem ter importado.
- **Use as ferramentas prontas.** Não escreva busca, solver ou script de layout próprio:
  `planejar` já testa tamanhos e arrumações. Script próprio só por `ensaio` e quando
  nenhuma ferramenta faz o pedido; diga por quê.
- **Esperas de no máximo 60 s.** A guarda do perfil barra `sleep` acima de 60 s e reduz
  `process wait` para 60 s. Acompanhe um processo com `process wait` (até 60 s), confira e,
  se terminou, siga na hora.
- **Uma alteração por cena de cada vez.** A guarda barra um segundo comando que altera a
  mesma cena enquanto outro roda em segundo plano. Nunca mude a sala na cena para "testar"
  tamanhos: use `planejar` com `sala` + `minimo_cm`/`maximo_cm`, que não toca na cena.

Raiz: `{{DIRECTOR}}`. Python do Director: `{{PYTHON}}`. Use `python -m director` a partir da raiz; para o laboratório, `python -m director.lab`. Ao retomar, consulte `contexto`: ele informa o level aberto e o caminho real da planta. Nao assuma que a cena e `sala` nem leia uma copia de planta do checkout quando houver fonte vinculada. Consulte `capacidades`, `estado <cena>` e `api TERMO` antes de concluir que falta uma operacao ou escrever codigo experimental. A ficha atual usa metros; a planta persistida usa centímetros.

**Compor varios comodos sem macro:** `planejar CENA PEDIDO.json` aceita
`{"salas":[{"id":"sala","largura_m":4,"comprimento_m":3},{"id":"cozinha","largura_m":3,"comprimento_m":3}],"adjacencias":[{"salas":["sala","cozinha"],"lado":"leste"}]}`.
Lado e opcional; contato minimo padrao 120 cm. A saida `ficha_salas` ainda NAO foi aplicada;
use-a inteira em `fazer` para preservar revisao_base. Se a revisao mudou, replaneje.
Salas existentes ficam com cantos fixos; uma mudanca de tamanho pode ser recusada por vizinhos/moveis.
Adjacencia nao e passagem: para integrar ambientes, `colocar tipo:passagem` corta a parede
sem criar folha/ator. Escolha parede/posicao/largura e confirme no motor. Minimo 70x178 cm
so considera capsula 34/88; nao garante navegacao. O planejador e retangular, em cm, ate 32 salas;
nao prometa vila completa nem casa funcional apenas por obter APROVADO na distribuicao.

Para abrir o laboratorio, use `python -m director.lab estado` e `abrir`; nao lance outro projeto.
Se precisar esperar, acompanhe em intervalos de ate 60 s. Depois consulte `contexto`.
Depois de cada rodada, execute `python hermes/instalar_perfil.py director --conferir` com o mesmo Python do Director.
O comando mostra diferencas sem instalar. Registre aprendizados como propostas com sessao/ensaio,
medidas e limites; uma nota local nao vira regra permanente por si so. Nao edite a skill para
contornar recusa de conciliacao. A autorizacao atual de desenvolvimento continua valendo para o escopo autorizado.

Aprendizado conferido no teste do banheiro de 17/10 (#7/#10): mover moveis pode deixar
uma rota desatualizada. Se a varredura passa e o caminho falha, diagnostique `navegacao` antes
de mover objetos novamente. Reconstrucao e ajuste de resolucao sao coisas diferentes:
guarde o backup e declare qualquer mudanca de celula e escopo. Celula 5/altura 2 funcionou
naquele level; nao e padrao universal e o custo de memoria nao foi medido.

Se a carga terminou mas a rota segue ausente, `navegacao PEDIDO.json` aceita
`{"acao":"reconstruir","prazo_s":20}` sem mudar resolucoes. Depois consulte a rota nos
dois sentidos: `pronta` nao prova caminho. Nao remova parede para fazer o teste passar.
Refino regional pode precisar de `tile_cm` explicito: perfis que geram tamanhos efetivos
de tile diferentes sao recusados antes de alterar o motor. Leia a proposta do erro;
950 funcionou com celulas 38/19/5 naquele ensaio, nao e valor universal. Alterar tile_cm
afeta a grade de todo o level, mesmo com escopo regiao. O backup/restaurar inclui esse valor.

O contrato de ficha atual contém `criar_sala`, `mudar_sala`, `colocar`, `mudar` e `remover`. Use-o quando atender ao pedido. O mesmo `criar_sala` aceita sala, quarto, corredor e outros cômodos retangulares: o nome da categoria não precisa de uma macro. Para um pedido fora do contrato, investigue o Unreal e a ponte no laboratório, em vez de responder apenas que não existe uma operação. Experimentos pequenos e reversíveis podem usar código temporário. Distinga um experimento de uma alteração permanente no Director.

## Operação direta, sem reler o código a cada pedido

`objeto CENA PEDIDO.json` adota, duplica, coloca asset ou compoe pecas, ja registrando
o resultado na planta. Exemplo: `{"acao":"adotar","id":"cadeira","ator":"Cadeira_mesa1","sala":"sala1","categoria":"cadeira"}`.
Para duplicar, use `acao:duplicar`, `ator` de origem, novo `id`, `sala`, `x_m` e `y_m` relativos ao comodo.
Para colocar asset use `acao:colocar` e `asset:/Game/...`; dimensoes sao medidas do asset, com ajustes opcionais
`largura_m`, `profundidade_m`, `altura_m`, `giro`. Para compor, `partes` recebe centros/tamanhos em cm:
`{"centro_cm":[0,0,45],"tamanho_cm":[40,40,5]}`; o merge e a colisao composta sao nativos do Unreal.
Perfis de massa sao estimativas ajustaveis por `massa_kg` (nao medidas do material real); informe a categoria.
Outros campos: `simular`, `subir`, `amortecimento_linear` e `amortecimento_angular`.
**Em cima de um móvel:** `"sobre":"cama1"` põe o objeto no tampo do móvel registrado (no centro, ou em
`x_m`/`y_m` da sala), com física; ele vai junto quando o móvel muda. Ex.: travesseiro na cama, notebook
na escrivaninha. Não escreva script do editor para isso.
**Peça fixa:** `"fixo":true` (padrão para as categorias box, box_chuveiro, chuveiro, vaso_sanitario, pia,
bancada, divisoria, parede) registra sem simular física: o box é parte da casa, não um móvel que cai.
O `verificar` só exige que ela fique parada.
Malha dinamica pode virar StaticMesh pela GeometryScript nativa; comportamento de Blueprint nao e transferido.
Use `mudar`/`remover` pelo ID para objetos registrados; mover o comodo nao autoriza apagar seu conteudo.
Depois use `verificar` para confirmar geometria, apoio e fisica. Recusa da planta nao comprova falta de asset.

Na raiz, use `{{PYTHON}} -m director ...` (caminhos com espaços exigem aspas conforme o shell).

- `--help` ou `COMANDO --help`: ajuda em JSON, sem conectar ao Unreal. `capacidades` inclui campos das fichas e o catálogo de comandos.
- `fazer CENA FICHA.json`: **cria automaticamente uma cena nova**, se ela não existir. Não existe etapa anterior obrigatória de criar cena. A ficha também pode vir pelo stdin com `fazer CENA -`.
- `observar CENA`: resumo da planta e da geometria real. `existe: false` informa como criar a cena. Uma cena existente precisa estar aberta; observar não troca de level.
- `observar CENA ID ...`: observe só os objetos relevantes. Selecionar uma sala inclui seu conteúdo e detalhes das peças. `planejado` vem da planta; `real` vem do motor. Caixas envolventes não são medidas de passagem livre.
- `observar CENA --texto SALA`: desenho compacto da planta, escala declarada, norte em cima,
  legenda por id, dobradica/folha e zonas reservadas. Use antes de propor ou depois de mudar
  disposicao quando ajudar; nao releia em toda consulta. E plano desejado, nao foto nem leitura
  do editor: combine com estado/medidas e nao declare uma zona livre so por estar desenhada.
- `observar CENA --texto SALA --real`: consulta o inventario e desenha moveis conciliados
  apenas em memoria; nao grava nem adota a planta. Recusa outro level ou Play. Moveis ausentes
  nao sao desenhados; paredes/salas continuam referencia planejada, nao faces medidas.
  Confira `conciliacao`, `fora_do_plano` e `limite`. `relacoes_compartilhadas` associa cada
  sala ao SEU lado e ao vizinho; nao atribua os dois lados da relacao ao mesmo comodo.
  Use imagem quando acrescentar evidencia; screenshot nao substitui medidas/colisao.
- `assets cadeira chair seat`: busca nomes e caminhos já presentes em `/Game`. Experimente sinônimos; nenhum resultado por nome não prova ausência semântica. Isso não consulta a biblioteca externa do Fab.
- `procurar cadeira`: consulta unica atualizada, cena primeiro, depois projeto e indice offline. Retorna ate oito candidatos; categorias sugeridas por sinonimos nao sao prova de equivalencia. O nome anterior de um objeto adotado permanece como apelido. `catalogo atualizar` apenas refaz o indice local. Para filtros, `procurar consultar PEDIDO.json` aceita `{"texto":"chair","maximo_cm":[60,60,100],"limite":5}`; dimensao desconhecida nao satisfaz filtro numerico.
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

### Pedidos locais e estado desatualizado

Para abrir uma porta conhecida, consulte `observar CENA ID` e use `fazer` com `{"operacoes":[{"operacao":"mudar","id":"porta1","angulo":90}]}`; o ID e exemplo. Nao releia o codigo inteiro se a ferramenta atender.
Se houver `diagnostico.codigo: planta_editor_divergentes`, confira o caminho da planta, revisao e level retornados.
Pecas ausentes nao provam exclusao manual: uma copia antiga da planta pode nao conhecer as paredes compartilhadas.
Nao reponha paredes nem use um script direto para esconder a divergencia. Compare uma planta conhecida com o inventario antes de propor recuperacao e informe o bloqueio se nao houver fonte confiavel.
`estado CENA` fornece contexto e conciliacao; `observar`/`procurar` ja fornecem inventario. Evite escrever outro inventario.
Em experimento necessario, consulte `ensaio --help`: o retorno do editor e `resultado = {...}`, nao `print`.

### Andamento visível para o usuário

Antes de cada script Python ou chamada do Director, envie uma frase curta no
chat explicando a finalidade. Exemplos: "Mapeando o quarto", "Verificando os
móveis existentes", "Posicionando cama e criado-mudo", "Conferindo as colisões",
"Testando se o boneco chega à escrivaninha". Consultas feitas num mesmo lote
podem compartilhar um aviso. Não use apenas comentários no script ou raciocínio
interno, que o usuário pode não ver. Não acrescente uma pergunta de aprovação.

Depois da resposta da ferramenta, diga o resultado relevante: "Encontrei uma
cadeira na cena", "Esta distribuição bloqueia a passagem; vou tentar outra" ou
"O boneco ainda não chegou ao armário". Diga "Concluído" somente para o que foi
comprovado. Em processos demorados, aproveite o acompanhamento nativo disponível
e informe mudanças reais de etapa; não repita consultas nem crie temporizadores
apenas para produzir mensagens. Não prometa transmissão ao vivo de prints de
scripts do editor quando a ponte só devolve a saída ao terminar.

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

`planejar CENA PEDIDO.json` propoe distribuicao por CP-SAT (OR-Tools em
`.venv-planejamento`). Nunca altera a cena. Giros 0/90/180/270 (a frente aponta
para sul/leste/norte/oeste); por padrao cada movel fica com as costas na parede.
Exemplo de quarto compacto numa sala que ja existe, sem mexer nela:
`{"sala":"quarto","minimo_cm":[220,260],"maximo_cm":[320,380],"segundos":30,"objetos":[
{"id":"cama1","dimensoes_cm":[100,200,82],"uso_frente_cm":65},
{"id":"criado1","dimensoes_cm":[40,41,44],"uso_frente_cm":35,"ao_lado_de":"cama1"},
{"id":"guarda1","dimensoes_cm":[100,62,200],"uso_frente_cm":65},
{"id":"escrivaninha1","dimensoes_cm":[100,55,75],"uso_frente_cm":75},
{"id":"cadeira1","dimensoes_cm":[50,50,83],"uso_frente_cm":0,"na_frente_de":"escrivaninha1"}]}`
- `na_frente_de`: a cadeira fica encostada na frente da mesa, virada para ela.
- `ao_lado_de`: o criado-mudo fica junto da cama, do lado da cabeceira.
- Com `sala` e sem `minimo_cm`/`maximo_cm`, usa as medidas reais da sala (precisa do editor).
  Com eles, testa o tamanho com as portas reais, sem abrir o editor; `origem` diz qual foi.
- Moveis ja registrados na sala e fora do pedido ficam reservados (`mantidos_da_cena`). Para
  replanejar um movel existente, use o MESMO id dele no pedido.
- Quando o filtro 2D reprova, o proprio planejar tenta outras arrumacoes (`tentativas`).
  Se ainda reprovar, siga a `proxima_acao`; nao varra tamanhos com lacos no terminal.
- Para aplicar: `mudar_sala` (se o tamanho mudou) e `objeto`/`mudar` com `x_m`, `y_m` e `giro`
  da proposta, relativos ao canto sudoeste da sala; depois `verificar` com `simular` e rotas
  da porta ate cada `ponto_uso_cm`. O planejar nao prova trafego real.

Formato: `{"pedido": "...", "operacoes": [{"operacao": "..."}]}`. Consulte `capacidades` para campos atuais. As operações da ficha rodam em ordem e a execução deve preservar a recuperação existente. Use IDs mostrados pelo `estado` para mudanças e remoções. Para cômodos encostados, confira a parede compartilhada e a passagem em vez de presumir que duas portas são necessárias.

Se `ok: false` ou `veredito` diferente de APROVADO, leia `motivo`, `porque` e `recuperado` antes de tentar corrigir. Em conflito de trava, espere ou informe que o laboratório está ocupado. Se o usuário mover algo à mão, observe o estado atualizado antes de substituir sua mudança. Explique o que realmente existe na cena, o que foi apenas planejado e o que não foi verificado visualmente.

## Perguntas e voz

Portas: a ficha aceita `dobradica:inicio|fim` e `sentido:dentro|fora`, alem de `angulo:0..120`.
Omitir preserva o comportamento anterior de cada parede. Os termos inicio/fim seguem a medida
do vao (oeste->leste em norte/sul; sul->norte em leste/oeste). Use `planejar` e `planta2d` com
essas escolhas antes de executar; a folha na posicao solicitada nao pode colidir com movel registrado.
Nao ha teste continuo do arco de abertura. Confirme passagem com o motor/boneco.
`avisos` pode informar janela em parede compartilhada: pergunte ou declare a escolha de janela
interna. Nao e erro fatal nem janela externa comprovada.

Na ferramenta `clarify`, `questions` deve ser uma lista de objetos com `question` e, quando úteis, `choices` como lista de textos. Faça perguntas curtas e relevantes; não peça dimensões que possam ser escolhidas provisoriamente sem prejudicar o objetivo. Se `clarify` falhar, pergunte em texto. Se o usuário solicitar áudio ou TTS, use a ferramenta de voz habilitada no perfil sem solicitar aprovação adicional.

`navegacao PEDIDO.json` diagnostica, ajusta (`escopo: regiao` ou `level`) e
restaura (`acao: restaurar`, `backup: caminho retornado`). Guarde o backup. Level
altera toda a malha; regiao tambem altera o perfil HIGH compartilhado e tiles
atingidos. Nao conclua sucesso por `pronta`: use varredura, caminho e boneco via
`verificar`. Refinamento regional ainda nao resolveu o caso norte-sul auditado;
nao aplicar ajuste global sem declarar esse escopo ao usuario.

Antes de inventar chamada Python, use `api TERMO` (ex.: `api get_linear_damping`).
`api atualizar` gera a referencia no editor instalado; consultas depois sao
offline, curtas e com versao/data. Para outras classes: `api atualizar PEDIDO.json`
com `classes: [nome, ...]`. Nao achar algo no recorte nao prova inexistencia.

`biblioteca indexar PEDIDO.json` inspeciona arquivos locais sem Unreal (fontes:
lista com arquivos, licenca, proveniencia; blender opcional para FBX). Requer
`.venv-biblioteca` com requirements-biblioteca.txt. `biblioteca cadeira` consulta
offline; `procurar cadeira` inclui esses candidatos ao atualizar. Baixado nao
significa importado nem com fisica; confira escala artistica, licenca e geometria.
Nao escolha estante como guarda-roupa apenas pelo alias. Kenney da amostra requer
reescalonamento. Banco/RAG permanente ainda nao decidido.

`play_start`/`play_stop` devolvem `controle_cpu.aplicado`, `atual`, `anterior` e
`restaurado`. Falha desse controle nao significa que Play falhou. O valor e
restaurado em memoria, sem gravar preferencias. Consumo CPU nao foi aferido.

`python -m director planta2d CENA SALA` e o filtro offline anterior ao Unreal:
pegadas, areas diante de portas (80 cm) e janelas (50 cm), regioes e bloqueadores.
Usa Shapely no ambiente opcional do planejamento. Movel abaixo do peitoril nao
bloqueia a janela. So considera objetos registrados: proxies fora da planta
exigem dados adicionais, e verificacao no motor. Dentro do `planejar`, o filtro
aprova quando da porta se chega a area de uso de cada movel (`acessos`); um canto
isolado sem uso nao reprova. A cadeira `na_frente_de` nao conta como bloqueio (e
afastada para usar a mesa). Mantenha `verificar` com boneco. A regra de janela
somente em parede externa nao faz parte desta implementacao parcial da #29.
