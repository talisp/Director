# Contrato dos arquivos da pesquisa

## Layout persistente

```text
~/pesquisas-director/estudos/
  fila.json                 # Fonte de verdade da fila; gerida por fila.py
  fila.md                   # Espelho legível, atualizado pelo script
  PAINEL.md                 # Para o Talis: copiar / inspirar-se / usar de cada projeto; refeito pelo finish
  indice.md                # Uma linha por repo; resumo, nota de utilidade, evidências
  comparativo.md           # Técnicas/critério comparados entre vários repositórios
  sintese-geral.md         # Descobertas cross-repo, sem duplicar dossiês
  conhecimentos/           # Uma ficha por técnica genérica reutilizável
  repositorios/
    owner--repo/
      AVALIACAO.md          # Cartão amigável com 17 notas
      analise.md            # Como funciona, diagramas textuais e desafios A-F
      evidencias.md         # E01..En, versão, fontes, código e linhas
      experimentos.md      # Hipóteses, comandos, logs e resultados medidos
      estado.md             # Checkpoints, pendências, baseline e diffs observados
  sugestoes-skill.md       # Sugestões para a skill (o Talis e o Claude Code decidem; a skill não se reescreve)
  laboratorio/
    owner--repo/            # Clone/testes/resultados; nunca dentro do Director
```

`fila.py` atualiza `fila.json` e `fila.md`. Não editar esses arquivos manualmente durante a pesquisa. Todo o resto tem escrita manual pela LLM na pasta externa. Os conhecimentos devem ser **técnicas**, não resumos de repositórios: objetivo, algoritmo, entradas/saídas, restrições, prova, casos adversariais e referências com commit; cada técnica cita todos os projetos que a usam.

## AVALIACAO.md

Use `templates/AVALIACAO.md` copiando sem alterar IDs e nomes da tabela. Todos os 17 devem ter valores `0..10` ou `?`, escopo e evidência. Uma justificativa concreta, mesmo para `0`. Validar com `scripts/verificar_avaliacao.py`. Atualizar data, commit e status da investigação.

**Cartão deve começar pelo que o usuário quer ouvir**: em até 12 linhas, função real, descoberta-chave, notas mais relevantes, valor para Director, risco e falta de prova. Depois, tabela completa de 17 linhas. Evitar texto motivacional, slogans e exibição de prosa longa. Não inventar score geral único ou usar média simples.

## analise.md

- Resumo e limitações reais da implementação.
- Arquitetura e formatos dos dados (desde entrada até saída).
- Planejamento **antes** de modificar mundo; qualidade da semântica/topologia.
- Como scripts/macros/BluePrints/PCG/motor geram ou editam cena.
- **3D→dados→LLM**: tabela por canal, com consumidor real e segunda decisão.
- Seis desafios A-F e evidência por classificação.
- Comparação com Director *real e no commit observado*, arquivos e funções.
- Conhecimentos portáveis e alternativas prontas, grau de adaptação.
- Dependências/licenças/versões, fontes oficiais verificadas e divergências.

## evidencias.md

Tabela com `E01...`: alegação, evidência `ALEGADO|CODIGO|TESTE_ISOLADO|UNREAL|NAO_VERIFICADO`, localização do código (link para commit, caminho, função e linha), limitações e data. Nas afirmações de ausência, especificar quais fluxos foram rastreados; **ausência de busca textual sozinha não basta**.

## experimentos.md

No topo: `Resultado: N PASS · N FAIL · N OBSERVAÇÃO · N NÃO TESTADO` e `Mudanças de expectativa:` (cada esperado mudado depois de rodar: esperava X, deu Y, porque Z; ou `nenhuma`). O `finish` recusa sem as duas linhas.

Para cada experimento: ID, hipótese, ambiente, entrada, procedimento/script, comando reprodutível, saída/arquivo, conclusão, limitações e eventuais erros do próprio experimento. Separar teste de matemática, teste do software e teste no motor. Arquivos brutos ficam no laboratório. Não escrever que uma execução Python offline demonstra funcionamento integrado.

## estado.md

Checkpoint: repo+commit, versão da skill (do `begin`), etapa, o que já foi feito, arquivos gerados, próxima ação concreta, impedimentos, comparação do `git status` (do `finish`) e a tabela do `medir_contexto.py`. Os três marcos (arquitetura; código e testes; evidências) também vão para a fila com `fila.py checkpoint URL "feito: ... | falta: ... | arquivos: ..."`. **Essencial para retomada sem contexto.**

## indice.md / sintese-geral.md / comparativo.md

**indice.md**: nome, URL, commit, nota/escopo de `01` (território), `06` (construção), `11` (3D textual), `13` (ciclo LLM), utilidade ao Director e link da avaliação. Não forçar tabela com 17 colunas na visualização principal.

**comparativo.md**: seções para os 17 IDs, lista dos projetos mais fortes por critério com evidência e notas normalizadas, e comparação honesta sobre provas. **sintese-geral.md**: a cada projeto, técnicas novas; equivalentes já vistas (onde); implementações melhores ou piores; evidências contraditórias; combinações possíveis. Usar critérios para não repetir a pesquisa do projeto anterior.

## Resposta para usuário (após cada conclusão)

Exemplo de formato curto:

> **Nome do projeto — avaliação pronta**
> Faz realmente: ...
> **Descoberta-chave:** ...
> **Notas:** planejamento territorial 0; construção procedural 8; Unreal→dados 5; ciclo LLM 0; animação 0 (fora de escopo).
> **Pode ensinar ao Director:** ... (código/testes)
> **Não comprovado:** ...
> **Arquivos:** caminho completo de AVALIACAO.md e evidências.

Para muitos repos, o usuário pode pedir um balanço agregado com as melhores técnicas por critério; a resposta usa índice e comparativo, não relê todos os clones.
