# Composicao de salas — bloco 4, 18/10/2026

`planejar CENA PEDIDO.json` aceita uma lista de salas com medidas e adjacencias.
Usa o OR-Tools CP-SAT ja instalado, com restricoes de separacao/parede compartilhada,
contato minimo e posicoes fixas. Minimiza a caixa que envolve o conjunto. Devolve
`ficha_salas` para o executor existente, sem criar uma macro de casa/corredor/vila.

Exemplo de entrada:

```json
{"salas":[{"id":"sala","largura_m":4,"comprimento_m":3},{"id":"cozinha","largura_m":3,"comprimento_m":3}],"adjacencias":[{"salas":["sala","cozinha"],"lado":"leste"}]}
```

`lado` e opcional. `contato_minimo_cm` padrao e 120. Cantos das salas ja existentes
permanecem fixos; os moveis e outros objetos nao sao replanejados. Se o tamanho novo
nao couber, o plano falha em vez de deslocar silenciosamente outros comodos.
Adjacencias incompativeis mostram o conjunto de pares conflitantes encontrado pelo solver;
nao atribuir a cada par isolado uma impossibilidade que so existe em conjunto.

`revisao_base` acompanha a ficha proposta. Se a planta mudou, o executor recusa
antes de aplicar. Fichas antigas sem esse campo continuam aceitas. Uma proposta
`sem_alteracoes:true` nao precisa ser aplicada. A aprovacao e da distribuicao, nao
da funcao/completude da casa ou da circulacao, que exigem aberturas e verificacao real.

## Passagem sem porta

`colocar tipo:passagem` usa sala/parede/posicao_m/largura_m/altura_m como os outros vaos.
Ela corta a parede compartilhada existente sem criar folha nem ator artificial. `observar`
explica isso e devolve os parametros reais das paredes associadas. Minimo 70 x 178 cm
considera capsula 34/88 com folga de 2 cm; nao garante NavMesh ou uso confortavel.

## Por que este incremento

A planta atual ja representa salas, vaos, paredes em comum e identidade. O gargalo era
escolher posicoes que satisfizessem varias relacoes antes de construir. Reutilizar esse
contrato e o CP-SAT acrescenta composicao, sem outro resolvedor, plataforma ou gerador
especifico de casa. O Unreal continua construindo por Blueprints e medindo colisao/navegacao.
PCG/distribuicao visual de assets nao substitui essa validacao de adjacencias; nao foi
adotado outro pipeline geometrico nem se afirma limitacao geral do PCG.

Limites atuais: retangulos, orientacoes dadas pelas medidas em x/y, parede de 15 cm,
resolucao de 1 cm, ate 32 salas e prazo de solver ate 10 s. Status FEASIBLE nao prova
area minima global; so OPTIMAL. O incremento nao resolve terreno, vila, interiores
nao retangulares nem decisao semantica de todos os comodos necessarios.

## Evidencias

- Fechamento em 18/10: 130 testes Director + 11 guarda aprovados, incluindo recusa
  de plano antigo sem apply. Logs locais em work/pipeline_20261018/*fechamento.log.
- Offline: quatro comodos em duas variacoes de medidas; ficha aceita pelo nucleo;
  conflito entre salas fixas identificado; alteracao local preserva outro comodo/movel;
  passagem de 65 cm recusada e parede cortada uma vez sem ator proprio.
- Native: sala 400x300, corredor 150x300, quarto 300x300 e banheiro 200x300 cm,
  planejados em conjunto. Quatro raios internos de cada comodo conferiram todas as medidas.
  Tres passagens sem porta; apos expansao externa de 20 cm, os demais objetos logicos
  permaneceram identicos e TODOS os 19 atores anteriores conservaram seus caminhos.
- Boneco cruzou sala/corredor nos dois sentidos: 7,1 e 6,8 cm do destino, limite 10,
  parado. Navegacao 5/2 explicita, com backup restaurado ao fim.
- Outra configuracao, origem em (2 m,1 m): sala e cozinha ligadas; cozinha aumentada
  de 300x300 para 350x300, medida no motor. Mesa da sala integralmente identica,
  identidades preservadas e capsula atravessou o vao. Cena original restaurada.
- Plano antigo foi recusado no laboratorio; observar a passagem devolveu VaoLargura=100,
  VaoAltura=210 e VaoBase=0 da parede real. Nao houve nova tentativa de alteracao.

Registros locais em work/pipeline_20261018/casa. Cenas piloto no laboratorio, fora do Git.
Nao e teste de pedido humano completo pelo Hermes; essa medicao continua em #4.
