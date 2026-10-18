# Diagnosticos de execucao — bloco 2

O CLI e o runner de ensaios devolvem `diagnosticos`, separados de `ok` e do veredito de qualidade.
A Ponte le apenas o intervalo do log do laboratorio que atravessou cada operacao. Usa o comando
nativo FlushLog antes da leitura, sem adicionar esperas nem esconder avisos do motor.
Mensagens iguais sao agrupadas com contagem, primeira/ultima ocorrencia, nome da operacao,
mundo quando conhecido e referencia por arquivo/offset/intervalo. O contexto recebe ate oito grupos;
o log original continua no laboratorio. Excecoes Python preservam seu rastro pelo caminho anterior.

## Limites explicitos

A correlacao e temporal, nao causal. O arquivo e selecionado entre logs ativos pelo mtime, sem
backups; duas instancias simultaneas podem tornar a selecao ambigua. O laboratorio deve ter um
editor operacional. Eventos assincronos podem surgir depois. Mundo de script arbitrario nao e
presumido. Coleta ausente, truncada, rotacionada ou sem flush confirmado e incompleta.
Zero avisos nao prova qualidade da cena nem ausencia de eventos atrasados. Falha de leitura nao
mascara o erro da operacao. Nao ha captura de stdout ao vivo nem rollback automatico de ensaio.

## Evidencias em 18/10/2026

- Fonte instalada do UE 5.8.3: PythonScriptPlugin/PyCore.cpp mostra que execute_python_command_ex
  captura logs Python; isso nao equivale a todos os avisos nativos de fisica/navegacao.
- UnrealEngine.cpp, HandleFlushLogCommand, confirma FlushLog no motor instalado.
- Leitura nativa GetMass duas vezes no Floor sem fisica: operacao bem-sucedida, dois avisos PIE
  identicos devolvidos em um grupo, nenhuma mudanca no inventario. A primeira prova revelou
  buffer de log e categoria PIE, corrigidos antes desta entrega.
- Excecao Python provocada: ValueError com rastro, falha declarada e inventario inalterado.
- Testes offline incluem eventos alheios no intervalo, rotacao/ausencia e truncamento do retorno.
- Hermes real: sessao local-11b9cb5e044d76481931dd06da248b255d8f35be27b42a48daab62442e221316,
  uma chamada terminal (1,931 s), 26,514 s no total, entrada acumulada 24.404 tokens (11.703 cache),
  saida 970. Recebeu e relatou os dois avisos, correlacao temporal e ausencia de mudancas,
  sem ligar fisica nem tentar corrigir o teste. Nao compara latencia de pedidos diferentes como benchmark.

Procedimento/backup: ensaios existentes guardam script exato/hash, erro/retorno e inventarios.
Os registros locais ficam em work/pipeline_20261018/diagnosticos e work/ensaios.
O conteudo de producao nao foi usado. Estado final deve ser conferido por contexto/estado.

Aprendizado reutilizavel: quando um aviso aparece no editor mas nao no retorno, verificar categoria
e buffer antes de supor que o agente ignorou o aviso. API Python e mensagens nativas sao canais
diferentes. Essa conclusao foi reaplicada em LogPython e em PIE/GetMass. O mecanismo reutiliza
o log e o FlushLog existentes; nao instala observador, scheduler ou plataforma de memoria.

Outros criterios de #14/#24/#38, inclusive aprendizagem reaplicada pelo operador, API correta
em um novo problema e cancelamento/interface real, continuam pendentes.
