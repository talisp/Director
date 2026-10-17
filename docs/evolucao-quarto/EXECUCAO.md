# Evolucao do Director a partir do ensaio do quarto

## Pedido revisado de execucao

Implementar, nesta ordem, #22, #23, #26, #25, #13, #21 (#19/#20), #12,
#10, #24, #27 e #28. Usar os corpos e comentarios das issues como criterios.
Uma entrega local por issue ou grupo pequeno, sem push, PR, merge nem fechamento
de issue ate autorizacao humana explicita. Nao incluir caminhos pessoais ou logs
brutos no GitHub. Preservar alteracoes preexistentes no checkout.

O teste final humano e o pedido literal de quarto registrado no anexo original.
Preparar uma cena separada a partir da revisao anterior aos quartos; nao executar
esse pedido pelo Hermes. Os quartos de referencia permanecem para auditoria.

Correcoes ao prompt original:

- O nucleo ja compartilha paredes. Medir segmentos em comum; nao presumir que o
  quarto Sol tem quatro paredes independentes.
- Contencao/sobreposicao ja existem para mesa na planta. Generalizar para objetos
  adotados e geometria medida, distinguindo limites de caixas envolventes.
- A skill v0.3.1 nao declara mais restricao a duas subpastas de work. Conferir a
  guarda instalada antes de atribuir um bloqueio ao codigo vigente.
- Verificacao barata e somente leitura nao equivale a Play: simulacao, ator de
  teste e alteracao de level sao etapas explicitas, com restauracao e registro.
- Erro de script experimental nao e automaticamente defeito do Director.
- Teste unitario/editor falso prova contrato e calculos, nao geometria nem Unreal.
- #22 so fecha apos novas sessoes reais dos agentes; a sessao atual em acesso
  completo nao comprova o comportamento de sandbox de uma nova sessao.
- Pesquisar primeiro componentes prontos. A biblioteca offline e uma prova
  pequena, sem banco/embeddings/gerenciador proprio decidido antecipadamente.

## Registro inicial

Baseline: 49 testes de nucleo/interface passam. Configuracoes globais nao foram
alteradas. Cada criterio so sera marcado comprovado com sua evidencia; pendencias
ficam explicitas. Nenhum PR foi publicado.

## #22 — configuracao dos agentes

Codex: `.codex/config.toml` usa workspace-write, rede habilitada e approval_policy
never. Rede habilitada NAO significa regra restrita a localhost. Exige confianca
no projeto; politicas gerenciadas e configuracoes do app podem prevalecer. Nao
forcar uma implementacao Windows: a documentacao atual distingue MXC e fallbacks.

Claude: `.claude/settings.json` permite comandos do Director e testes por Bash e
PowerShell. Nao concede acesso total nem instala dependencias. Regras com um
interpretador especifico de venv precisam corresponder ao comando realmente usado.

Para ativar, abrir uma NOVA sessao confiando no projeto. Se houver bloqueio,
registrar comando, cliente/versao e politica efetiva; nao repetir aprovacoes sem
diagnostico. A prova de zero prompts em duas novas sessoes continua pendente.

Fontes oficiais conferidas em 17/10/2026:
- https://learn.chatgpt.com/docs/config-file/config-reference
- https://learn.chatgpt.com/docs/windows/windows-sandbox
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/permissions

## #23 — ensaios

`python -m director ensaio criar nome pedido.txt`

`python -m director ensaio executar ID script.py`

`python -m director ensaio listar ID`

O runner copia os bytes executados para `work/ensaios/ID/execucao-UUID/script.py`,
registra SHA256, resultado/erro, inventarios anterior/posterior e IDs alterados.
Nao e scheduler, nao executa automaticamente, nao aplica rollback silencioso.
O registro local pode conter caminhos privados e permanece ignorado pelo Git.

Validacao: 52 testes de nucleo/interface/ensaios passaram (49 anteriores + 3 novos).
No Unreal, uma leitura registrou 47 atores e a cadeira existente, sem alteracoes;
um RuntimeError provocado foi registrado com hash e inventarios sem mudanca.
O teste unitario adicional provoca erro depois de mutar o editor falso e comprova
que a mudanca parcial fica no registro; nao e prova geometrica do motor.
Nao foi demonstrado ainda o comportamento da guarda de um novo perfil Hermes.

## #26 — resultado medido

`fazer` devolve resultado solicitado/planejado/medido/nao_verificado; `relatorio`
permite consultar depois sem alterar o level. Quatro raios em altura superior aos
moveis precisam confirmar paredes. Ausencia de medida nao vira dimensao planejada.
Medido na referencia Sol: 260 x 350 cm; fixture nova: 400 x 400 cm. Teste negativo
usa paredes medidas com 305 cm contra plano de 320 cm e nao aprova a divergencia;
um raio em movel nao produz medida interna. 54 testes passam com #25 inicial.

## #25 — verificacao por escopo

`verificar` agrega geometria de componentes com colisao (sem billboards),
contencao, raios exteriores, sobreposicoes de colisao nativas, apoio proximo,
varredura, caminho, destino efetivo da projecao, Play e chegada. `aprovado` vale
somente para o escopo informado; nao afirma que foram testadas interacoes como
sentar, deitar ou abrir gavetas. A estabilidade usa duas amostras e limites
explicitados no codigo, nao comprova todas as perturbacoes possiveis.

Reproducao somente leitura da cena de referencia: cama Hermes 24 cm e escrivaninha
15 cm alem da face exterior da parede, ambos confirmados por raio. Sol: cinco
moveis dentro, apoio proximo e sem intersecoes de colisao com profundidade de
envelopes acima de 0,5 cm. O contato com o piso nao foi classificado como penetracao.

Nova cena `auditoria_quarto` preparada da rev14, SHA256 do mapa de origem
752678eba4b8381aee98829eee1a04d46fe0f74ea776148ed7d4e2662f22fb41.
Fixture isolada com mesa sem fisica foi corretamente reprovada pelo Play;
personagem parado a 200 cm foi reprovado, mesmo com estado IDLE. A travessia dessa
porta ainda falhou na navegacao e segue para #10; nao foi mascarada como sucesso.
O erro do controle de CPU de #28 reapareceu no resultado do teste. Foto PNG
recortada foi produzida pelo cliente com Pillow; revisao visual nao executada.

Pendencias da #25: teste positivo completo com moveis gerenciados (#13), percurso
positivo da fixture (#10), variacoes de objetos rotacionados/compostos e baseline
antes/depois no fluxo final. Nao declarar a issue totalmente resolvida ainda.
