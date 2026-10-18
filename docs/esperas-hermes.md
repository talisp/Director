# Esperas do Hermes — verificacao de 18/10/2026

Issue #38, retomada do bloco 2 depois da auditoria do pipeline.

## Defeito confirmado

No Hermes instalado, `tools/process_registry.py` declara `PROCESS_SCHEMA.timeout` e
`_SESSION_ACTIONS['wait']` chama `process_registry.wait(..., timeout=args.get('timeout'))`.
A guarda 0.3.0 escrevia `timeout_seconds`. Assim, um pedido de 300 s continuava com
`timeout=300`, ou a ausencia de `timeout` deixava o padrao configurado (180 s no codigo).
Os testes antigos verificavam apenas a alteracao do argumento errado.

Guarda 0.3.1 normaliza o alias antigo para `timeout`, remove `timeout_seconds`, limita
a 60 s e recusa valor nao numerico, infinito, zero ou negativo sem derrubar o hook.
Nao muda a duracao permitida do processo nem mata processos quando uma espera vence.

## Evidencia

- 13 testes da guarda aprovados, incluindo argumento atual, alias antigo, ambos juntos,
  ausencia, valores invalidos e chamada embrulhada em tool_call.
- API real instalada, em processo Python isolado e registro proprio. Subprocessos Python
  adotados pelo registro; nenhum processo do gateway ou de outros perfis foi controlado.
- Curto: solicitado timeout 300, guarda enviou 60; terminou em 0,751 s.
- Longo: espera de 1 s devolveu timeout em 1,009 s; proxima espera terminou em 2,037 s.
- Falho: retorno exited com codigo 7, sem fingir sucesso.
- Cancelado: kill do processo do proprio ensaio, retorno exited/-15 e processo confirmado morto.
- Registro bruto: work/pipeline_20261018/processos-native.json, fora do Git.

O primeiro arranque do ensaio falhou por dependencia Python fora do sys.path; nenhum
subprocesso havia sido iniciado. A execucao acima usou as dependencias do runtime local.
Avisos de plugins opcionais ausentes nesse ambiente isolado nao sao diagnostico do gateway.

## O que continua aberto

Isto verifica registro/process wait/kill, nao o shell do terminal (#6), mensagens visiveis
no aplicativo, botao Parar, entrada imutavel ou duas alteracoes concorrentes no gateway.
Os testes offline de mesma cena continuam passando, mas nao provam concorrencia real.
SOUL/skill orientam mensagens; nao garantem que o Qwen as publique. #38 continua aberta
para esses criterios. Nao se acrescentou scheduler, notificacao propria nem outra trava.
