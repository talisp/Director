# Acervo SQL pelo Hermes — 21/10/2026

## Escopo e primeira tentativa

Pedido: selecionar uma mesa/estante ArtVIP catalogada mas ainda nao baixada,
conferir tamanho/licenca/espaco e baixar um unico lote de ate 1 MiB em R:/CINF/BD.
Sem Unreal, Blender ou importacao. Hermes perfil director, GPT-6 Luna low.

Sessao `local-1c18499df0cbaaa972ce2a56fa30d38f646d9ba7c25d102838eedb6f6b819faf`:
NAO ATENDIDO, 19,515 s. Leu skill 0.5.12, fez quatro buscas com ArtVIP no texto,
recebeu primeiros candidatos de outras fontes e parou sem baixar.
Isso nao prova ausencia no banco: a busca lexical usa OR e nao filtrava fonte.
Nao houve falha de rede nem modelo importado nesse ensaio.

## Correcao dirigida

- `acervo.buscar`: filtro SQL parametrizado por fonte antes do limite, mantendo
  disponibilidade e aliases. ArtVIP mostra bytes do lote para triagem.
- CLI: `buscar --fonte artvip --disponibilidade remoto mesa`.
- Skill 0.5.13: consulta dirigida, exemplo completo de download autorizado,
  reutilizacao por hash e registro de derivados antes de importar.
- Download atualiza apenas o candidato afetado no indice FTS, sem reconstruir
  o indice inteiro de 14.507 objetos.
- 17 testes dirigidos aprovados (SQL e operacao), incluindo isolamento por fonte,
  limite, tamanho desconhecido, parser, hashes, cache e identidade persistente.

Consulta independente somente leitura encontrou 57 mesas ArtVIP remotas; os
primeiros oito incluem lote de 81.702 bytes. Resultado real pelo Hermes apos
correcao descrito abaixo.

## Primeiro reteste e conferencia independente

Sessao `local-8919e17dad7a0fc8f5041f848bbcdabbeba05351f0f9e690ceba3996b2189421`,
skill 0.5.13, 45,844 s. Objetivo principal ATENDIDO com desvios de procedimento:
tentou JSON literal quando a CLI ainda exigia arquivo/entrada padrao, recuperou-se
criando pedido temporario em C: e continuou apesar de orientacao para parar no
primeiro bloqueio. Isso exige melhora da interface/instrucao, nao outra macro 3D.

Baixou `bookcase007`, ID `3a963cef53ddd763abf050d70696fde366a169f522ddf9a0885f4c48c14c7c90`,
85.433 bytes, cinco arquivos, revisao ArtVIP `d22f2095bc9db29fdd4b60f4a3c4f8177e1f5e9e`.
Licenca Apache-2.0 conforme catalogo. Conferencia independente confirmou:

- Nao havia arquivo ligado a esse objeto antes; cinco tamanhos/hashes correspondem
  ao manifesto remoto fixado (SHA-256 ou Git blob conforme fonte).
- Primeira execucao baixou cinco arquivos; segunda reutilizou cinco, sem nova rede.
- Total de objetos permanece 14.507; 19 caminhos anteriores/hash/identidades preservados.
- SQL indexa um arquivo principal e guarda os cinco no manifesto de download.
  A resposta do Hermes disse cinco arquivos registrados no objeto: interpretacao
  imprecisa, nao cinco linhas na tabela `arquivos`.
- Nenhuma verificacao de fisica foi aprovada implicitamente.

Skill 0.5.14 esclarece armazenamento do manifesto e temporarios em R:. A CLI passa
a aceitar tambem JSON literal, preservando arquivo/entrada padrao. O retorno de
download identifica explicitamente o arquivo indexado e o papel das dependencias.

## Evidencias e limites

Evidencias locais: `R:/CINF/BD/Director/hermes-acervo-20261021/`.
Antes do ensaio: 14.507 objetos, 19 caminhos de arquivos registrados e mais de
3 TB livres em R:. `antes.json` guarda identidade/hash/caminhos anteriores.
Logs do Hermes nao sao prova independente de integridade dos arquivos.
Baixar USD nao comprova escala, colisao, articulacao ou importacao no Unreal.
HSSD e referencias Code4Scene/Fab continuam com as restricoes ja documentadas.
