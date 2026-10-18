# Director

**Criação e edição de cenários 3D funcionais no Unreal Engine por conversa, com modelos de linguagem locais ou econômicos.**

O Director busca transformar pedidos como “crie uma cozinha anexa à sala” ou “aumente esse cômodo sem deslocar a mesa” em mudanças verificáveis na cena. A pessoa descreve o que quer, esclarece escolhas importantes e pode corrigir o resultado sem precisar programar ou fornecer coordenadas.

O destino são **cenas e animações para vídeos de referência**, usados depois em ferramentas de geração de vídeo por IA. Nesta etapa, a prioridade é construir e modificar cenários com coerência espacial, preservação e possibilidade de interação. A aparência final pode ser simples. A exportação do vídeo será feita manualmente pelo usuário no Unreal.

**Estado em 18/10/2026: protótipo experimental.** Há capacidades testadas no laboratório, mas ainda não há comprovação de atendimento confiável a todos os pedidos por uma LLM. As limitações e as pendências fazem parte desta entrega.

- [Objetivo e critérios de trabalho](docs/OBJETIVO.md)
- [Pipeline autorizado e pendências](docs/pipeline-2026-10-18.md) · [issue de acompanhamento #48](https://github.com/talisp/Director/issues/48)
- [Como retomar o projeto](docs/CONHECIMENTO.md)
- [Operação pelo Hermes](hermes/README.md) · [instalação publicada separada do desenvolvimento](docs/operador-publicado.md)

## Como funciona

```text
Pedido → consulta da cena → plano → execução no Unreal
       → medidas e diagnóstico → comparação com o pedido → correção
```

1. **O agente interpreta e investiga.** No ambiente local, o perfil Director do Hermes usa o Qwen. Ele consulta o cenário, procura assets existentes e utiliza as ferramentas disponíveis. Pode investigar alternativas no laboratório quando as operações atuais não bastam, dentro da autorização recebida.
2. **O núcleo Python calcula e valida.** Fichas JSON descrevem operações; a planta persistente registra o estado desejado. Código determinístico valida medidas e relações, deriva peças e prepara mudanças. O planejamento espacial utiliza CP-SAT para propor arranjos e adjacências.
3. **O Unreal executa o trabalho de motor.** A ponte aciona a automação do editor, Blueprints paramétricos, assets, colisões, física e navegação. O Director combina essas capacidades em operações repetíveis.
4. **A observação retorna dados objetivos.** Identidades, parâmetros, caixas reais, medidas, colisões, caminhos e avisos ajudam o agente a comparar o executado com o pretendido. Screenshots podem complementar essa informação.

Uma ficha descreve uma alteração; a planta representa o cenário desejado; os dados do Unreal mostram o estado observado. Essas camadas não são intercambiáveis. `ok: true` indica execução da ferramenta, sem garantir atendimento ao pedido humano. Mesmo um veredito geométrico aprovado tem escopo limitado.

O núcleo possui conciliação, backups e recuperação de falhas. Scripts experimentais e interrupções da ponte têm limites próprios: **não há garantia de desfazer automaticamente qualquer operação arbitrária**.

## O que existe e foi verificado

| Capacidade | Evidência e limites |
|---|---|
| Criar e alterar salas, paredes, portas, janelas e objetos, preservando identidades | [Primeira entrega](docs/entrega1/README.md) e [estado compartilhado](docs/estado-local.md). A conciliação depende da planta correta e das alterações suportadas. |
| Compor vários cômodos por dimensões e adjacências, sem macro de casa | [Pilotos de quatro cômodos e cozinha ampliada](docs/composicao-salas.md). Retângulos, parede de 15 cm, resolução de 1 cm e até 32 salas no piloto; adjacência não cria abertura automaticamente. |
| Criar passagens sem folha de porta; configurar dobradiça e sentido de abertura | [Composição](docs/composicao-salas.md) e [portas/2D](docs/portas-e-2d.md). Passagem física livre não garante caminho completo na NavMesh. |
| Procurar assets da cena, do projeto e da biblioteca offline | [Biblioteca e piloto Kenney](docs/biblioteca-piloto.md). Uma cadeira foi importada, unida pelo motor em um objeto e verificada fisicamente; isso não certifica interação corporal. |
| Observar geometria e conter informação para a LLM | [Observação textual e contenção](docs/observacao-textual.md). O desenho em texto representa a planta desejada; sua vantagem sobre JSON ou imagem ainda não foi demonstrada. |
| Devolver avisos nativos e erros ao operador | [Diagnósticos](docs/diagnosticos.md). A correlação com a operação é temporal; ausência de avisos não prova qualidade. |
| Manter operação e desenvolvimento separados | [Instalação publicada e túnel do modelo](docs/operador-publicado.md). Recuperação do túnel foi testada; reinício real do Windows/login e redundância continuam pendentes. |

**Verificação de código desta entrega:** 132 testes do Director e 13 da guarda aprovados; a suíte do Director também passou na instalação publicada. Os documentos acima distinguem testes offline, verificações reais no Unreal e sessões do Hermes. Quantidade de testes não é medida de Pedidos Atendidos.

## O que ainda falta

- Demonstrar que o operador atende pedidos completos e variações sem omitir requisitos ou inventar decisões essenciais.
- Resolver os dois casos históricos de navegação após reabertura e em passagem norte–sul.
- Concluir a biblioteca, os testes de observação, a aprendizagem com procedência e a operação no aplicativo do Hermes.
- Evoluir apoio em superfícies, peças finas, materiais e revisão limitada com preservação.
- Validar a evolução da pesquisa de GitHub e os pilotos externos previstos.

Personagens com corpo, interações como pegar/sentar e animação temporal pertencem à evolução futura. Os testes atuais de cápsula/Character e de física não equivalem a um sistema de animação corporal pronto.

A lista completa e sua ordem estão no [pipeline](docs/pipeline-2026-10-18.md). O projeto sucede o [unreal-local-director](https://github.com/talisp/unreal-local-director), descontinuado.

## Consultar e testar

O núcleo e os comandos básicos usam Python 3.11+ e biblioteca padrão. Planejamento, validação 2D e análise offline de modelos usam as dependências opcionais declaradas em `requirements-planejamento.txt` e `requirements-biblioteca.txt`.

Sem conectar ao Unreal:

```powershell
python -m director --help
python -m director capacidades
python -m unittest director.testes.testes_nucleo
python -m unittest hermes.testes_guarda
```

Para a suíte completa, use um ambiente com as dependências de planejamento instaladas:

```powershell
python -m unittest discover -s director/testes -p 'testes_*.py'
```

A integração foi verificada no Windows com Unreal Engine **5.8.3**, em um projeto de laboratório separado. Ela utiliza Python Editor Scripting, ModelContextProtocol, EditorToolset e GeometryScripting. Isso não comprova compatibilidade com outras instalações ou versões. Consulte [retomada](docs/CONHECIMENTO.md) antes de abrir/criar um laboratório.

O perfil de uso deve apontar para uma instalação do código publicado, separada da pasta em que agentes desenvolvem. Plantas, biblioteca e trava compartilhadas não devem ser substituídas por cópias antigas ao trocar a instalação.

## Código e documentação

| Caminho | Responsabilidade |
|---|---|
| `director/nucleo/` | Fichas, planta, derivação, conciliação e execução |
| `director/planejamento.py`, `director/planejamento_salas.py`, `director/espaco2d.py` | Planejamento espacial e verificações 2D |
| `director/editor/` | Operações executadas dentro do editor Unreal |
| `director/ponte.py`, `director/lab.py`, `director/estado_local.py` | Comunicação, laboratório e fonte compartilhada |
| `director/catalogo.py`, `director/biblioteca.py` | Busca e biblioteca de assets |
| `hermes/` | Orientação do operador, skill e guarda |
| `docs/` | Objetivo, pipeline, evidências, limitações e histórico |

## Referências e licença

A adaptação de conectividade e áreas livres de SceneSmith está identificada em [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). Outros estudos são referências de pesquisa; uma avaliação favorável não significa integração ou validação do repositório inteiro. A [proposta de pesquisa dirigida](docs/pesquisa-dirigida-director.md) distingue código, algoritmo, inspiração e solução pronta.

O Director possui **licença própria de código disponível para consulta**, com condições e restrições em [LICENSE](LICENSE); não é apresentado como software open source. Assets, modelos e o Unreal Engine têm licenças próprias e não são incluídos automaticamente nesta publicação.
