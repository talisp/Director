# Checkpoint de entrega — 21/10/2026

Autorizacao: publicar por blocos e atualizar Director-publicado a cada entrega
validada. Nao usar Unreal; nao usar GLM. Testes do Hermes, quando necessarios,
usam Luna explicitamente. A planta local modificada por outro trabalho fica fora
dos commits. Este documento e a issue #48 preservam a ordem em caso de interrupcao.

## Sete passos e criterios

| Passo | Estado inicial desta rodada | Prova para concluir / dependencia |
|---|---|---|
| 1. Consolidar correcoes locais | Em fechamento | Publicar hierarquia USD, skill 0.5.20, medidor e patch Hermes; testar reaplicacao e instalar em pasta estavel |
| 2. Aquisicao Hermes/Luna | Pendente sucesso positivo | Buscar remoto, planejar, baixar autorizado e registrar; lote de 200 KB foi corretamente recusado, nao e sucesso de download |
| 3. Preservacao e reutilizacao | Pendente | Comparar identidades/arquivos anteriores; repetir pedido sem duplicar ou baixar novamente |
| 4. Recusa e recuperacao | Parcial, testes deterministas existentes | Conferir regressao de interrupcao, dependencia, arquivo divergente, entrada invalida e metadado desconhecido; registrar limites reais |
| 5. Publicacao e instalacao | Continua em cada bloco | PR com evidencias, merge e fast-forward do Director-publicado; comentarios nas issues, sem fechar criterios nao testados |
| 6. Uso real em cena | Bloqueado por restricao expressa | Nao executar agora: importacao, escala, apoio, colisao, montagem, identidade e preservacao requerem Unreal |
| 7. PA e contexto | Parcial | Medir pedido completo e custo sem confundir bytes/replay com tokens cobrados; PA espacial completo depende do passo 6 |

## Evidencias ja conferidas

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
