# Director: como retomar o trabalho

Atualizado em 18/10/2026. Leia primeiro o [objetivo](OBJETIVO.md), o [README](../README.md)
e o [pipeline autorizado](pipeline-2026-10-18.md). O pipeline define a ordem; encontrar
um problema novo não autoriza trocar de frente sem registrar causa, dependência e prioridade.

## Procedimento atual

1. Confira branch/commit, alterações locais e a issue do bloco. Preserve o trabalho de outros
   agentes. A instalação do operador usa código publicado; desenvolvimento ocorre em outra pasta.
2. Consulte `python -m director --help` e `capacidades`, que não conectam ao Unreal.
   Use `contexto` para identificar o level e a fonte real da planta quando precisar do editor.
3. Plantas, biblioteca e trava ficam na fonte compartilhada do laboratório, configurada por
   `director/config.py`/`estado_local.py`. Não escolher uma planta só por ter revisão maior.
   [Procedimento de vínculo](estado-local.md); [instalação publicada](operador-publicado.md).
4. O núcleo usa biblioteca padrão; os testes completos também precisam das dependências de
   `requirements-planejamento.txt`. Execute a suíte pertinente ao risco da mudança. Última
   suíte completa comprovada: 132 testes Director e 13 guarda. Isso não é taxa de PA.
5. Para trabalho autorizado no editor, consulte `python -m director.lab estado` antes de
   `abrir`. Use somente o laboratório; a ponte recusa o projeto cinematográfico/porta 8001.
   `pecas`, criação de laboratório e demonstrações alteram estado: não executá-los como rotina
   de leitura. Não interromper uma sessão de outro operador.
6. Antes de Python experimental, procure capacidade pronta e consulte `api TERMO`; use o
   mecanismo de ensaio e a trava. Declare hipótese, evidência, limites e recuperação. Código
   permanente depende da autorização de desenvolvimento recebida; pedido de cena não basta.
7. Compare intenção, planta e medidas nativas. Preserve identidades e partes corretas. Registre
   a prova e as limitações na própria issue; publique antes de atualizar a instalação do operador.

## Evidências atuais

