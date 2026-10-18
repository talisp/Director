# Portas e filtro 2D — bloco 4, 18/10/2026

Ficha de porta aceita `dobradica: inicio|fim` e `sentido: dentro|fora`. Omissao preserva
a ponta/rotacao anteriores em cada parede. Angulo logico continua 0..120; o adaptador
converte o sinal para o Blueprint e de volta na conciliacao/incorporacao do Play.
Derivacao e geometria compartilham o mesmo calculo. Nao se criou Blueprint novo.

O nucleo recusa folha na posicao solicitada sobre movel registrado; diz qual porta e movel.
O filtro 2D considera a folha e o planejador usa a dobradica escolhida. Continua conservador
nas reservas de uso. Nao ha verificacao continua do arco percorrido, malha exata do movel,
colisao com atores externos a planta ou promessa de melhor layout possivel.

Janela em parede compartilhada permanece permitida, mas gera `avisos` com os dois comodos,
motivo e proxima acao, nos retornos de fazer/estado/observar/planta2d/planejar.
O operador deve perguntar ou declarar a escolha de janela interna.

## Verificacao

- Testes: 16 combinacoes de parede/dobradica/sentido, compatibilidade por omissao,
  valor invalido, recusa atomica por movel, conciliacao de angulo negativo e aviso de janela.
- 121 testes Director + 11 guarda aprovados, incluindo os filtros de porta/janela,
  passagem bloqueada pela cama, quarto_sol e propostas filtradas.
- No laboratorio, quatro combinacoes oeste (inicio/fim x dentro/fora) tiveram caixas da
  Folha coincidentes com o calculo (< 0,01 cm) e varredura de capsula livre. Fechada bloqueou.
- O Construction Script usa espessura local Y=0..4, nao -2..2. Medicao real confirmou isso;
  a aproximacao antiga do filtro foi corrigida. A parede de 15 cm tambem entra no eixo real.
- Um primeiro trace tocou o piso: centro z89 deixava a capsula exatamente sobre o topo z1.
  O teste de passagem foi repetido em z92, com a mesma capsula 34/88, separando contato de piso
  de bloqueio na porta. Caminhada real confirmou que o piso e transitavel.
- Porta oeste, dobradica inicio, para dentro: com navegacao 5/2 no level de piloto, o boneco
  atravessou nos dois sentidos e parou a 6,9 e 7,8 cm (limite 10), parado. Backup de navegacao
  restaurado, boneco removido, Play encerrado e cena original integralmente preservada.
- Uma regressao de nome de variavel no planejador foi capturada antes da publicacao e
  corrigida sem mudar limites. O primeiro teste de trace tambem usava o campo do CLI `livre`
  no retorno nativo, que fornece `acertou`; o ensaio foi corrigido para ler o contrato real.

Registros locais: work/pipeline_20261018/portas. Nenhum level ou planta pessoal no commit.
Isso resolve a configuracao da porta e o aviso 2D; nao encerra #10 como solucao geral
de navegacao regional/retomada. O uso de 5/2 foi explicito, isolado e restaurado.
