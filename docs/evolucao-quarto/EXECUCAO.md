# Evolucao do Director a partir do ensaio do quarto

## Pedido revisado de execucao

Implementar, nesta ordem, #22, #23, #26, #25, #13, #21 (#19/#20), #12,
#10, #24, #27 e #28. Usar os corpos e comentarios das issues como criterios.
Uma entrega local por issue ou grupo pequeno, sem push, PR, merge nem fechamento
de issue ate autorizacao humana explicita. Nao incluir caminhos pessoais ou logs
brutos no GitHub. Preservar alteracoes preexistentes no checkout.

O teste final humano e o pedido literal de quarto registrado no anexo original.
Preparar uma cena separada a partir da revisao anterior aos quartos; nao executar
esse pedido pelo Hermes. Os quartos de referencia permanecem para auditoria.

Correcoes ao prompt original:

- O nucleo ja compartilha paredes. Medir segmentos em comum; nao presumir que o
  quarto Sol tem quatro paredes independentes.
- Contencao/sobreposicao ja existem para mesa na planta. Generalizar para objetos
  adotados e geometria medida, distinguindo limites de caixas envolventes.
- A skill v0.3.1 nao declara mais restricao a duas subpastas de work. Conferir a
  guarda instalada antes de atribuir um bloqueio ao codigo vigente.
- Verificacao barata e somente leitura nao equivale a Play: simulacao, ator de
  teste e alteracao de level sao etapas explicitas, com restauracao e registro.
- Erro de script experimental nao e automaticamente defeito do Director.
- Teste unitario/editor falso prova contrato e calculos, nao geometria nem Unreal.
- #22 so fecha apos novas sessoes reais dos agentes; a sessao atual em acesso
  completo nao comprova o comportamento de sandbox de uma nova sessao.
- Pesquisar primeiro componentes prontos. A biblioteca offline e uma prova
  pequena, sem banco/embeddings/gerenciador proprio decidido antecipadamente.

## Registro inicial

Baseline: 49 testes de nucleo/interface passam. Configuracoes globais nao foram
alteradas. Cada criterio so sera marcado comprovado com sua evidencia; pendencias
ficam explicitas. Nenhum PR foi publicado.

## #22 — configuracao dos agentes

Codex: `.codex/config.toml` usa workspace-write, rede habilitada e approval_policy
never. Rede habilitada NAO significa regra restrita a localhost. Exige confianca
no projeto; politicas gerenciadas e configuracoes do app podem prevalecer. Nao
forcar uma implementacao Windows: a documentacao atual distingue MXC e fallbacks.

Claude: `.claude/settings.json` permite comandos do Director e testes por Bash e
PowerShell. Nao concede acesso total nem instala dependencias. Regras com um
interpretador especifico de venv precisam corresponder ao comando realmente usado.

Para ativar, abrir uma NOVA sessao confiando no projeto. Se houver bloqueio,
registrar comando, cliente/versao e politica efetiva; nao repetir aprovacoes sem
diagnostico. A prova de zero prompts em duas novas sessoes continua pendente.

Fontes oficiais conferidas em 17/10/2026:
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/windows/windows-sandbox
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/permissions

## #23 — ensaios

`python -m director ensaio criar nome pedido.txt`

`python -m director ensaio executar ID script.py`

`python -m director ensaio listar ID`

O runner copia os bytes executados para `work/ensaios/ID/execucao-UUID/script.py`,
registra SHA256, resultado/erro, inventarios anterior/posterior e IDs alterados.
Nao e scheduler, nao executa automaticamente, nao aplica rollback silencioso.
O registro local pode conter caminhos privados e permanece ignorado pelo Git.

Validacao: 52 testes de nucleo/interface/ensaios passaram (49 anteriores + 3 novos).
No Unreal, uma leitura registrou 47 atores e a cadeira existente, sem alteracoes;
um RuntimeError provocado foi registrado com hash e inventarios sem mudanca.
O teste unitario adicional provoca erro depois de mutar o editor falso e comprova
que a mudanca parcial fica no registro; nao e prova geometrica do motor.
Nao foi demonstrado ainda o comportamento da guarda de um novo perfil Hermes.

