# Protocolo de investigação extensiva

## Pipeline com evidências em cada etapa

### P0 — Preparação e baseline (somente leitura do Director)

1. Confirmar root da Skill, root do espaço `~/pesquisas-director/estudos`, localização e HEAD do Director; não adivinhar caminhos. Se Director indisponível, usar status `NAO_VERIFICADO` na comparação e avisar; não afirmar que já faz ou não faz.
2. `fila.py begin URL` grava sozinho o `git status` do Director e do `unreal-macros` (baseline) e a versão da skill; copie o que ele imprimir para `estado.md`. **Nunca escrever em `REGISTRO.md` nem em `unreal-macros`.**
3. Ler `indice.md`, `sintese-geral.md` e as fichas de `conhecimentos/` do tema; salvar `estado.md` com etapa e próximos passos; se bloqueado, `partial` com o motivo.

### P1 — Proveniência, frescor e manutenção

Consultar repositório oficial, commits recentes, releases/changelog, issues/PRs pertinentes, licença, dependências e mudanças incompatíveis; comparar relatos independentes, quando existirem. Registrar **data de acesso e commit**. Releases novos, badges, quantidade de estrelas e bench próprio não provam qualidade. Limites/licença de produtos (Houdini, Unreal, plugins) devem ser verificados na documentação do fabricante, com data — não confiar no README.

### P2 — Anatomia e percurso do código

Buscar pontos de entrada e funções reais; seguir callsites e formatos dos dados. Separar:
- **Declaração** (README e nomes)
- **Implementação** (funções/algoritmos reais)
- **Execução** (testes e comportamento)

Para sistemas baseados em nós/HDA/Blueprint/C++: inspecionar arquivos textuais, interfaces, parâmetros, serialização e, se possível, scripts embutidos; classificar lacunas binárias como `DESCONHECIDO` e não inventar grafo completo. Não interpretar imagem promocional como validação.

### P3 — Antes da construção: raciocínio e matemática do plano

Procurar se existe modelo explícito de **objetivo → restrições → proposta espacial → conferência → execução**.
- Quem planeja ruas, topografia, locais de casas, relações de áreas?
- Uma vila de 100 famílias é hierarquia de ruas+lotes+casas ou aleatoriedade?
- Existe representação de sala, corredor, passagem, parede compartilhada, terreno?
- Como são selecionados assets versus calculadas geometrias novas?
- Como o plano vira parâmetros/roteiro/Blueprint/PCG/Geometry Script/script Houdini?
- Há validação *antes* da execução? Ordem de operações e pré-condições?
- Conseguiria criar objeto/padrão que não estava no catálogo original? Quem cria nova capacidade?

### P4 — Depois da construção: a observação tem consumidor?

Desenhar o caminho completo **Unreal → coletor → representação → consumidor → nova decisão da LLM → eventual correção**. Para cada canal registrar:
- produtor (UE real, algoritmo próprio, log, cache, plano previsto)
- dado bruto (`actors`, `transforms`, `bounds`, malhas, raycast, navmesh, colisões, poses, joint transforms, hierarquia, segmentação, imagem)
- unidade/coordenada, frame/timestamp, fonte, incerteza, invalidade/fallback
- esquema textual/matemático (JSON, matriz, grafo, resumo de relações)
- custo de coleta (chamadas, dados, frequência, filtragem por relevância, diff) **medido ou ?**
- quem consome (humano, test, UI, ferramenta, **segunda chamada efetiva à LLM**)
- mecanismo de correção (planeja de novo, modifica delta, undo/rollback ou nenhuma)

**Gatilho obrigatório de investigação:** se o README diz agente autônomo, localizar o código que envia a resposta da ferramenta **de volta** ao modelo e a segunda decisão. Se não localizar após rastreio suficiente, afirmar `NAO DEMONSTRADO`; se confirmar ausência no fluxo examinado, registrar `AUSENTE` com evidência. Não exigir LLM de um gerador que nunca prometeu LLM.

### P5 — Comparação tripla

(1) O projeto externo realmente faz? (2) O Director **hoje**, no commit/arquivo examinados, já faz o quê? (3) Que matemática, padrão de arquitetura ou técnica merece portar/testar e por quê? Distinguir inferência de prova, vantagem da ideia e custo de implantação. C++, Rust, Houdini ou Blueprints **não requerem conversão completa**: priorizar regra/algoritmo portável e verificar API equivalente nativa do UE. Antes de propor infraestrutura nova, verificar opção madura existente.

### P6 — Provas e contraprovas

