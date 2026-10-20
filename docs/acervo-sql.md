# Acervo SQL local

SQLite da biblioteca padrao do Python; sem servidor, pacotes novos ou inferencia.
Destino padrao: `R:\CINF\BD\Director\acervo.sqlite3`. Pode ser escolhido por
`DIRECTOR_ACERVO_DB`. Se R: nao existir, a operacao falha; nao cria um acervo em C:.
O banco, indices e downloads nao entram no Git.

## Consulta pelo agente

`python -m director acervo buscar cadeira` devolve ate oito candidatos compactos.
`python -m director acervo resumo` informa contagens e integridade.
`python -m director acervo pedido PEDIDO.json` executa uma operacao explicita;
`pedido -` le JSON da entrada padrao. Essas operacoes sao offline.
`acervo coletar PEDIDO.json` tambem oferece leitura do laboratorio ja aberto; nao inicia o editor.
Nomes/categorias em ingles e aliases PT/EN atuais do Director permitem busca inicial.
Nao foram geradas descricoes bilingues por LLM para o acervo inteiro.
FTS5 e SQL parametrizado; nao entrega o banco inteiro ao agente.
Uma copia congelada de `acervo.py` e do vocabulario pode ser instalada em
`R:\CINF\BD\Director\ferramentas`; aceita os mesmos argumentos diretamente:
`python R:\CINF\BD\Director\ferramentas\acervo.py buscar cadeira`.
Assim o Hermes pode chama-la pelo terminal sem instalar MCP, mudar o perfil
ou usar codigo de um checkout em desenvolvimento. Atualizacoes dessa copia sao explicitas.

## Modelo e procedencia

- `fontes`, `objetos`: origem + ID original preservados; mesmo nome nao une modelos.
- `tags`: idioma e procedencia. Classificacao sugerida nao comprova funcao.
- `arquivos`: caminho, SHA-256, tamanho, presenca observada. Duplicacao so por hash;
  arquivo alterado gera outra identidade local; registros anteriores ficam no historico.
- `instalacoes`: caminho do asset e projeto conforme indice consultado; snapshot nao e
  garantia de instalacao atual. Nao mistura caminhos `/Game` de projetos diferentes.
- `instancias`: ator e level; separa planta planejada de snapshot observado.
  Atores da cena nao entram automaticamente como modelos pesquisaveis.
- `caracteristicas`: valor, procedencia e evidencia; mantem os dados antigos sem
  apresenta-los como novas medidas. Orientacao/suporte HSSD nao certificam o Unreal.
- `verificacoes`: capacidade, resultado, versao, evidencia e data; nao testado difere
  de aprovado. Um teste de colisao nao aprova animacao nem todo o objeto.
- `registros`: versoes de importacoes e receitas preservadas, sem duplicar reimportacao
  identica da mesma fonte. Banco nao apaga candidatos por ausencia numa varredura parcial.

Licenca HSSD CC BY-NC 4.0 permanece explicita. A importacao do indice nao aceita termos
em nome do usuario, nao autentica Hugging Face e nao autoriza uso comercial dos modelos.
Licencas dos arquivos locais permanecem por objeto, sem herdar a de outro arquivo.

## Carregar dados existentes

Pedidos JSON:

```json
{"acao":"hssd","indice":"R:/CINF/BD/SceneSmith/HSSD-HSM/data/preprocessed/hssd_wnsynsetkey_index.json"}
```

```json
{"acao":"indice","indice":"CAMINHO/indice.json","projeto":"CAMINHO/DirectorLab.uproject"}
```

`indice` reaproveita a biblioteca offline e os snapshots do catalogo existentes.
Arquivos locais sao hasheados de novo; SHA divergente e arquivo ausente sao relatados,
sem declarar disponibilidade. O indice original nao e modificado.

```json
{"acao":"plantas","pasta":"CAMINHO/cenas","projeto":"CAMINHO/DirectorLab.uproject"}
```