## #26 — resultado medido

`fazer` devolve resultado solicitado/planejado/medido/nao_verificado; `relatorio`
permite consultar depois sem alterar o level. Quatro raios em altura superior aos
moveis precisam confirmar paredes. Ausencia de medida nao vira dimensao planejada.
Medido na referencia Sol: 260 x 350 cm; fixture nova: 400 x 400 cm. Teste negativo
usa paredes medidas com 305 cm contra plano de 320 cm e nao aprova a divergencia;
um raio em movel nao produz medida interna. 54 testes passam com #25 inicial.

## #25 — verificacao por escopo

`verificar` agrega geometria de componentes com colisao (sem billboards),
contencao, raios exteriores, sobreposicoes de colisao nativas, apoio proximo,
varredura, caminho, destino efetivo da projecao, Play e chegada. `aprovado` vale
somente para o escopo informado; nao afirma que foram testadas interacoes como
sentar, deitar ou abrir gavetas. A estabilidade usa duas amostras e limites
explicitados no codigo, nao comprova todas as perturbacoes possiveis.

Reproducao somente leitura da cena de referencia: cama Hermes 24 cm e escrivaninha
15 cm alem da face exterior da parede, ambos confirmados por raio. Sol: cinco
moveis dentro, apoio proximo e sem intersecoes de colisao com profundidade de
envelopes acima de 0,5 cm. O contato com o piso nao foi classificado como penetracao.

Nova cena `auditoria_quarto` preparada da rev14, SHA256 do mapa de origem
752678eba4b8381aee98829eee1a04d46fe0f74ea776148ed7d4e2662f22fb41.
Fixture isolada com mesa sem fisica foi corretamente reprovada pelo Play;
personagem parado a 200 cm foi reprovado, mesmo com estado IDLE. A travessia dessa
porta ainda falhou na navegacao e segue para #10; nao foi mascarada como sucesso.
O erro do controle de CPU de #28 reapareceu no resultado do teste. Foto PNG
recortada foi produzida pelo cliente com Pillow; revisao visual nao executada.

