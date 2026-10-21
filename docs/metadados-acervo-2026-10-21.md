# Metadados para decidir, sem enviar o acervo inteiro a LLM

Estudo de 21/10/2026. Recomendacao arquitetural; nao altera o esquema SQL nem
implementa uma nova consulta nesta rodada. Continua as issues36/39/48.

## O que ja existe no Director

Inspecao somente leitura do SQLite em R:/CINF/BD/Director/acervo.sqlite3:

- `objetos`, `fontes`, `arquivos`, `instalacoes`: identidade/origem, licenca,
  hashes, bytes, arquivos locais e assets observados no projeto.
- `caracteristicas`: valores JSON com procedencia/evidencia. Ja guarda dimensoes,
  eixo/up/front, caixa USD, colisao configurada, dependencias e juntas declaradas.
- `verificacoes`: capacidade, resultado, evidencia, versao e data. Ja guarda
  escala aprovada dos dois moveis; apoio de cubo aprovado na mesa fixa;
  colisao interior da estante e geracao de juntas Chaos reprovadas no ensaio.
- `registros`: preserva resultados completos, incluindo dimensoes da montagem,
  tolerancias, partes e amostras fisicas em `ensaio_montagem_usd`.
- `instancias`/`receitas`: separam objeto de acervo, colocacao em cena e receita.

Evidencias no codigo: `acervo.caracteristica`, `registro`, `buscar`, `detalhe`;
`acervo_operacao.inspecionar_usd`, `importar`; `editor/acervo_usd.py` e
`editor/acervo_importacao.py`. Os ensaios manuais tambem gravaram provas no SQL;
essa organizacao manual nao deve ser descrita como automacao generica concluida.

Lacunas verificadas: `buscar` nao apresenta dimensoes/funcao ao selecionar um
candidato e limita verificacoes as tres ultimas linhas, independentemente da
capacidade. `detalhe` devolve todas as caracteristicas/instalacoes/verificacoes.
Uma falha relevante pode desaparecer da busca quando surgirem tres testes mais
recentes de outras capacidades. Escolher apenas o ultimo valor de dimensao tambem
nao resolve diferencas entre parte, conjunto, fonte e variante.

Medida somente leitura: JSON compacto da busca de oito mesas ArtVIP retornou
4.023 caracteres; `detalhe` completo da estante 15.575 e da mesa 16.834 caracteres.
Contagem de caracteres, nao de tokens. Isso justifica detalhe seletivo; nao prova
que qualquer resumo menor preserve as informacoes necessarias.

`caracteristicas` nao tem unidade/frame/variante/data como colunas obrigatorias;
parte disso esta nos nomes/procedencias/JSONs. `verificacoes.versao` e texto livre,
nao vinculo automatico ao hash/escala/configuracao testada. Ainda nao ha mecanismo
geral comprovado para invalidar testes apos mudar conversao, escala ou colisao.

## Fontes externas relidas, com revisao fixada

### SceneSmith