Le plantas salvas (sem Unreal); cada repeticao atualiza as instancias e preserva versoes.
Objetos presentes apenas em plantas nao sao apresentados como assets importados.

## Novos downloads e pastas locais

O download autorizado deve salvar em R:, e registrar o ID selecionado no catalogo:

```json
{"acao":"arquivo","objeto":"ID_SQL","caminho":"R:/CINF/BD/modelos/ID.glb","origem":"sessao/download e URL","licenca":"licenca da fonte"}
```

Pode fornecer `sha256` esperado. O comando verifica o arquivo e vincula ao candidato
remoto sem criar outra identidade. Nao verifica dependencias ou executa importacao.
Baixador autenticado HSSD nao faz parte desta entrega. Desde 20/10, importacao
explicita GLB/glTF e download seletivo ArtVIP estao em `acervo_operacao.py` (abaixo).
Depois da importacao futura, registrar explicitamente o mesmo `objeto`:

```json
{"acao":"instalacao","objeto":"ID_SQL","projeto":"CAMINHO/DirectorLab.uproject","caminho":"/Game/Director/Objetos/SM_Exemplo","origem":"ensaio/importacao"}
```

Isso liga arquivo e instalacao a mesma identidade antes de atualizar o catalogo do editor.
Se o caminho ja estiver ligado a outro objeto, informa conflito; nao une silenciosamente.

Para arquivos sem catalogo remoto, `{"acao":"varrer","pasta":"R:/CINF/BD/minha_pasta","limite":200}`
registra hashes numa pasta explicitamente escolhida. Evita links/junctions de diretorios.
Formatos GLB/GLTF/FBX/OBJ/USD/BLEND sao apenas identificados, nao executados/carregados.
Nao varre C: inteiro e nao deduz licenca pelo nome. Arquivos externos do GLTF/OBJ devem
continuar juntos; a varredura nao certifica completude desse conjunto.

## Criacoes na cena

1. Sincronizar `plantas` ou importar um indice `catalogo atualizar` posteriormente.
2. Consultar `{"acao":"instancias","nivel":"/Game/Director/Cenas/L_sala"}`.
3. Promover explicitamente uma instancia:

```json
{"acao":"promover","instancia":"ID_SQL_INSTANCIA","nome":"Mesa com copo","origem":"sessao/ensaio ou usuario","tags":["mesa","table"]}
```

Guarda a definicao registrada e o contexto de dependencias `sobre`/`sala` da planta.
Receitas sao candidatos nao testados: nao exportam meshes nem garantem portabilidade,
fisica ou recompilacao. Mantem os caminhos de assets referenciados. Uma composicao que
precise reunir varios objetos independentes exige definir seu conjunto antes de promover;
nao presume que o nome de um ator contenha toda a composicao.
Mudanca na planta do alvo antes da promocao exige nova sincronizacao.

Promocao a receita continua explicita. Desde 20/10, a CLI sincroniza a planta
depois de `fazer`, `objeto`, `incorporar` e `material` bem-sucedidos. Chamadas diretas
a modulos ou edicoes externas exigem `sincronizar`/coleta; nao ha monitor em segundo plano.

## Recuperacao

Mutacoes de cada pedido usam transacao; falha fatal reverte o pedido. Importacao de
indice local pode registrar itens validos e devolver erros por arquivo, com `ok:false`.
Repetir importacao identica e idempotente. Fontes permanecem intactas.
Comandos de consulta abrem SQLite em modo somente leitura. Para copia de seguranca
consistente de um banco em uso, usar a API `sqlite3.Connection.backup`, nao copiar
um arquivo enquanto houver transacao ativa. O SQL nao substitui backups dos modelos.

## Verificacao

`python -m unittest director.testes.testes_acervo -v` cobre IDs duplicados, hashes,
modificacao de arquivo, vinculo de download futuro, promocao/historico/dependencias,
consulta PT/EN compacta, verificacoes com evidencia e falhas de integridade.
Nao sao provas de geometria, fisica ou importacao no Unreal.

