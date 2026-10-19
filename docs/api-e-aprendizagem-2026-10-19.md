# Referência instalada e aprendizagem — 19/10/2026

Bloco 2, #24 e #14. A exportação anterior não incluía `CollisionEnabled` na lista
de classes e só registrava métodos chamáveis: os valores dos enums não apareciam.
A consulta também não normalizava acentos/preposições e cortava o início da documentação,
mesmo quando o termo relevante estava no final.

Correção pequena: exportar enums instalados e seus membros públicos em maiúsculas;
normalizar consultas em português e devolver trecho próximo da ocorrência, com corte
explícito. A referência continua gerada pelo motor, sem nomes de API inventados à mão.

Verificação nativa da candidata: UE 5.8.3-58210709, 2.926 entradas, 1.281.146 bytes,
nenhuma das 33 classes solicitadas ausente. A consulta exata
`CollisionEnabled.QUERY_AND_PHYSICS` devolveu o valor real do enum instalado. Inventário
integral e configuração de navegação preservados. Registros em `work/api-validada-20261019.json`.

Regressão: 145 testes Director aprovados no venv de planejamento (sem skips); teste de
biblioteca também repetido no venv próprio. A suíte no Python básico omite 22 testes por
dependências opcionais; não contamos esses skips como sucesso funcional.

## Ensaio real do operador

Perfil Director, GLM-5.3-Flash, sessão
`local-dcffe5b2b754af3cc264ce2804ffbe634e6b28287d2953705c20185b85a4a716`.
Pedido: contar modos de colisão e simulação por StaticMeshComponent, sem alterar o motor.
O GLM consultou a referência, escreveu script próprio e executou por `ensaio`: primeira
execução sem erro de API, 47 atores, 69 componentes, 68 QUERY_AND_PHYSICS e 1 NO_COLLISION,
12 com flag de simulação. Não se interpretou a flag do editor como estabilidade em Play.

O agente registrou problema, hipótese, versão, procedimento, referência, script/hash,
registro, observado, limites e recuperação como **proposta**, sem promover a skill.
Corrigiu um caminho de ator digitado errado em sua própria nota antes de concluir.

Numa cópia com conteúdo alterado, reutilizou o mesmo ensaio/script, hash
`c2ac0d6815a4b05c5f397cc3c784458e4a5ed99e58683b241051d83bd2a45e7f`.
Achou 49 atores, 71 componentes, QUERY_AND_PHYSICS 69, novo QUERY_ONLY 1,
NO_COLLISION 1 e simulação 13. As diferenças conferem com a preparação independente.
As duas execuções registram criados/removidos/alterados vazios. A cena original voltou
com inventário e navegação idênticos, sem Play nem pacotes pendentes.

Primeira investigação: 463,310 s, 16 chamadas. Reaplicação: 107,002 s, duas chamadas.
Houve consultas amplas/repetidas antes da primeira execução; não atribuir toda a demora
ao transporte ou ao Unreal (scripts: 0,453/0,547 s). `GetCollisionEnabled` inicialmente
não encontrava `get_collision_enabled`; o ensaio motivou aceitar essa diferença de grafia
na busca, devolvendo sempre o nome Python real. A regressão correspondente foi acrescentada.
Não se mediu comparação equivalente contra o Qwen anterior.

Evidências locais: `work/glm-api-20261019.jsonl`, `glm-api-variacao-20261019.jsonl`,
`glm-api-20261019/aprendizado.json`, `variacao.json` e `api-glm-prova-independente.json`;
execuções `bd69fa45...` e `3339bbe8...` do ensaio
`20261019-020526-glm-api-20261019-colisao-19efc5`. As transcrições completas ficam locais.

Isso satisfaz os critérios delimitados de #24 e #14 para o operador atual; não prova
que toda consulta futura acertará na primeira, que qualquer código gerado será seguro,
ou que aprendizagem implica promoção automática. Sem novo banco de memória ou scheduler.
