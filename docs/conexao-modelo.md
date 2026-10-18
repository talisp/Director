# Conexao do modelo — constatacoes de 18/10/2026

A porta do editor do laboratorio e 8011. A porta do modelo e outra conexao.
Nao interpretar um listener TCP como prova de que o modelo responde: consultar `/health`
e conferir modelo carregado antes de iniciar uma rodada de inferencia.

Nesta verificacao, a sessao SSH que ocupava 8080 local encaminhava para 8081 remota.
O `/health` remoto do modelo respondeu na 8080, enquanto 8080 local encerrava a conexao.
Essa sessao era interativa, por isso nao foi encerrada para trocar seu encaminhamento.
Foi aberto outro encaminhamento SSH, somente loopback, 8082 local para 8080 remota,
com ExitOnForwardFailure e ServerAliveInterval/ServerAliveCountMax. O perfil Director
passou a usar esse endpoint; o config anterior foi guardado em backup local. Os outros
perfis e a sessao SSH anterior foram preservados.

O `/health` da 8082 confirmou `qwen3.8-flash-next-q8_0` carregado no Strata.
Isso nao comprova redundancia nem recuperacao depois de reiniciar o Windows. O novo
encaminhamento e um processo SSH desta sessao, sem servico ou agendador adicional.
Uma falha deve ser diagnosticada por camadas: listener local, destino do encaminhamento,
saude remota, saude pelo encaminhamento e entao uma rodada curta do agente.

Nao iniciar dezenas de retries ou alterar 8081 para compensar erro de rota. Uma segunda
sessao SSH sem encaminhamento do endpoint nao e redundancia do modelo; duas pontes
na mesma porta/endereco tambem nao ficam escutando ao mesmo tempo. #17 permanece aberta
ate conferir os caminhos pretendidos e a recuperacao persistente.

## Atualizacao operacional

O processo temporario foi substituido pela tarefa nativa `Director_Qwen_Tunel_8082`.
Disparo no login do usuario e repeticao a cada minuto, instancia unica; iniciador escondido
acompanha a vida do SSH. `RestartOnFailure` sozinho nao se confirmou no ensaio; a repeticao
nativa recuperou o listener 47,1 s apos encerrar seu SSH, com novo PID e /health ok.
Isso elimina a dependencia do terminal do Codex, mas ainda nao prova reinicio real do
Windows/login nem redundancia. Detalhes, cuidado ao parar a tarefa e prova em
operador-publicado.md. Os outros tuneis e perfis foram preservados.

Aliases pessoais, enderecos remotos, credenciais e config.yaml bruto nao sao publicados.