## Coleta incremental — schema 2

`acervo coletar PEDIDO.json` registra cada rodada em `coletas`, o estado por escopo
em `itens_coleta` e cada tentativa/ausencia em `inspecoes`. Cada item confirmado e
commitado: falha ou interrupcao posterior nao perde os anteriores. Rodadas antigas
abruptamente encerradas podem continuar com estado `em_andamento`; a proxima rodada
reaproveita os itens confirmados sem depender desse estado de rodada. Nao ha retry
infinito: erros sao elegiveis na proxima execucao explicita. Lock nativo impede duas
coletas simultaneas do mesmo escopo e e liberado pelo SO quando o processo termina.

```json
{"coletor":"arquivos","pasta":"R:/CINF/BD/Director/arquivos","limite":50}
```

Hashes incluem o modelo e dependencias externas glTF (BIN/texturas). A versao do
inspetor inclui codigo, Python, trimesh e numpy; mudancas invalidam o cache. A segunda
rodada ainda le arquivos para conferir integridade, mas nao carrega a geometria de novo.
GLB/glTF 2.0: bounds por trimesh, materiais e presenca de skins/animacoes por metadados.
FBX/OBJ/USD/BLEND: apenas inventario/hash com `nao_suportado` para inspecao geometrica.
Isso nao aprova nem dispensa a inspecao futura. Nao roda Blender nem scripts dos assets.
Os workers usam o mesmo Python do coletor e prazo de 60 s por modelo.
Usar o Python existente `.venv-biblioteca/Scripts/python.exe`, que ja possui trimesh.

Arquivo novo ou modificado gera inspecao; sucesso inalterado e reaproveitado. `forcar:true`
permite reavaliacao explicita. Dependencia ausente/fora da pasta autorizada ou URI remota
produz erro sem carregar a malha. Arquivo que muda durante a inspecao nao e certificado.
Formato sem suporte e preservado no inventario e so sera reavaliado ao mudar versao,
conteudo ou quando houver `forcar:true`. Nao marca ausentes se o inventario foi parcial,
inacessivel ou interrompido pelo limite. Ausencia preserva objeto e historico.

```json
{"coletor":"unreal","pasta":"/Game","limite":100}
```

Reutiliza Ponte/trava do laboratorio. Exige editor aberto, sem Play/pacotes pendentes.
AssetRegistry inventaria sem carregar todas as malhas. Assinatura usa bytes dos pacotes
salvos, arquivos auxiliares e dependencias transitivas `/Game`, mais versao do motor.
Dependencias `/Engine` e `/Script` sao representadas pela versao do motor, sem auditoria
de alteracoes locais no motor. Referencias dinamicas fora do registry nao sao certificadas.
Carrega por vez apenas classes com inspetor: StaticMesh (bounds, LOD, materiais, colisao
configurada), SkeletalMesh (bounds, skeleton/PhysicsAsset), AnimSequence (duracao/skeleton)
e PhysicsAsset (contagens acessiveis). Campos indisponiveis ficam explicitamente nao
verificados. Nao instancia Blueprints, nao roda Construction Scripts nem simula fisica.
As outras classes ficam inventariadas com estado `nao_suportado`.

A ferramenta congelada em R: aceita os mesmos pedidos. O coletor Unreal reutiliza a
ponte da instalacao fixa `Director-publicado` (ou `DIRECTOR_OPERADOR`), sem modificar
essa instalacao ou o perfil Hermes. O script de leitura do editor fica junto da
ferramenta em `ferramentas/editor/acervo_inspecao.py`. Atualizacao de conteudo importado
no projeto ainda nao e feita por este coletor.