Pendencias da #25: teste positivo completo com moveis gerenciados (#13), percurso
positivo da fixture (#10), variacoes de objetos rotacionados/compostos e baseline
antes/depois no fluxo final. Nao declarar a issue totalmente resolvida ainda.

## #13 — objetos gerenciados

`objeto CENA PEDIDO.json` inspeciona antes de registrar, usa o executor existente
com recuperacao e inclui o objeto no planejamento, conferencia, mudanca/remocao.
Identidade/categoria/apelidos/modelo/perfil fisico ficam na planta. Medidas e pivo
sao obtidos da malha, evitando assumir que o pivo fica no centro. A massa padrao e
uma estimativa declarada, substituivel pela pessoa.

Na copia rev14, a cadeira existente revelou ser DynamicMeshActor (nao varias
StaticMeshes). Conversao por GeometryScript e decomposicao convexa nativas
permitiram adotar sua geometria e materiais, com massa 8 kg e identidade na planta.
Duplicacao em outro comodo preservou a origem e registrou um novo ID. Um banco
de cinco partes foi unido pelo merge nativo e registrado como um corpo de 8 kg.
Um cubo com centro a 3,9 m numa sala de 4 m foi recusado antes de criar o ator.
O estado voltou sem diferencas entre planta e editor apos as operacoes positivas.

Limites: conversao de geometria nao transfere logica de Blueprint; inicialmente
trata orientacao vertical (yaw), com limites declarados para objetos inclinados.
Perfis fisicos padrao ainda requerem validacao especifica para materiais/escala.
Uma falha de inventario durante desenvolvimento expos necessidade de recuperar
tambem erro ao conferir; esse caminho agora solicita a recuperacao existente.

## #21 — consulta unica (#19/#20)

`procurar cadeira` atualiza metadados da cena e AssetRegistry e consulta um indice
local pequeno. Cena vem antes do projeto, independente da pontuacao nominal.
Aliases PT/EN e nomes anteriores dos objetos adotados sao preservados. Nomes,
classes e dimensoes sao dados do motor; categorias por sinonimos sao sugestoes.
Filtros dimensionais excluem dimensoes desconhecidas. O indice JSON deste lote
nao decide banco permanente nem implementa embeddings, scheduler ou novo RAG.

Teste no editor: consulta cadeira retornou quatro candidatos, com os tres objetos
da cena antes do asset do projeto. A cadeira adotada mantem Cadeira_mesa1 como
apelido; o teste da cena final rev14 ainda precisa confirmar o nome original.
Teste negativo: geladeira nao retorna candidatos no catalogo reduzido de cadeiras;
limite 40 x 40 cm exclui cadeira de 50 x 50 cm e asset sem dimensoes. 56 testes
passaram. A prova de novo asset apos atualizacao fica para o lote offline #27.

## #12 — planejamento espacial

Adotado OR-Tools CP-SAT 9.15.6755 em ambiente opcional isolado, evitando escrever
um solver de empacotamento. Fontes oficiais verificadas em 17/10/2026:
https://github.com/google/or-tools/releases/tag/v9.15 e
https://developers.google.com/optimization/cp/cp_solver/ .

`planejar CENA PEDIDO.json` mede salas existentes, reserva portas e moveis da
planta, propoe retangulos e areas de uso frontal; nao aplica a proposta. Pode
minimizar area dentro de limites, com orientacoes 0/90 graus. Compartilhamento de
paredes vem da planta; requer conferencia posterior no motor. Objetos externos
nao registrados e forma real complexa ainda exigem verificacao #25. Nao prova
minimo global arquitetonico. Dois testes positivos/negativos passaram no ambiente
opcional; consulta no editor propos armario e criado sem mudar a cena.

## #10 — navegacao com escopo (parcial)

`navegacao PEDIDO.json`: diagnosticar, ajustar regiao por NavModifierVolume nativo,
ou level explicitamente, e restaurar backup persistido antes da mudanca. Guarda
parametros, raio e atores criados. Regiao afeta tiles e outros modificadores HIGH
que compartilhem o perfil; nao promete isolamento geometrico exato.

Na copia: padroes 38/19/19 cm, altura 10, raio 35. Ajuste de todo level para
2/2/2 cm e altura 2 foi explicitamente testado, salvo e reaberto: boneco chegou
nas duas orientacoes a 7,3 e 6,8 cm, tolerancia 10. Tempo observado do pedido ate
nav pronta: 0,52 s (nao e benchmark de CPU/memoria/FPS). Restauracao devolveu
38/19/19 e altura 10. Regiao de tamanho zero foi recusada.

Pendente: refinamento apenas regional nao corrigiu norte-sul nesta instalacao;
leste-oeste chegou a 7,3 cm. Nao declarar #10 corrigida. Ensaios por componente
e volume, com classe de area nula/default, estao registrados. Nao repetir esses
ensaios sem nova evidencia. O primeiro componente usou area Null padrao e cortou
a malha; corrigido, experimentos removidos e configuracao original restaurada.

Fontes consultadas em 17/10/2026:
https://dev.epicgames.com/documentation/unreal-engine/navigation-mesh-resolutions-user-guide
https://issues.unrealengine.com/issue/UE-214913
https://forums.unrealengine.com/t/changing-navmeshresolutionparams-cellsize-in-ini-fails-to-generate-new-bvquantfactor-which-breaks-findnearestpoly/2653823
A API instalada confirma modificadores e resolucoes; os relatos nao provam a
causa local. Preferida a navegacao nativa, sem construir outro pathfinder.

## #24 — referencia da API instalada

`api atualizar [PEDIDO.json]` exportou 2.844 entradas de 26 classes da instalacao
5.8.3 para cache de 1.264.357 bytes, sem enviar o texto inteiro ao modelo.
`api TERMO` consulta offline e devolve ate cinco trechos de 1.800 caracteres.
Lista de classes pode ser ampliada por arquivo, sem editar documentacao manual.
Consulta get_linear_damping encontrou metodos reais; simbolo inventado retornou
zero. Alias massa -> mass testado. Os textos sao gerados; execucao/contexto nao
sao garantidos pela documentacao. Nao indexa automaticamente todos os plugins.

## #27 — prova pequena offline, sem Unreal

Reutilizados trimesh 5.1.1 (release 02/10/2026, Python 3.13 Windows testado) e
Blender instalado 5.2.2 LTS para FBX em processo separado, sem UI. Considerado
ASSETMCP: busca, manifestos e inspecao ja existem, mas sem release e com issue #1
sobre inicializacao MCP 2.x; nao instalado nem adotado como infraestrutura nesta
prova. O adaptador aqui so chama leitores existentes e integra o catalogo #21.

Cinco GLB Kenney + licenca: 103.553 bytes baixados de commit fixo
3694c6879e487c108f55677be7dd2ca75b07cc3b. Recursos dos GLB da amostra embutidos.
Mais um FBX do cache Fab existente: poltrona de 20.711.724 bytes, 199.817 triangulos,
114,57 x 66,16 x 176,40 cm. Total seis modelos: 20.814.564 bytes; inspecao 9,969 s.
Cama Kenney mede 57,10 x 112,50 x 37,50 cm: requer escala escolhida e conferida.
BookcaseClosedDoors e estante fechada; nao foi certificado como guarda-roupa.

`biblioteca indexar PEDIDO.json` usa fontes com arquivos explicitos, proveniencia,
licenca e Blender opcional; cache guarda hash, caminho, medidas, materiais,
triangulos, estado baixado_nao_importado e preview quando disponivel. Nao fabrica
preview ou prova de direitos Fab a partir de arquivo em cache. Consulta biblioteca
funciona sem ponte; procurar inclui o indice offline quando atualiza. Novo asset
Kenney cama apareceu na consulta unificada. Geladeira nao retornou candidatos;
arquivo ausente reprova e preserva indice anterior. Nao foi instalado banco SQL,
embeddings, sincronizador ou novo servidor RAG. A amostra nao mede escala de milhoes.

Pesquisa verificada em 17/10/2026:
- https://github.com/shorepine/kenney : ultimo commit 30/08/2026, CC0, caminhos
  estaveis; e espelho de assets Kenney. Preservada licenca local.
- https://kenney.nl/assets/furniture-kit : origem oficial do pacote.
- https://polyhaven.com/our-api : mudanca de 18/07/2026 permite API tambem para uso
  comercial, exigindo credito ao usar API ao vivo. Assets sao CC0. Pagina atual
  prevalece sobre relato antigo de restricao comercial; termos devem acompanhar
  qualquer futura integracao. Nao baixamos toda a biblioteca nesta prova.
- https://github.com/allenai/objaverse-xl : ultimo release 0.1.7 de 01/11/2023,
  ultimo commit observado 27/08/2024. Dataset ODC-By, objetos com licencas diferentes.
  Nao tratar todos os objetos como CC0 nem recomendar baixar tudo sem selecao.
- https://trimesh.org/trimesh.exchange.load.html e
  https://github.com/mikedh/trimesh/releases/tag/5.1.1 : leitor pronto. Issues
  abertas incluem memoria em GLB grande e limites geometricos; bounds aqui sao
  envelopes, nao prova de colisao ou adequacao ao jogo.
- https://github.com/evonar543/ASSETMCP e issue #1: alternativa mais abrangente,
  candidata futura; nao ha comparacao de producao que justifique trocar a ponte.

Recomendacao para o proximo lote: Kenney selecionado, Poly Haven selecionado por
qualidade/escala/custo de arquivos; Objaverse somente com filtro por objeto e
licenca. Cache Fab ja pode ser consultado localmente, sujeito aos direitos de cada
compra. Nao prometer que todos os tres acervos estao baixados ou prontos no Unreal.

## #28 — controle de CPU no Play

Reproducao em play_start e play_stop: "DeveloperSettings: Failed to find property
 'throttle_cpu_when_not_foreground' for attribute 'throttle_cpu_when_not_foreground'
 on 'EditorPerformanceSettings'". Texto original preservado no registro local,
sem caminhos privados no comentario da issue.

Cabecalho e objeto reais da instalacao confirmam bThrottleCPUWhenNotForeground.
A classe nao tem wrapper Python especifico: alias snake_case falha, nome refletido
C++ funciona. Ajustado esse acesso, sem trocar por CVar de efeito diferente.
Play medido: anterior=true -> atual=false com aplicado=true; stop atual=true e
restaurado=true. Sem SaveConfig; mudanca de sessao. Falha eventual retorna
aplicado=false e erro especifico sem mascarar resultado do Play. Testes cobrem
valores anteriores true/false e propriedade indisponivel; nao medem consumo CPU.

## Validacao integrada e entrega

Na copia independente `auditoria_quartos` da revisao 17 (nao no level original):
#25 reprovou cama 24 cm e escrivaninha 15 cm para fora da parede leste, com raios
confirmando ambos. Quarto Sol aprovado com cinco corpos fisicos estaveis e quatro
caminhos completos; boneco a 7,3 / 7,6 / 7,1 / 7,5 cm dos alvos (tolerancia 10).
Inventario antes/depois: zero criados, removidos ou alterados. A varredura agora
segue segmentos do caminho nativo: uma linha reta bloqueada nao reprova um
trajeto valido com curva. Caso negativo de segmento bloqueado tambem coberto.
Foto opcional gerada e inspecionada: recorte pequeno, sem prova visual de medidas;
as provas de contencao e circulacao sao as consultas do motor. Nao testado sentar,
abrir guarda-roupa ou deitar. A associacao dos proxies antigos aos quartos segue
inferida (eram objetos fora da planta); objetos novos podem ser registrados.

Teste final humano preparado em `hermes_quarto_final`, rev14, sem quarto criado.
Busca cadeira retornou primeiro Cadeira_mesa1 (DynamicMeshActor), depois asset do
projeto, depois chairDesk offline. Estado planta/editor sem diferencas. SHA256 do
snapshot confere; mapa e planta originais `sala` mantiveram os hashes do inicio
desta validacao. Pedido literal e instrucoes estao na pasta de ensaio final.

A skill fonte foi atualizada no repositorio. Nao foi reinstalada no perfil externo
nem iniciada nova conversa Hermes/Codex/Claude: nao comprovar #22 nem carregamento
da skill nova com esta sessao. Nenhuma configuracao global foi alterada.
Comentario original de reproducao #28 anexado a pedido do prompt:
https://github.com/talisp/Director/issues/28#issuecomment-6237793572 .
Sem push, PR, merge ou fechamento de issue. Branches locais sao empilhados: a
validacao integrada depende das etapas anteriores. Separacao de PRs devera
preservar essa dependencia e excluir as cenas locais de ensaio e mudancas
preexistentes. Issues adicionadas depois foram ignoradas conforme solicitado.

Status honesto: #22 pendente de sessoes novas; #10 pendente do refinamento
regional e benchmark CPU/memoria/FPS; #12 ainda e proposta retangular e nao uma
prova arquitetonica completa. #27 e somente seis modelos offline; nao e acervo
integral nem banco definitivo. Os demais resultados devem ser lidos com os limites
acima; testes falsos nao substituem os ensaios registrados no Unreal.

Exemplos dos comandos novos: COMANDOS.md. Evidencias extensas ficam em work,
fora do Git; o manifesto de scripts registra tambem helpers do cliente que nao
rodaram pelo executor Python do editor, sem inventar duracao retroativa.

Validacao final automatizada: 66 testes Director passaram no ambiente com solver;
no Python comum, 64 passaram e dois do solver opcional foram pulados. Quatro
testes do complemento Hermes passaram. Compilacao Python e diff --check sem erros.
Os testes de falha incluem erro depois de iniciar ajuste de navegacao com backup
persistido e erro ao pedir Play com restauracao do controle CPU (simulados).
Todos os scripts temporarios novos foram preservados na pasta oficial; manifesto
lista a versao atual e as execucoes pelo editor, distinguindo helpers de cliente.
As versoes do ensaio antigo tambem continuam em work/sol_20261017, sem exclusao.

## Aproveitamento da #29 como referencia para #12/#25

As novas #29, #30 e #31 foram lidas por solicitacao posterior do Talis. Somente
#29 forneceu codigo/metodo aproveitado neste lote; nao foi assumida implementacao
integral das tres. #30 (ASCII com comparacao Qwen) e #31 (notas/recuo por rodadas)
continuam fora deste lote. Nao executamos uma nova conversa Hermes.

Adaptados reachability.py e clearance_zones.py do SceneSmith, commit
67cc408fd38334b4a926efef45e284302ed5055b, MIT (Nicholas Pfaff, 2026), com aviso
integral em THIRD_PARTY_NOTICES.md. Shapely 2.2.0, release 07/10/2026, instalado no
ambiente opcional do OR-Tools; nucleo permanece biblioteca padrao. Comparada a
alternativa Clipper2/Pyclipr: Shapely ja fornece buffer/union/difference e coincide
com o algoritmo fonte, sem precisarmos implementar recorte ou outro pathfinder.
Fonte atual: https://shapely.readthedocs.io/en/stable/reference/shapely.buffer.html
https://github.com/shapely/shapely/releases/tag/2.2.0 . Issues de precisao/GEOS
reforcam a necessidade de nao equiparar buffer aproximado a colisao do motor.

`planta2d CENA SALA` roda sem ponte, medindo contencao de pegadas, area livre de
porta (80 cm), janela (50 cm, respeitando peitoril/altura), regioes e bloqueadores
individuais por retirada. Planejador reserva essas areas e filtra o resultado:
nao devolve objetos como proposta aprovada quando o filtro reprova. Nao busca
outra distribuicao automaticamente depois de reprovar; devolve diagnostico para
nova tentativa, sem prometer ausencia de outra solucao.

Testes: guarda-roupa na janela invade 40 cm e reprova; movel abaixo do peitoril
nao viola janela; porta invadida 60 cm reprova; cama transversal gera 2 regioes e
e identificada como bloqueio. Caso negativo passa apos reduzir a largura.
Fixture do Sol, com os cinco envelopes medidos e porta, passou offline: 1 regiao,
proporcao 1, area livre para centro da capsula 14.266,817 cm2; tempo observado
1,599 ms, nao benchmark estatistico. Fixture de navegacao regional tambem tem
uma regiao em 2D, embora o boneco norte-sul falhe com a malha padrao: separar
espaco livre de conectividade NavMesh e necessario.

Limites: comando da planta nao enxerga atores externos; o teste Sol usa fixture
explicita dos envelopes medidos, nao uma planta vazia tratada como prova. Uma
regiao conexa nao prova ligacao a porta ou a cada ponto de uso. Buffer circular
aproximado; nao testa fisica, giro de folha ou NavMesh. A regra de recusar janela
em parede compartilhada da #29 NAO foi incorporada nem marcada concluida.

Hipotese adicional #10 apos leitura da #29: codigo instalado de
NavModifierVolume.cpp confirma PostEditChangeProperty sem caso NavMeshResolution,
e SetAreaClass chama UpdateActorData. Testada atualizacao nativa depois de definir
HIGH, usando area Default neutra. Nao resolveu norte-sul (150 cm do destino),
embora leste-oeste chegasse a 7,3 cm. A hipotese nao basta para explicar a falha.
Configuracao restaurada e modificador de teste removido; nao declarar correcao
regional. Cena final limpa reaberta apos o teste. Mantido registro da sondagem,
sem insistir na mesma hipotese sem evidencia nova.
