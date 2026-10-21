# Régua de avaliação — versão 1.1 (17 critérios)

> 1.1 (16/10/2026): caminho real antes da nota (10, 11, 13), medição própria na 16, `ALEGADO` só com `?`, exemplos fixos do CityGenerator. Avaliações feitas com a 1.0 não são reescritas; ao comparar, lembre a versão.

## Regras de pontuação

Avaliar **capacidade do repositório no commit examinado**, não fama, intenção ou utilidade para o Director. Aplicabilidade ao Director e força da prova são campos independentes.

- `0`: capacidade comprovadamente não implementada no caminho estudado; indicar `FORA_ESCOPO` quando essa era uma decisão do autor, não defeito.
- `1–3`: apenas operações elementares/presets, dependência extrema de humano ou implementação mínima.
- `4–6`: implementação parcial, funcional em condições restritas ou com etapas humanas.
- `7–8`: implementação consistente, regras explícitas, boa generalidade no escopo, com evidência de código e idealmente testes.
- `9–10`: generalização e robustez excepcionais com testes adversariais e demonstração efetiva. Sem prova de execução, evitar 9–10.
- `?`: não há evidência suficiente para pontuar; não substituir por nota intuitiva.

## Antes de dar a nota: o caminho real

Para as linhas que falam de LLM e de dados do motor, **escreva o caminho antes do número** (`caminho: produtor → consumidor → o que muda depois`) e confira cada seta no código:
- **10:** uma entrada em linguagem natural que, no código do projeto, **provoca operações**. Um guia em Markdown para outro agente operar o projeto não é essa entrada.
- **11:** o que sai do Unreal (qual dado, por qual função) e **quem recebe** (humano, arquivo, outro programa, LLM).
- **13:** o resultado **entregue a uma LLM**, seguido de uma **segunda decisão** dela. Loop determinístico (medir → ajustar → refazer sem modelo) é engenharia boa, mas na 13 vale 0; registre-o na 05 ou na 17.
- **16:** medição sua (`TESTE_ISOLADO` ou `UNREAL`), separada de tempos publicados pelo autor, que deixam a nota em `?`.

Se não achar o caminho depois de rastrear, a nota é `0` (ausente no fluxo rastreado, com os fluxos listados em `evidencias.md`) ou `?` (não deu para rastrear).

Calibração **repetível**: para cada linha, usar as âncoras `0`, `5` e `8` abaixo; interpolar apenas justificando. Escores 9–10 exigem prova superior à âncora 8. Não somar nem tirar média simples dos 17 itens: compare os relevantes para o objetivo de cada projeto. Nota da **capacidade** não é nota da **relevância** nem da **facilidade de adaptação**.

**Escopo** de cada linha: `DENTRO_ESCOPO`, `FORA_ESCOPO` ou `INCERTO`.
**Evidência**: `ALEGADO`, `CODIGO`, `TESTE_ISOLADO`, `UNREAL`, `NAO_VERIFICADO`. `ALEGADO` só acompanha nota `?`.
Para itens compostos, marque o nível de evidência mais forte que fundamenta especificamente a nota, não o nível máximo encontrado no projeto inteiro. Em `CODIGO`, prova é implementação inspecionada, não nome de classe.

## Critérios e âncoras