Prova real em 19/10/2026: 86 assets inventariados no laboratorio, 33 com inspecao
especializada e 53 sem inspetor dessa classe. Repeticao reutilizou os 86. Arquivos:
6 GLB/glTF inspecionados e 1 FBX inventariado sem backend; repeticao reutilizou os sete.
Um glTF previamente copiado sem BIN/texturas foi recusado; quatro dependencias locais
foram copiadas e verificadas antes da inspecao bem-sucedida. Historico do erro preservado.
Lote sintetico separado em R: comprovou adicao, modificacao, ausencia, erro e retomada
com GLBs reais. Inventario da cena, level e navegacao permaneceram identicos; sem
pacotes pendentes. Nao houve Hermes/LLM, download ou importacao de novos assets.

## Catalogos externos — schema 3

`acervo fontes PEDIDO.json` importa snapshots preparados por `acervo_fontes.py`:

```json
{"pasta":"R:/CINF/BD/Director/fontes/REVISOES_DO_SNAPSHOT"}
```

Para atualizar os metadados publicos, sem baixar malhas nem comprar pacotes:

```
python R:\CINF\BD\Director\ferramentas\acervo_fontes.py baixar R:\CINF\BD\Director\fontes
```

Leitura YAML usa PyYAML 6.0.3 (`requirements-acervo.txt`). Nesta instalacao, dependencia
isolada em R:\CINF\BD\Director\dependencias, sem mudar ambientes Hermes ou instalar
globalmente. Se nao encontrar PyYAML no Python, a ferramenta procura essa pasta.

- ArtVIP original: API publica de arquivos, revisao fixa, um objeto por USD principal;
  nao confunde USDs de recurso, origem ou materiais com novos objetos. Registra nomes,
  grupos/subcategorias, arquivos da pasta, tamanhos, hashes LFS quando fornecidos e
  revisao. A lista da pasta nao certifica fechamento de referencias USD/MDL externas.
  Articulacao e uma declaracao do dataset, ainda nao inspecionada no Unreal.
- Code4Scene: lista de pacotes e paletas text-to-scene. Pacotes ficam em `pacotes`;
  objetos referenciados ficam em `objetos` ligados por `referencias_pacote`. Nao sao
  registrados como baixados/importados. Caminhos Blueprint sao normalizados ao pacote,
  preservando o spawn path original. Dimensoes sao declaracoes externas em cm, sem
  sobrescrever medidas locais. Precos/licencas/versoes de engine permanecem historicos
  e atribuídos a fonte, sem afirmar que os anuncios Fab foram conferidos agora.
- Categorias originais e uma taxonomia pequena PT/EN sao pesquisaveis; sugestao de tag
  nao e comprovacao de funcao. Nenhuma LLM foi utilizada para essas traducoes.
- Coincidencias com assets locais usam prefixo de caminho literal (nao LIKE com `_`
  como coringa), sem concluir posse, licenca ou igualdade da revisao. O cruzamento so
  cobre as instalacoes registradas, nao toda a conta Fab ou o projeto cinematografico.

Cada snapshot preserva revisoes e SHA-256. Importacao e transacional e repeticao do
mesmo snapshot/importador reaproveita o resultado sem duplicar dados. Codigo4Scene
nao distribui os pacotes 3D. O arquivo-fonte baixado pode conter gabaritos do benchmark:
nao o fornecer ao agente em um teste Code4Scene. O SQL recebe apenas referencias de
assets/pacotes, sem prompts completos nem rubricas de avaliacao.

Em 19/10/2026 foram encontrados 476 USDs principais em ArtVIP e 2.959 caminhos unicos
nas paletas Code4Scene. Foram lidas 150 tarefas; nove nao possuem paleta individual
embutida. Portanto isso nao e um inventario completo de todos os assets de cada pack.
49 registros de pacotes incluem 48 de terceiros e o Starter Content. Repositorios e
manifestos de origem sao preservados em R:, sem redistribuir modelos no Git.
As paletas contem 15.006 entradas brutas; repeticoes dentro do mesmo caso/caminho
foram consolidadas em 14.844 vinculos de referencia. Nenhum desses numeros representa
arquivos 3D baixados. O cruzamento inicial nao encontrou pastas coincidentes no
laboratorio registrado; nao permite concluir que o usuario nao possui packs no Fab.

