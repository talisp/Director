# Revisao da abertura da porta — 18/10/2026

## O que aconteceu

O Hermes conseguiu abrir a porta. Entre o pedido e a resposta final foram 587,8 s e 45 chamadas:
27 terminal, 7 write_file, 6 read_file e 5 patch. A primeira ficha (porta1, angulo 90) estava correta.
Em 28,5 s o executor recusou por uma parede esperada na planta, mas ausente no editor.
O restante incluiu investigacao de codigo, inventarios e scripts experimentais.
O ensaio de abertura teve tres falhas de API antes da execucao bem-sucedida;
as tres falhas registraram zero alteracoes. Nao houve medicao precisa que separe inferencia de cada ferramenta.

## Causa confirmada e recuperacao local

O level L_sala correspondia a planta rev17 do checkout antigo, nao a rev8 usada em Director-correcoes.
A planta rev17, conciliando apenas o angulo da porta ja aberto pelo Hermes, produziu zero diferencas,
zero pecas faltantes/extras e zero divergencias estruturais contra o inventario completo.
A rev8 foi preservada em backup; a planta validada foi recuperada no checkout ativo.
O arquivo fonte do checkout antigo permaneceu intacto. Nao se reconstruiram paredes nem se apagaram comodos.
Essa recuperacao e local; o estado particular da cena nao foi incluido no commit de codigo.
Definir uma fonte persistente entre checkouts e retomada da cena continua pendente em #45.

## Correcoes pontuais encerradas nesta entrega

- Recusa deixa de afirmar exclusao manual e retorna diagnostico com planta, revisao, level, faltantes e extras.
- `estado` identifica o arquivo e level usados, inclusive quando outra cena esta aberta.
- `ensaio` avisa quando nao ha variavel `resultado`; sucesso de execucao continua distinto de dados devolvidos.
- Ajuda e skill orientam usar observar/estado e a API existente antes de escrever inventarios.
- Reparo de `_pid_vivo` revisto: compara bytes ASCII de PID/nome, sem decodificar mensagens localizadas de tasklist.
  O reparo inicial do Hermes foi preservado antes da revisao. Resolve #46.
- SOUL distingue tarefa de cena de alteracao permanente do programa. Uma autorizacao de desenvolvimento ja dada
  continua valida; nao ha aprovacao por comando. Skill 0.5.1 instalada, preservando notas locais anteriores.

## Verificacao

104 testes Director e 11 da guarda passaram, com quatro novas regressoes.
No Windows real, PID do editor reconhecido e PID inexistente recusado, sem erro de codificacao.
Pelo executor normal, fechar levou 1,750 s e abrir 1,641 s, incluindo consulta de capsula:
fechada bloqueou na Folha de porta1; aberta liberou a passagem. So o parametro Angulo da porta mudou;
apos o ciclo, o inventario inteiro era igual ao inicial e a planta estava conciliada.

A tentativa posterior de medir novamente o Hermes foi interrompida: o endpoint 8080 encerrou conexoes
(WinError 10054) e a sessao entrou em auto-recovery sem chamadas de ferramenta. Portanto, nao ha benchmark
de latencia total do modelo depois da correcao. Os tempos acima sao do executor, nao da LLM.
A porta foi devolvida a 90 graus depois dessa tentativa. Cena salva, sem Play ou pacotes pendentes.

O perfil Director foi removido e servido novamente pelo controle nativo do host Hermes, com confirmacao
`unserved:director` e `served:director`. Default, codex-unreal-economico e hermes-dev permaneceram servidos.
O comando CLI de restart isolado havia recusado por multiplexacao; nao se reiniciou o host inteiro
nem se alterou o Hermes para contornar essa recusa.

Registros locais e backups: `work/revisao_porta_20261018/`. Logs brutos e arquivos de perfis nao foram publicados.
Nenhuma solucao de armazenamento global, novo comando de porta, SQL ou alteracao de biblioteca integra esta entrega.
