# Operador publicado separado do desenvolvimento

Fechamento operacional de 18/10/2026, ligado ao pipeline #48 e conexao #17.

## Codigo do Hermes

O perfil Director usa uma instalacao Git dedicada em `%USERPROFILE%/Director-publicado`,
fora das pastas de trabalho dos agentes. Seu HEAD deve ser um commit publicado de `origin/main`,
com arquivos rastreados limpos. O perfil, SOUL e skill devem apontar para essa mesma pasta.
Nao desenvolver nela; experimentos/alteracoes de programa ficam na copia de desenvolvimento.
Plantas, biblioteca e trava continuam na fonte compartilhada do laboratorio: nao copiar
uma planta antiga para a instalacao nova nem selecionar automaticamente a maior revisao.

As dependencias opcionais ficam em venvs proprios dessa instalacao, criados com os
requirements publicados; nao usar Python/site-packages da pasta de trabalho de um agente.
O interpretador principal existente do unreal-macros continua sendo reutilizado.

Atualizacao futura: terminar testes e publicar o PR primeiro; conferir limpeza da pasta
publicada, buscar `origin/main` e avancar somente por fast-forward. Se houver divergencia,
recusar e investigar, sem reset/clean ou descarte automatico. Instalar os templates da
pasta publicada com o Python do Director, conferir hashes e recarregar somente o perfil
Director pelo controle nativo do gateway compartilhado. Nao reiniciar todos os perfis.
Registrar commit instalado e resultado dos testes. Publicar nao atualiza automaticamente
essa pasta: a etapa de instalacao/conferencia deve fazer parte do fechamento de cada entrega.

## Conexao apos reinicio

Usar o Agendador de Tarefas nativo do Windows, no login do proprio usuario, para iniciar
o tunel dedicado que atende o perfil Director. Nao depender de um processo iniciado pelo
terminal do Codex. A tarefa nao exige guardar senha e usa o SSH/identidade ja configurados.

Executar SSH escondido com `BatchMode`, `ExitOnForwardFailure`, `ConnectTimeout` e
`ServerAliveInterval/ServerAliveCountMax`; escuta somente loopback. Encaminhamento e
alias pessoais ficam na configuracao local, fora do Git. Nao alterar a sessao interativa
anterior nem o acesso web do Strata. Instancia unica, sem limite de duracao; reinicio da
tarefa em falha com intervalo de um minuto. Isso reaproveita o Windows, sem scheduler novo.

O iniciador local usa WScript com janela escondida e espera pelo SSH, devolvendo seu
codigo de saida; assim a tarefa acompanha a vida do processo e aplica a recuperacao.
Nao basta agendar um lancador que termina imediatamente deixando SSH sem supervisao.

Validar `/health`, modelo carregado, dono do listener, tarefa em execucao e recuperacao
apos encerrar apenas o SSH dessa tarefa. Nao reiniciar o Windows durante trabalhos de
outros agentes. O disparo real depois de reiniciar/logar deve permanecer explicitamente
na lista de verificacoes pendentes ate acontecer. Isso nao prova redundancia entre pontes.

Referencia de configuracao: [Microsoft — New-ScheduledTaskSettingsSet](https://learn.microsoft.com/en-us/powershell/module/scheduledtasks/new-scheduledtasksettingsset?view=windowsserver2025-ps),
consultada em 18/10/2026, e cmdlets ScheduledTasks disponiveis no Windows instalado.

## Busca e comprovacao nas issues

`catalogo.consultar` agora desconsidera palavras comuns da consulta e os avisos genericos
dos indices antigos. Novos indices guardam orientacao em `aviso`, separada da descricao
pesquisavel. Descricoes reais de assets continuam pesquisaveis.
No mesmo cache local, "cama de solteiro" devolvia 43 candidatos, incluindo DirectionalLight,
ExponentialHeightFog e SkyLight; corrigido, devolve apenas cama1 e SM_SM_CamaSolteiro.
Isso verifica pertinencia da busca, nao equivalencia funcional/dimensoes de cada candidato.

As issues #12/#29/#33/#37/#40 receberam comentarios proprios com prova, limites e links
para documentos. Encerramento automatico pelo PR nao substitui esse comentario.
A orientacao da guarda instalada ja usa `process_manage(..., timeout=60)` desde o PR56;
foi acrescentada regressao para impedir a volta de `timeout_seconds` na mensagem.