| ID | Dimensão | 0 — ausente | 5 — parcial | 8 — forte |
|---|---|---|---|---|
| 01 | Planejamento territorial/global | Não decide estrutura do território | Distribui lotes, vias ou regiões com regras limitadas | Planeja hierarquia território→vias→lotes→edificações com restrições verificáveis |
| 02 | Planejamento de ambientes e conexões | Não distribui cômodos/áreas funcionais | Organiza alguns espaços e adjacências | Resolve planta funcional com circulação, portas e acessibilidade verificáveis |
| 03 | Planejamento geométrico/modular | Apenas posiciona objetos prontos | Composição paramétrica limitada | Resolve contornos, transformações e módulos sob restrições geométricas diversas |
| 04 | Ordem e dependências de execução | Não explicita etapas | Algumas dependências fixas | Pipeline por etapas, pré-condições, checkpoints e falha rápida |
| 05 | Validação pré-execução | Executa sem conferir | Algumas checagens de dimensões/colisões | Verifica integridade espacial, restrições, topologia e efeitos antes de modificar motor |
| 06 | Construção procedural de edifícios/cenários | Não constrói estruturas | Gera construções simples, parâmetros limitados | Gera estruturas compostas, paramétricas e utilizáveis |
| 07 | Criação genérica de objetos/estruturas | Nenhuma criação | Monta tipos/peças conhecidos | Produz geometria nova variando forma e topologia além de catálogo fixo |
| 08 | Geração de grandes mundos | Não organiza escala territorial | Distribuição ampla com limitações | Gera territórios grandes com hierarquia, consistência e controle de densidade |
| 09 | Modificação preservando existente | Só recria/destrói | Altera partes mas quebra dependências/bake | Altera objetos existentes por identidade/diff com preservação verificável |
| 10 | Linguagem natural → operações no Unreal | Sem entrada de LLM | LLM escolhe presets e solicita comandos | Pedidos abertos são decompostos em ações executáveis e verificadas |
| 11 | Extração do Unreal em dados matemáticos/textuais | Não consulta estado | Retorna transformações, medições ou logs parciais | Retorna estado 3D preciso, consultável, compacto e filtrável |
| 12 | Semântica espacial amigável à LLM | Apenas números ou nenhum dado | Algumas relações derivadas | Grafo contextual de relações, acessos, oclusão e significado calculados e verificáveis |
| 13 | Ciclo observação → decisão → autocorreção | Não há segunda decisão da LLM | Resultados chegam ao modelo, mas correção parcial | Loop motor→observação estruturada→nova inferência→correção validada |
| 14 | Navegação e movimento de personagens | Não movimenta personagens | Rota ou deslocamento com limitações | Navegação e movimento até alvos com verificação espacial e obstáculos |
| 15 | Interação/gestos/animação | Não oferece animação | Aciona animações com alvo, sem alinhamento robusto | Coordena alvos, corpo, IK/poses e ações temporais verificadas |
| 16 | Eficiência computacional demonstrada | Sem otimização e custos inviáveis comprovados | Medidas parciais, caches/recomputes limitados | Tempos, memória e dados monitorados com experimentos independentes reproduzíveis |
| 17 | Conhecimento técnico reaproveitável | Sem técnica pertinente | Alguns algoritmos/padrões portáveis | Métodos claros e generalizáveis, com protótipos ou provas independentes |

### Calibradores externos (não copiar notas automaticamente)

- Edifício apenas com fachada parametrizada e sem planta interna: `06` pode ser alto, `02` deve ser zero, se isso foi verificado; ausência de planta **não** reduz a nota `06`.
- Gerador de ruas→lotes→edifícios: potencial forte em `01`, mesmo sem LLM; `10/12/13` podem ser zero.
- Sistema que gera e valida comandos, mas exibe resultados **só para o humano**: `11` pode ser positivo; `13` é `0` se for comprovado que não há retorno a outra inferência.
- Métrica de aceleração apenas no README: `16` fica `?` se não houver prova suficiente, mesmo que o código use caching.
- Resíduo numérico zero num polígono que se autointersecta: reduz `05`, não necessariamente `03`.
- `TESTE_ISOLADO` de matemática não comprova `UNREAL` fim-a-fim.

### Exemplos fixos (CityGenerator `c5ec23ec`, auditoria de 16/10): o significado de uma nota não muda entre pesquisas

- `10`: o projeto não recebe linguagem natural; o `CLAUDE.md` dele ensina o Claude Code a operá-lo → **0, FORA_ESCOPO** (a v0.1 deu 3).
- `13`: o loop medir → ajustar → refazer é automático, sem LLM → **0** no fluxo implementado (a v0.1 deu 4).
- `16`: só os tempos do autor (cook de 30–60 min) e cronômetros no código → **`?`** (a v0.1 deu 5).
- `11`: um script do UE exporta medidas para JSON lidas pelo Houdini → nota positiva com `caminho:` UE → JSON → Houdini (consumidor não é LLM; isso pesa na 12/13, não na 11).
- `01`: preparação do grafo de ruas e restrições antes de gerar → 8 com `CODIGO`, mesmo sem a operação completa testada.

## Como auditar a nota

Cada linha da tabela em `AVALIACAO.md` tem **seis campos**: ID, Dimensão, Nota, Escopo, Evidência, Justificativa. A evidência precisa apontar para item identificável em `evidencias.md` (ex.: `E07`) ou arquivo/função do commit. O nível de evidência e o escopo nunca são inferidos somente pela nota.

Acrescente em `AVALIACAO.md`, fora da tabela:
- **Descoberta-chave** em uma frase clara, com evidência.
- **Aproveitamento para Director:** `ALTO`, `MÉDIO`, `BAIXO`, `NENHUM` ou `INCERTO`, com motivo (não é média).
- **Custo/adaptação:** `BAIXO`, `MÉDIO`, `ALTO` ou `INCERTO`, com dependências e licença.
- **Confiança da pesquisa:** `BAIXA`, `MÉDIA` ou `ALTA` com explicação.
- **Principal alternativa/concorrente** realmente verificado, se pertinente.
