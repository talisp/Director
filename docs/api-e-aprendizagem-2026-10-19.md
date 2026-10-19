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

A consulta real e a aprendizagem pelo GLM serão registradas após os ensaios. A exportação
e esses testes, sozinhos, ainda não encerram as issues: #24 exige o operador usar a
referência antes de executar; #14 exige procedência e reaplicação numa variação.