## Operacao do acervo — 20/10/2026

Use a CLI da instalacao fixa publicada, nao Python arbitrario do editor:
`python -m director acervo pedido PEDIDO.json`. As novas acoes abaixo nao estao na
copia congelada anterior em R:; ela conserva o inventario/consulta anteriores.

1. `{"acao":"planejar_download","objeto":"ID_SQL"}`: plano ArtVIP com revisao fixa,
   arquivos/tamanhos/hash/licenca declarada. Sem rede nem download neste planejamento.
2. `{"acao":"baixar","objeto":"ID_SQL","autorizar_download":true,
   "origem":"autorizacao/sessao","max_bytes":100000}`: baixa apenas o selecionado,
   preserva estrutura e verifica SHA256 LFS ou hash Git dos arquivos pequenos.
   Cache por arquivo verificado; recusa divergencias em vez de sobrescrever.
   Lock nativo por objeto, transacao SQL ao final e temporarios na pasta R:.
   Destino padrao `R:/CINF/BD/ArtVIP/REVISAO/`; sem aceite/autenticacao HSSD nem compra Fab.
3. `{"acao":"importar","objeto":"ID_SQL","arquivo":"R:/CINF/BD/.../modelo.glb",
   "destino":"/Game/Director/Acervo/NomeNovo","origem":"ensaio/sessao"}`:
   revalida hash/dependencias glTF e usa `AssetImportTask`/Interchange instalado.
   Recusa pasta existente, Play ou pacotes pendentes. Salva apenas assets novos;
   nunca presume mesh unico nem cria atores. Mais de uma malha pode pertencer ao
   mesmo candidato. Falha pode deixar assets novos parciais: confira o destino;
   nao repita importacao nem apague automaticamente assets para esconder o erro.
4. `{"acao":"inspecionar_usd","objeto":"ID_SQL","arquivo":"R:/.../modelo.usd"}`:
   usa pxr incluido no Unreal para ler unidades, malhas, juntas e fechamento de
   dependencias. Nao importa/simula juntas no Chaos. Requer plugin USD disponivel.
5. `{"acao":"sincronizar","cena":"NOME"}`: captura somente planta persistida e
   referencias de meshes. Instancias sao snapshots historicos, nao assets novos;
   `estado_cena` registra o conjunto atual e a revisao, sem apagar versoes antigas.
   A CLI chama esta captura depois de mutacoes bem-sucedidas. Se SQL falhar, conserva
   sucesso da cena e retorna `acervo.ok:false` com instrucao de repetir so o registro.
6. `{"acao":"rotular"}`: aliases de categorias existentes em lote, com procedencia
   `sugerida`. Nao afirma material, funcao, articulacao ou dimensao pelo nome.

A consulta inclui as tres verificacoes mais recentes e seus escopos; resultado
parcial nao deve ser interpretado como certificacao universal de fisica. O download
verifica arquivos da pasta do objeto; somente a inspecao USD verifica referencias
resolvidas naquele ambiente. Um objeto com dependencias ausentes nao esta pronto.

Fontes de API: docstrings do UE 5.8.3 instalado consultadas em 20/10;
`AssetImportTask` e `AssetTools.import_asset_tasks` testados no laboratorio.
`GLTFImportOptions` nao existe nessa instalacao: nao foi usado um caminho antigo
com essa classe. USD inspecionado via `pxr` fornecido pelo plugin USDCore instalado.

Os arquivos de origem, banco, caches, copias, evidencias e backups ficam em R:.
Os pacotes `.uasset/.umap` novos pertencem ao Content do projeto laboratorio
existente; nao se moveu o projeto nem alterou o projeto cinematografico.

Provas, numeros e limites: [piloto de operacao](acervo-operacao-2026-10-20.md).