1. Escolher testes focados em hipóteses de maior impacto; não apenas repetir suíte do autor.
2. Começar offline com stdlib Python onde possível; usar diretório descartável, testar entradas esperadas **e** adversariais (degeneração, rotação, colisão, idempotência, relações contraditórias, escala, estrutura parcialmente alterada).
3. Usar o Unreal quando o teste precisar, pelo laboratório do Director (`python -m director.lab abrir`, com a trava), nunca as cenas do filme (`Y:`). Não instalar projetos externos no Director.
4. Salvar script, comando, entrada, saída, ambiente, versão, erro e diagnóstico; diferenciar `TESTE_ISOLADO` de `UNREAL`. Fazer medição confiável, sem inventar aceleração ou gasto em tokens.
5. Se a suíte falhar, investigar causa (caminho fixo, licença, sistema, dependências, defeito) antes de culpar o projeto.
6. Placar em quatro categorias (PASS, FAIL, OBSERVAÇÃO, NÃO TESTADO) e a lista "Mudanças de expectativa" (esperava X, deu Y, porque Z). Defeito medido nunca entra como PASS.

### P7 — Avaliação amigável e arquivo técnico

Pontuar os 17 itens **depois** de produzir evidências, usando `references/RUBRICA.md`. Criar `AVALIACAO.md` primeiro na apresentação final, depois documentos profundos; uma frase descoberta-chave é obrigatória. `?` quando não comprovado; escopo separado. Registrar triagem de fontes conflitantes e limitantes. Atualizar `indice.md`, `sintese-geral.md`, `comparativo.md` para descobertas entre projetos; não colar o README nem criar duplicatas gigantes.

### P8 — Fecho, isolamento e próximo

O `finish` compara o `git status` com o baseline e diz o próximo da fila. Se a missão concluir, `fila.py finish`; senão `partial` com o motivo e a próxima ação em `estado.md`. **Comecar o proximo somente se couber no lote autorizado**. Parar com FILA VAZIA, chamadas, ferramenta, decisao ou orcamento; no teto, preservar checkpoints e fila. Idade do contexto isoladamente nao equivale a teto autorizado.

## Bateria comum de desafios (investigar **pertinência**, não obrigar execução)

A. "Construa corredor de 1,5×5 m ligando duas salas existentes sem paredes duplas e com passagem livre." → adjacência, transições, cortes e verificação.

B. "Crie casa para quatro pessoas com três quartos, sala, cozinha, banheiro e circulação." → planta de uso versus fachada.

C. "Crie vila medieval rural para cem famílias, com caminhos, praça, água, cultivo e moradias." → hierarquia de planejamento **ANTES** da geração.

D. "Amplie cozinha, acrescente porta, preserve móveis e resto da casa." → diff, identidade, edição incremental, undo.

E. "Faça personagem andar até a mesa e pegar caneca." → identificação de alvo, navmesh, animação, IK/pose, hand-to-object, retorno do estado ao agente.

F. "Estou na cozinha: qual rota até a porta frontal? O que bloqueia?" → consulta 3D real, representação matemática e semântica para uma LLM, custo de observação.

Classifique cada desafio `DIRETO`, `PARCIAL`, `INDIRETO`, `NAO_APLICAVEL` ou `NAO_VERIFICADO` com evidência e uma linha sobre a capacidade aproveitável.

## Perguntas críticas adicionais

- Pode detectar que a ação retornou `ok` mas a geometria ficou inválida?
- A referência espacial está em coordenadas mundiais ou locais e como é transformada?
- Em modelo que pode trabalhar horas, onde persiste o plano, próximo passo e falhas?
- O sistema distingue mundo **pretendido** de mundo **observado** no motor?
- A observação cabe no contexto da LLM com filtros espaciais e deltas?
- Há medidas de desvio entre alvo e ação executada, sem exigir prints recorrentes?
- O mecanismo é macro fechada, primitivas genéricas, script gerado descartável ou ferramenta native do UE? Há espaço para compor algo inédito?
- Existem pontos de risco de scripts extraídos de fontes externas e qual licença permite portar conhecimento/código?


## Teto por lote (0.3.1)
Antes da pesquisa, registrar os limites autorizados de repositorios, inferencias LLM e bytes; contabilizar requisicoes HTTP separadamente. O teto prevalece sobre a ordem de continuar a fila. Ao atingi-lo, checkpoint e partial orcamento se o projeto esta incompleto; se acabou, deixar proximo PENDENTE. Relatar consumo e lacuna; somente o usuario amplia o teto. Nao alegar que o contador chama-se tokens se ele mede chamadas.