Revisao [67cc408fd38334b4a926efef45e284302ed5055b](https://github.com/nepfaff/scenesmith/tree/67cc408fd38334b4a926efef45e284302ed5055b),
commit de 20/05/2026, main consultada em 21/10. Licenca do codigo MIT, distinta das
licencas dos datasets. Codigo/documentacao lidos; nao executamos SceneSmith.

- [README, ArtVIP Setup](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/README.md#artvip-setup):
  ArtVIP pre-processado em Drake SDFormat, colisoes VHACD/CoACD e embeddings CLIP.
  Isso difere dos USDs originais x-humanoid-robomind/ArtVIP que baixamos.
  Exportacao para outros simuladores e descrita como experimental. Nao transferir
  automaticamente para Chaos uma alegacao de qualidade no Drake.
- [HssdRetrievalServerRequest/Result](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/agent_utils/hssd_retrieval_server/dataclasses.py):
  descricao, tipo, dimensoes desejadas, limite de candidatos; resultados com ID,
  categoria, tamanho e score. Aproveitar busca semantica seguida de compatibilidade
  geometrica, sem precisar importar outro servidor ou CLIP agora.
- [HssdRetriever](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/agent_utils/hssd_retrieval/retrieval.py):
  `_calculate_bbox_score` calcula distancia L1; menor e melhor. Nao e probabilidade
  de sucesso. O contrato de resultado articulado descreve bbox_score com outra
  convencao; a formula e ordenacao precisam ser conferidas por backend.
- [ArticulatedMeshMetadata/load_source_data](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/agent_utils/articulated_retrieval_server/data_loader.py):
  le `metadata_index.yaml` com descricao, montagem piso/parede/teto, manipulavel e
  bounding boxes do pre-processado. E um candidato concreto para aproveitar dados
  prontos sem estimar tudo novamente. Disponibilidade desse indice separado dos
  arquivos grandes ainda nao foi confirmada. O loader usa `yaml.unsafe_load`;
  nao copiar essa desserializacao para dados externos: normalizar formato/tipos
  com leitura segura, preservando revisao e vinculo ao derivado correspondente.
- [HssdMeshMetadata](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/agent_utils/hssd_retrieval/data_loader.py):
  indice basico tem ID/nome/up/front/WordNet. O ranking dimensional abre a malha;
  ter somente esse indice nao equivale a ter medidas ou superficies prontas.
- [HsmSupportSurfaceData e loader](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/agent_utils/hssd_retrieval/support_surface_loader.py):
  area, normal, cantos, horizontalidade e folga vertical, com tratamento de OBB e
  conversao de eixos. Nosso `support_region:true` do HSSD e apenas uma pista:
  nao contem a superficie utilizavel ou a folga. O pacote HSM de superficies nao
  foi importado/testado no Unreal nesta pesquisa.
- [ArticulatedPhysicsAnalysis](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/agent_utils/articulated_physics_analyzer.py):
  posicao de montagem, frente, escala, materiais e massa por link. A analise usa
  VLM e defaults, inclusive massa fallback de 5 kg: valores estimados, nao balanca
  ou certificacao. Guardar como estimativa com procedencia.
- [AssetRegistry.apply_scale_by_sdf_path](https://github.com/nepfaff/scenesmith/blob/67cc408fd38334b4a926efef45e284302ed5055b/scenesmith/agent_utils/asset_registry.py):
  atualiza entradas que compartilham um modelo reescalado e salva incrementalmente.
  Licao: variacao/conversao precisa atualizar os metadados e validade das provas.

SceneSmith e um pipeline de geracao/recuperacao/validacao; seu uso de modelos
treinados e resultados experimentais nao certifica cada asset em outro motor.

### Code4Scene

Revisao [2716e4397f768bf16b1f33dd34680d48aed0601f](https://github.com/SimWorld-AI/Code4Scene/tree/2716e4397f768bf16b1f33dd34680d48aed0601f),
03/10/2026, igual ao snapshot do nosso catalogo. Codigo Apache-2.0; pacotes Fab
mantem licencas/aquisicoes proprias. Codigo/documentacao lidos; benchmark nao rodado.

- [README](https://github.com/SimWorld-AI/Code4Scene/blob/2716e4397f768bf16b1f33dd34680d48aed0601f/README.md):
  benchmark de construcao/edicao no Unreal, com catalogos/pacotes e verificadores;
  nao e outra base de malhas redistribuidas nem um modelo de geracao ja treinado.
- [AssetCatalog.apply](https://github.com/SimWorld-AI/Code4Scene/blob/2716e4397f768bf16b1f33dd34680d48aed0601f/code4scene/evaluation/asset_catalog.py):
  separa categoria do catalogo das tags que o agente pode escrever. Aproveitar a
  procedencia, sem copiar a restricao do benchmark que reconhece apenas categorias
  de assets prontos: Director precisa aceitar composicoes novas quando validadas.
- [PlacedAsset/AssetCandidate](https://github.com/SimWorld-AI/Code4Scene/blob/2716e4397f768bf16b1f33dd34680d48aed0601f/code4scene/evaluation/requirement_graph/asset_candidates.py):
  identidade, asset, posicao/yaw, pegada e grupo. Score de metadados serve para
  localizar candidatos, nao prova cumprimento. O benchmark usa confirmacao visual;
  Director deve manter verificacao geometrica/fisica como principal quando suficiente.
- [SceneIdentityGroup.llm_payload](https://github.com/SimWorld-AI/Code4Scene/blob/2716e4397f768bf16b1f33dd34680d48aed0601f/code4scene/evaluation/identity_catalog.py):
  agrupa identidade e limita termos por origem. Aproveitar consulta compacta e
  rastreavel; nao criar uma nova camada de IDs opacos sem necessidade.
- [test_physics_probe_semantics.py](https://github.com/SimWorld-AI/Code4Scene/blob/2716e4397f768bf16b1f33dd34680d48aed0601f/tests/test_physics_probe_semantics.py):
  evita interpretar pasta/level contendo river/water como prova de objeto nao solido.
  Nomes e tags podem ajudar busca, mas nao devem decidir fisica.

Nao foram adotados scores, alegacoes de benchmark ou testes dos autores como
validacao independente do nosso ambiente. Evidencia independente e o ensaio local.

## O que guardar, e quando mostrar

| Grupo | Dados a persistir | Retorno inicial para LLM |
|---|---|---|
| Identidade e acesso | ID/fonte/revisao/hash, licenca, dependencia, local/remoto/importado observado, familia e variante | ID, nome PT/EN, disponibilidade e restricao acionavel |
| Geometria | Dimensoes, unidade/frame, AABB/OBB/pegada, frente/cima, pivot/minZ, parte versus conjunto, escala aplicada | Tamanho relevante com origem/estado; desconhecido explicito |
| Funcao e montagem | Categoria, papel, piso/parede/teto/sobre objeto, assento/recipiente/apoio, declaracao versus prova | Funcao relevante e limitacao; categoria nao comprova sentar/guardar |
| Interacao | Superficie utilizavel, altura/normal/folga, volume interno livre, espaco para abrir, partes e pontos de uso | Resumo somente se pedido exigir apoiar/guardar/abrir |
| Fisica | Complexidade/perfil de colisao, fixo/dinamico, massa/material/atrito com origem, provas de apoio/estabilidade | Capacidade especifica e escopo; nunca fisica_ok global |
| Articulacao/animacao | Grafo de partes, juntas/eixos/limites/pivots, rig/clips quando existentes, estados validos | Existe/declarado/testado; detalhes so ao articular/animar |
| Validade | Arquivo/derivado/asset/receita/configuracao testada, motor, data, metodo, evidencia, falhas e invalidacao | Resultado vigente e bloqueios relevantes, com referencia curta |

Nao exigir todos os campos para catalogar ou baixar. A ausencia e um dado util:
avaliar sob demanda as propriedades que afetam o pedido. Nao adivinhar massa,
atrito, capacidade de carga ou amplitude de junta apenas pela aparencia/nome.

Modelo e instancia sao diferentes: dimensao nativa/frente/links pertencem ao modelo;
transformacao, porta aberta, caminho bloqueado e superficies ocupadas pertencem a
instancia/cena. Escala/colisao/derivado configurados formam uma variante/receita.
Uma prateleira livre no asset nao esta necessariamente livre na cena.

Cada valor util precisa de origem distinguindo fonte declarada, medido no arquivo,
medido no Unreal, configurado, simulado, estimado por LLM e informado pelo usuario.
Incerteza qualitativa e preferivel a inventar um numero de confianca.

Provas devem apontar para a assinatura do que foi testado: hash da fonte/derivado,
identidade/versao do asset ou receita, escala e configuracao de colisao/fisica.
Alteracao pertinente torna a prova obsoleta para a nova variante; mantem historico
e permite reutilizar resultados realmente independentes da alteracao.

## O que nao enviar por padrao

- Vertices, triangulos, UVs, todos os ossos/juntas, matrizes e caminhos de prim.
- Embeddings numericos, texturas, thumbnails ou logs completos.
- Todos os materiais/LODs e paths/hashs de cada dependencia a cada busca.
- Repeticoes de sinonimos/descricoes longas, historico de testes substituidos e
  medidas antigas sem relacao com a variante selecionada.
- Scores opacos como se fossem probabilidade, etiqueta "articulado" como prova
  de que abre no Chaos ou nomes de pastas como propriedades fisicas.

Dados detalhados uteis ficam no SQL ou em artefatos em R: referenciados com hash;
embedding serve para calculo, nao leitura pela LLM. Decimais completos ficam na
evidencia; resposta usa precisao adequada ao pedido, sem falsear tolerancias.

## Consulta recomendada, usando infraestrutura existente

1. Busca textual/aliases + filtros SQL do que e necessario: categoria, tamanho,
   disponibilidade, licenca e capacidades, tratando desconhecidos explicitamente.
2. Retornar poucos candidatos (padrao atual oito), com tamanho, funcao sugerida,
   disponibilidade, capacidades relevantes e bloqueios vigentes.
3. Para o escolhido, detalhe seletivo por assunto: geometria, apoio, articulacao
   ou evidencias. Evitar `detalhe` completo para cada candidato.
4. Codigo deterministico verifica encaixe e folga; Unreal confirma estado real.
   Persistir resultado reaproveitavel e nova falha com procedencia.

Exemplo conceitual da ficha curta da mesa ja ensaiada, nao nova API implementada:

```json
{
  "id": "5ee2002c4ee1e9edf9e64d4390bc60abe2f9e8e67a6110c534323a92c6afb85f",
  "nome": "table 5",
  "categoria_sugerida": "mesa",
  "dimensoes_xyz_cm": [162.92, 57.56, 76.26],
  "origem_dimensoes": "montagem_unreal_ensaio_20261021",
  "disponibilidade": "importado_snapshot",
  "uso_testado": "apoio de cubo 5cm sobre mesa fixa por 3.47s: aprovado",
  "limite": "factory testada nao gerou juntas Chaos; gavetas nao aprovadas"
}
```

Isso nao permite concluir que aguenta uma pessoa, move-se com fisica ou abre
gavetas. A ficha detalhada precisa indicar asset/variante/ensaio exatos.

## Primeiro incremento recomendado e criterio de sucesso

Reutilizar caracteristicas/registros/verificacoes para uma projecao compacta por
objeto/variante, sem criar outro banco, MCP, servidor vetorial ou nova plataforma.
Normalizar apenas valores frequentemente filtrados; manter detalhes no formato
atual com referencias. Antes de ampliar a coleta, definir assinatura de validade
e regra de conflito entre medidas/fonte/configuracao.

Provas de aceitacao propostas: pedido de mesa dentro de um tamanho seleciona por
medida/escopo correto; pedido de gaveta que abre distingue junta declarada de junta
Chaos testada; apoio em estante conserva a falha interior mesmo apos novos testes;
reimportacao/escala/colisao alterada nao herdam aprovacao sem revisao; busca e detalhe
seletivo cabem no limite de saida e preservam as informacoes decisivas. Comparar
PA/tentativas/tamanho da resposta no Hermes, sem usar testes unitarios como PA.

Prioridade na frente do acervo: tornar as provas existentes consultaveis e impedir
reuso indevido, antes de rotular visualmente milhares de modelos ou baixar bancos
inteiros. Superficies HSM/artefatos pre-processados do SceneSmith merecem piloto
posterior, com acesso por objeto e compatibilidade real, sem assumir porte direto.

Pesquisa local: R:/CINF/BD/Director/pesquisa-metadados-20261021, com revisoes,
arvores e dezessete arquivos MD/Python selecionados. Apenas leitura do SQL e das
fontes; nenhum teste Unreal/Hermes, download de modelo ou migracao nesta rodada.
