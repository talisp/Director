# Checkpoint de entrega — 21/10/2026

Autorizacao: publicar por blocos e atualizar Director-publicado a cada entrega
validada. Nao usar Unreal; nao usar GLM. Testes do Hermes, quando necessarios,
usam Luna explicitamente. A planta local modificada por outro trabalho fica fora
dos commits. Este documento e a issue #48 preservam a ordem em caso de interrupcao.

## Sete passos e criterios

| Passo | Estado inicial desta rodada | Prova para concluir / dependencia |
|---|---|---|
| 1. Consolidar correcoes locais | Entregue PR #83; ajuste CRLF na entrega seguinte | Hierarquia, skill, medidor e patch instalados. Regressao publicada detectou CRLF no reaplicador, corrigido com teste dedicado |
| 2. Aquisicao Hermes/Luna | Concluido no escopo offline | Download real de 5 arquivos / 1.337.456 bytes, registro conferido; antes tambem recusou teto insuficiente |
| 3. Preservacao e reutilizacao | Concluido no escopo offline | Cinco arquivos reutilizados; identidades e arquivos anteriores preservados; SQL integro |
| 4. Recusa e recuperacao | Validado offline; sem certificacao universal | Hash divergente, orcamento/autorizacao, dependencia, entrada indevida, retomada e falha SQL cobertos por testes; novo caso de queda na segunda dependencia |
| 5. Publicacao e instalacao | Continua em cada bloco | PR #83 incorporado/instalado c9bab4b; segunda entrega documenta o ensaio e corrige CRLF; comentarios por criterio |
| 6. Uso real em cena | Bloqueado por restricao expressa | Nao executar agora: importacao, escala, apoio, colisao, montagem, identidade e preservacao requerem Unreal |
| 7. PA e contexto | Offline medido; espacial pendente | PA offline atendido em 33,635 s, 5 chamadas/6 ferramentas; bytes/cache registrados. Comparacao controlada e PA espacial dependem de nova bateria |

## Evidencias ja conferidas

Relatorio do bloco seguinte: [aquisicao, preservacao, contexto e limites](acervo-offline-luna-2026-10-21.md).

- Fonte publicada de partida: 6ba4eaa (PR #82). Trabalho de hierarquia: 62a400c.
- 25 testes de preparacao/referencias/medidor e 4 de rota nativa passaram.
- Mais 3 testes do reaplicador passaram: patch real em copia, backup/idempotencia,
  recusa de alteracao independente e de base incompativel. Nenhum usa o editor.
- SQL principal: quick_check `ok`, foreign_key_check sem violacoes.
- Luna respondeu numa sessao real com provider openai-codex, uma chamada e zero
  ferramentas; nao apenas o nome configurado. Sessao terminada em `c29bf60`.
- Ensaio real de aquisicao terminado em `57493d1`: recusou lote 1.337.456 bytes
  acima de 200.000, relatou desconhecimento de dimensoes/carga; 18,735 s. Nenhum
  download foi concluido por esse ensaio. Dados brutos ficam em R:, nao no Git.

## Correcao local do Hermes (#81)

Tres causas confirmadas: perda da proveniencia do adaptador LOCAL na
canonicalizacao de perfis; fallback ao modelo padrao quando faltava politica;
override de provider herdava endpoint/configuracao do modelo anterior. A CLI
tambem rejeitava run_budget que o gateway ja suporta.

Patch em `hermes/correcoes/rota-native.patch`, base e fingerprints em JSON.
`python hermes/manutencao_rota.py` apenas confere; `--aplicar` faz backup e aplica
somente na base compativel, recusando alteracoes desconhecidas. Nao reinicia
gateway nem altera credenciais. E um patch local versionado aqui, nao uma
correcao incorporada ao upstream Hermes. Apos atualizar Hermes, revalidar a base.

## Limites que nao podem desaparecer da fila

#75/#36: hierarquia declarada nao comprova articulacao Chaos, superficie util ou
fisica. #39: medidor nao comprova melhoria de custo ou compressao. #38: orcamento
na CLI nao comprova interface/cancelamento concorrente. #6 exige aplicativo;
#17 exige reinicio/redundancia; #22 exige novas sessoes restritas. #35/#68/#4
conservam os criterios espaciais/conversacionais. Mixamo nao entra neste ciclo.
