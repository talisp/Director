# Validação conversacional da candidata — 19/10/2026

## Ambiente e limites

Perfil real `director` do Hermes; modelo configurado e anunciado pelo endpoint:
`glm-5.3-flash`, provedor local `glm-maya`, servidor na porta 8082. Não se alteraram
modelo, raciocínio, configuração, skill instalada ou outros perfis durante os ensaios.
O ping sem ferramentas respondeu `CONEXAO_OK`: 17,631 s de parede, saída 0.

O operador continuou na instalação fixa publicada. Um adaptador temporário, fornecido
explicitamente ao agente, executou a candidata imutável `7762188` em namespace separado,
com trava e conferência do laboratório/level. Não foi teste cego da skill instalada:
o agente recebeu objetivo, consultas, limites e acesso ao adaptador. Não demonstra PA
geral nem capacidade de inventar sozinho a infraestrutura do ensaio.

## Resultados efetivamente conferidos

| Pedido delimitado | Decisão do GLM | Evidência independente |
|---|---|---|
| Recuperar navegação leste–oeste sem afinar o level | Reconstrução nativa; diagnóstico redundante antes dela | Rotas completas de 730 cm nos dois sentidos; perfis 38/19/19 e tile 1000 preservados; atores preservados |
| Corrigir rota norte–sul parcial com escopo declarado | Propôs HIGH 5/2; recebeu recusa por tiles 988/988/1000; usou proposta explícita tile 950 e mediu novamente | Rotas completas de 743,6 cm nos dois sentidos; DEFAULT 19 e raio 35 preservados; varredura sem colisão; atores preservados |

A autorização específica do segundo ensaio incluía mudar tile, entendendo seu alcance
no level inteiro. O agente não generalizou esse consentimento para outras cenas.
`pronta=true` e `conectividade_verificada=false` foram corretamente diferenciados das
consultas de caminhos. Nenhum código do programa foi editado pelo agente.

O primeiro ensaio consumiu 222,271 s de parede; o segundo, 146,996 s. O servidor respondeu;
a demora inclui inferências e ferramentas, não equivale a falha de conexão. Houve sete
chamadas no primeiro: skill, quatro terminais e duas escritas de JSON. Não se otimizaram
parâmetros do GLM nem se comparou seu desempenho com o modelo anterior.

Os contadores exportados pelo Hermes foram entrada/saída/cache lido 153292/3770/142860
no primeiro resultado e 335815/5906/319288 no resultado da continuação da mesma sessão.
Não somamos esses valores como consumo líquido independente: a continuidade pode agregar
contadores, e entrada inclui cache. Não há medição de custo financeiro ou benchmark.

`write_file` funcionou nas duas escritas da sessão CLI; isso **não encerra #6**, que trata
da interface do aplicativo. Uma primeira tentativa de retomar com overrides de criação
foi recusada antes da inferência (zero tokens); retomou-se sem mudar a política congelada.

## Preservação e rastreabilidade

Somente cópias `L_glm_nav_ew_20261019` e `L_glm_nav_ns_20261019` foram usadas. Ao terminar,
salvou-se a cópia própria e reabriu-se `L_sala`: inventário integral e configuração de
navegação idênticos aos registrados antes, fora de Play, sem pacotes por salvar.
Não houve acesso ao projeto cinematográfico nem ao Blender.

Transcrições, pedidos, adaptador, snapshot da candidata, backups e comparações locais:
`work/glm_20261019/`, ignorado pelo Git. Sessão de conexão
`local-562834d0473d254ab0428865325ff90a48929a8bc63c9163d0e6dca647c52c48`;
sessão dos dois ensaios
`local-1b0b5cb6120137ff6f97f0a2b9b65b59f08944798f7e95579f8fb86658fae183`.

Mais 25 testes dirigidos passaram nesta rodada (12 navegação, 13 guarda). A regressão
completa anterior permanece documentada no relatório principal; não foi repetida sem
alteração de código. Memória/FPS, cena grande e seleção autônoma sem adaptador seguem
fora da evidência. #14 exige reaplicação da aprendizagem com procedência em outra variação;
esta correção após feedback não basta para encerrá-la.