- [Composição de salas e passagens](composicao-salas.md); [portas e verificação 2D](portas-e-2d.md).
- [Biblioteca](biblioteca-piloto.md); [observação](observacao-textual.md); [diagnósticos](diagnosticos.md).
- [Espera no Hermes](esperas-hermes.md); [causa da demora da porta](revisao-porta-2026-10-18.md).
- [Pesquisa dirigida proposta](pesquisa-dirigida-director.md); pendências na [#48](https://github.com/talisp/Director/issues/48).

## Registro histórico de 13/10/2026

O conteúdo abaixo preserva as descobertas da primeira entrega. Números de testes, caminhos
de trava, roteiro e hipóteses são históricos, não o estado atual nem uma ordem de execução.
A evolução comprovada e as pendências atuais estão nos links acima.

<details>
<summary>Abrir anotações da primeira entrega</summary>

# Director: o que se sabe e como retomar

> Documento técnico curto para **qualquer agente ou pessoa** continuar sem depender de conversa anterior. Estado em 13/10/2026. Números da primeira entrega: [entrega1](entrega1/README.md).

## Como retomar (procedimento mínimo)
Na raiz deste repositório, com um Python 3.11 ou mais novo (o núcleo usa só a biblioteca padrão):
1. Leia este arquivo e o [README](../README.md).
2. `python -m unittest director.testes.testes_nucleo` → tem de dar 33 de 33 (não precisa do Unreal).
3. `python -m director capacidades` → o que uma ficha pode pedir (também não precisa do Unreal).
4. Com o Unreal 5.8 instalado: `python -m director.lab criar` e depois `python -m director.lab abrir` (cria e abre o projeto de laboratório, na porta 8011). Abra o laboratório **sempre por este comando**: ele liga as ferramentas do Director, o inglês e o modo sem diálogos.
5. `python -m director pecas` cria as peças; `python -m director fazer CENA FICHA.json` aplica uma ficha; `python -m director estado CENA` compara a planta com o Unreal.
6. Mudou código em `director/editor/`? `python -m director.dev reload` recarrega as operações sem reiniciar o editor.
- Prova completa numa cena **nova**: `python -m director.demonstracao tudo NOME` (cerca de 50 s; fecha e reabre o editor do laboratório).
- Proteções: só fala com o editor cujo projeto é o laboratório; recusa a porta 8001; trava de um operador por vez (`work/unreal_lab.trava`); só mexe em ator com etiqueta `DIR_ID:` e só grava em `/Game/Director`.
- Caminhos e portas: variáveis `DIRECTOR_LAB_DIR`, `DIRECTOR_LAB_PORTA`, `DIRECTOR_EDITOR_EXE` (ver `director/config.py`).

## O que é reutilizável e o que é instrumento de teste
**Candidatos a ficar no Director** (funcionaram ao vivo; a arquitetura definitiva ainda é decisão do Talis):
| Arquivo (em `director/`) | Papel |
|---|---|
| `nucleo/operacoes.py` | contrato das fichas (5 operações), validação e recusas; `capacidades` para qualquer agente |
| `nucleo/planta.py`, `nucleo/derivar.py` | planta declarativa e identificadores estáveis das peças |
| `nucleo/plano.py` | adoção de edição manual, mudança mínima, conferência |
| `nucleo/executor.py` | os 8 passos de uma alteração e o `incorporar` |
| `nucleo/pecas.py` + operação `pieces_build` | peça = dados (variáveis, componentes, Construction Script em texto); o programa cria o Blueprint |
| `ponte.py`, `lab.py`, `config.py` | proteção (trava, recusa de outro editor) e o laboratório |
| `editor/director_tools/` (`inventory`, `apply`, `save`, `reload_level`, `level_ensure`, `measure`) | o que roda dentro do editor |
| `__main__.py` | porta única em texto, sem agente |

**Instrumentos experimentais** (ficam para referência; não são arquitetura):
- `demonstracao.py` (roteiro da prova e `PonteQueEstraga`), `dev.py` e a operação `dev_exec` (roda Python solto no editor do laboratório);
- personagem de teste (`walker_place`, `walker_remove`, `sim_walk_start`, `sim_walk_state`) e os empurrões (`sim_impulse`, `sim_move`, `sim_door`);
- `testes/editor_falso.py` (editor de mentira dos testes); `fichas/comando*.json` (exemplos);

## Ferramentas da Epic: o que foi usado (UE 5.8.3, tudo conferido ao vivo)
| Para | API | Onde é usada |
|---|---|---|
| Criar Blueprint, variáveis, compilar | `BlueprintTools.create / add_variable / set_variable_instance_editable / set_variable_category / compile_blueprint / get_default_object` (plugin experimental EditorToolset: `Engine\Plugins\Experimental\Toolsets\EditorToolset\Content\Python\editor_toolset\toolsets\blueprint.py`) | `ops.py: pieces_build` |
| Escrever o Construction Script | `BlueprintTools.get_graph(bp, "UserConstructionScript")` + `write_graph_dsl(grafo, texto)`; manual da linguagem em `blueprint_dsl.py: USAGE`; a entrada é `(fn ConstructionScript () ...)` | `pecas.py` (textos), `pieces_build` |
| Componentes do Blueprint | `ActorTools.add_component(blueprint ou componente pai, classe, nome)`; moldes por `SubobjectDataSubsystem.k2_gather_subobject_data_for_blueprint` + `get_object_for_blueprint` | `ops.py: _moldes` |
| Atores na cena | `EditorActorSubsystem.spawn_actor_from_object / spawn_actor_from_class / destroy_actor / get_all_level_actors`; `set_editor_property` numa variável da instância **roda o Construction Script de novo** | `ops.py: _uma`, `inventory` |
| Level | `LevelEditorSubsystem.new_level_from_template / load_level`; `EditorLoadingAndSavingUtils.get_dirty_*_packages / save_packages` | `level_ensure`, `reload_level`, `save` |
| Medir | `SystemLibrary.line_trace_single`, `capsule_trace_single_by_profile` (`"Pawn"`), `HitResult.to_dict()`; `NavigationSystemV1.find_path_to_location_synchronously`, `is_navigation_being_built` | `measure` |
| Navegação | `NavMeshBoundsVolume` (caixa de 200 cm, escalada) + `on_navigation_bounds_updated`; `[/Script/NavigationSystem.RecastNavMesh] RuntimeGeneration=Dynamic` no `DefaultEngine.ini` | `derivar.py`, `lab.py` |
| Play | `LevelEditorSubsystem.editor_play_simulate / editor_request_end_play`; `AIController.move_to_location`; física dos componentes (`set_simulate_physics`) | `ops.py`, seção Play |
| Servidor de ferramentas | plugin ModelContextProtocol; porta em `Config\DefaultEditorPerProjectUserSettings.ini`; toolset próprio registrado pelo `init_unreal.py` da pasta no `UE_PYTHONPATH` | `lab.py`, `editor/init_unreal.py` |

## Limitações observadas e como foram resolvidas
| Problema (medido) | Solução adotada | Arquivo |
|---|---|---|
| A linguagem de grafos da Epic usa os nomes dos nós **em inglês**; no editor em português os nomes mudam (`Transformação\|...`, `Variáveis\|Padrão\|Obter...`) e ela falha | o laboratório abre com `-culture=en`; `pieces_build` recusa em outra língua | `lab.py`, `ops.py` |
| Variável numa categoria muda o nome do nó: `Variables\|Director\|GetLargura` (componentes ficam em `Variables\|Default\|Get...`) | dois prefixos no cadastro | `pecas.py` (`VAR`, `GET`) |
| Componente com sublinhado no nome (`Uso_Dentro`) não é achado pelo grafo | nomes sem sublinhado (`UsoDentro`, `AncoraTopo`) | `pecas.py` |
| Colisão desligada pelo Construction Script (`SetCollisionEnabled`) **fica guardada na instância** e volta nas rodadas seguintes: o segmento reaparece visível e sem colisão | a peça nunca mexe em colisão; segmento sem tamanho fica invisível, com 1 cm, 5 cm abaixo da base | `pecas.py: _caixa` |
| `ScopedEditorTransaction.cancel()` não desfaz nada; `TRANSACTION UNDO` desfaz criar e atualizar, mas **devolve quebrada** (sem colisão) uma peça removida | recuperação = recarregar o level do disco (`load_level` no mesmo level, sem diálogo) e conferir o inventário | `executor.py: _recuperar` |
| O Python do editor não cria ator dentro do Play (`GameplayStatics.begin_deferred_actor_spawn_from_class` não existe no Python) | o personagem de teste é posto antes do Play e tirado depois; em seguida o level é recarregado (fica "por salvar" sem diferença) | `ops.py: walker_*` |
| Com a folha da porta fora da malha, o personagem entra e fica preso na folha aberta | a folha entra na malha (`can_ever_affect_navigation=True`), fica na face de dentro da parede, e a malha é refeita em jogo | `pecas.py`, `lab.py` |
| Logo depois de uma mudança, `is_navigation_being_built` ainda responde "não" e a malha está pela metade | 4 leituras seguidas sem obra; a medida de caminho espera até 5 s | `executor.py: _esperar_nav` |
| Diálogo modal trava o servidor de ferramentas | laboratório com `-unattended`; `quit_editor` recusa se há algo por salvar | `lab.py`, `ops.py` |
| Corpo com física que não é a raiz se solta do ator ao simular | `BP_Objeto` herda de `StaticMeshActor` (a malha é a raiz) | `pecas.py` |
| No catálogo o toolset aparece como `PythonTypes.DirectorTools_0x...`; o `ProgrammaticToolset` da Epic é uma caixa de areia, não roda Python livre | busca pelo nome; operação própria `dev_exec` para desenvolver | `ponte.py`, `ops.py` |
| `EditorAssetLibrary.delete_asset` num level devolveu "apagado", mas o `.umap` continuou no disco | com o editor fechado, os levels de ensaio foram movidos para fora do projeto | — |
| Não expostos ao Python: `Actor.rerun_construction_scripts`, "Keep Simulation Changes" | mudar uma variável já roda o Construction Script; o `incorporar` copia posição e giro lidos no Play | `executor.py: incorporar` |

## Três níveis de certeza
**Verificado ao vivo** (números em [entrega1](entrega1/README.md)): o programa cria Blueprints paramétricos com Construction Script; cria, atualiza e remove peças por identificador mantendo o mesmo ator; parede com vão; porta que barra e libera; física de objetos soltos; malha de navegação e `Character` entrando pela porta; salvar, fechar e reabrir; adotar edição manual; `incorporar`; recusar ficha inválida; recuperar de falha; atualizar um Blueprint já usado (a porta mudou e a instância na cena acompanhou).

**Soluções provisórias** (funcionam, mas não são desenho final):
- geometria de cubos e cilindros escalados; copo maciço; sem materiais;
- porta que gira por parâmetro (sem interação, sem animação); pontos de uso como componentes simples, não Smart Objects;
- o segmento "escondido" de 1 cm sob a parede;
- recuperação por recarga do level + cópia do `.umap` e da planta em `work\restauracao` (restaurar de uma cópia é manual; não há versionamento dos assets);
- level criado do modelo `Template_Default` do motor, com a sala 1 cm acima do chão dele;
- estrutura mexida à mão (parede, piso, lugar da porta) não é adotada: o Director repõe na mudança seguinte e avisa;
- uma porta ou janela por trecho de parede; com duas na mesma parede o núcleo divide a parede (testado só sem o Unreal).

**Hipóteses** (ninguém mediu):
- uma LLM pequena preenche as fichas sem errar;
- Smart Objects podem ser criados e ligados às peças pelo Python; PCG ou Geometry Script trazem ganho sobre os cubos;
- a ligação de uma sequência do Sequencer com as peças sobrevive a reabrir e a recriar uma peça; dá para gravar o Play numa sequência editável;
- um personagem com corpo e animação anda pelo mesmo caminho da cápsula;
- duas salas com parede em comum ("porta para o banheiro"), sala girada, cenas grandes;
- o mesmo método funciona num projeto de verdade (editor em português, cenário pesado).

## O que falta para um Director utilizável
1. Medir a LLM pequena preenchendo fichas (barato; não precisa do Unreal).
2. Peças com aparência de verdade (malhas prontas) e um catálogo pequeno de móveis.
3. Personagem com corpo e animação; interação (abrir a porta, sentar, pegar o copo).
4. Sequência editável, câmera e saída de vídeo.
5. Mais de uma sala; parede em comum.
6. Ligação com um agente (que só precisa chamar `python -m director`), sem mudar o núcleo.
7. Decidir como versionar os arquivos do Unreal.

</details>
