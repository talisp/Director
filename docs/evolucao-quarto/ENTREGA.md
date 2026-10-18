# Entrega local para auditoria — 17/10/2026

O trabalho original foi implementado e testado por etapas locais. Ha pendencias
explicitadas abaixo; nao declarar todas as issues corrigidas. Nenhum push, PR,
merge ou fechamento de issue foi feito. Os unicos registros externos publicados
foram os comentarios de reproducao/aproveitamento solicitados.

| Issue | Resultado e prova | Limite ou pendencia |
|---|---|---|
| #22 | Configuracoes de projeto Codex/Claude validas; sem mudar configuracao global | Novas sessoes reais dos dois agentes ainda nao provaram zero aprovacoes; perfil Hermes externo nao reinstalado |
| #23 | Pasta oficial, hash, antes/depois e erro registrado; 27 scripts temporarios atuais preservados e 37 execucoes no editor | Helpers de cliente identificados separadamente, sem inventar tempos retroativos |
| #26 | Relatorio separa pedido/plano/medido/nao verificado; quarto Sol medido 260 x 350 cm | Metodo exige quatro paredes atingidas por raios; nao prova fisica |
| #25 | Na copia de auditoria, Hermes reprova por 24/15 cm externos; Sol passa com 5 corpos estaveis e 4 chegadas de 7,1 a 7,6 cm; inventario antes/depois igual | Apoio e envelope sao aproximacoes; nao testado sentar, deitar ou abrir armario |
| #13 | Cadeira dinamica adotada e duplicada com 8 kg; banco de 5 partes virou objeto registrado, 8 kg; objeto fora da sala recusado | Massa de perfil e estimativa; conversao nao transfere logica de Blueprint, inclinacao tem limite declarado |
| #21 (#19/#20) | Busca cadeira acha Cadeira_mesa1 primeiro na cena limpa, depois projeto e chairDesk offline | Categorias/aliases sugerem candidatos; nao certificam funcao |
| #12 | CP-SAT pronto, medidas reais, reservas, area de uso, paredes planejadas compartilhadas e filtro Shapely | Modelo retangular 0/90; nao e prova de minimo global; filtro reprovado nao dispara nova busca automatica |
| #10 | Ajustes declaram escopo e guardam backup; restauracao comprovada 38/19/19 cm; ajuste global explicito chegou a 7,3/6,8 cm em duas orientacoes apos salvar/reabrir | Refinamento regional continua sem resolver norte-sul. Tempo observado global 0,52 s; CPU, memoria e FPS nao aferidos |
| #24 | Cache gerado no Unreal 5.8.3: 2.844 entradas, 26 classes, 1,26 MB; consulta offline curta; simbolo inventado retorna zero | Nao cobre todos os plugins; doc nao garante execucao |
| #27 | Seis modelos offline, 20.814.564 bytes, primeira inspecao 9,969 s; 5 GLB Kenney mais FBX Fab existente | Nao importa nem configura fisica no Unreal; escala artistica requer ajuste; licenca Fab nao inferida do cache; SQL/RAG permanente nao decidido |
| #28 | Nome refletido correto; CPU true -> false no inicio e true/restaurado no fim; falhas separadas da simulacao | Consumo CPU nao medido; mudanca somente de sessao |
| #29 (referencia usada) | Adaptados metodos MIT SceneSmith; Sol offline: 1 regiao, proporcao 1, 1,599 ms observados; janela invadida 40 cm, porta 60 cm e cama bloqueadora reprovam | Parcial: nao foi adicionada recusa de janela em parede compartilhada. Uma regiao nao prova acesso a todos os alvos |

#30 e #31 foram lidas por solicitacao posterior e nao tiveram codigo/fluxo
incorporado. A comparacao Qwen com ASCII e a revisao por notas/rodadas nao foram
executadas. O teste humano final do quarto tambem nao foi executado.

Comandos, com um exemplo de cada: [COMANDOS.md](COMANDOS.md).
Registro de pesquisa, ensaios e limites: [EXECUCAO.md](EXECUCAO.md).
Skill atualizada: `hermes/skills/director/SKILL.md` (fonte do repositorio).
Aviso MIT: `THIRD_PARTY_NOTICES.md`.

## Testes e preservacao

70 testes Director passaram no ambiente opcional com OR-Tools e Shapely. No
Python comum, 64 passaram e 6 opcionais foram pulados. Quatro testes do complemento
Hermes passaram. Compilacao Python e diff --check sem erros nas verificacoes.
Os testes de CPU e persistencia de backup de falha incluem simulacoes; os numeros
de contencao, massa, caminhada e estabilidade acima vieram do Unreal real.

A cena original sala e sua planta mantiveram os hashes ao final. Todos os ensaios
de mudanca foram feitos em copias independentes. A malha de navegacao do ensaio
regional foi restaurada; o teste com celula 1 cm (divisor de 19) tambem falhou no
norte-sul, demorou 3,197 s ate pronta, e nao foi tratado como correcao.

Cena final aberta: `hermes_quarto_final`, revisao 14, 17 pecas e 10 outros atores,
zero diferencas entre planta e editor, sem pacotes por salvar. Nao ha quarto novo.
Pedido literal e COMO_TESTAR.md: pasta local do ensaio final indicada na mensagem
de entrega. Antes de usar uma sessao nova do Hermes, conferir a instalacao da
skill fonte no perfil. Nao substituimos arquivos do perfil externo nesta entrega.

Comentarios publicados, sem encerrar as issues:
- https://github.com/talisp/Director/issues/28#issuecomment-6237793572
- https://github.com/talisp/Director/issues/29#issuecomment-6238663883

Os branches locais sao empilhados e incluem um branch de validacao integrada.
As cenas locais e a alteracao preexistente de sala/planta.json ficaram fora dos
commits. Os scripts atuais e versoes anteriores foram preservados em work,
com manifesto que distingue execucao no editor de helper do cliente.
