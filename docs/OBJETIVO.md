# Objetivo e critérios de trabalho do Director

## Produto desejado

Uma pessoa descreve, constrói e dirige mundos tridimensionais conversando com uma LLM,
sem precisar conhecer programação ou Unreal. Pode fazer pedidos sucessivos, apontar um
problema e pedir uma correção local, preservando o que já funciona.

As cenas e animações servirão de referência para ferramentas de geração de vídeo por IA,
especialmente para continuidade espacial e temporal. Formas simples e materiais básicos
podem bastar; posições, acessos, contatos e ordem das ações precisam fazer sentido.
A exportação dos vídeos é manual no Unreal e não é responsabilidade do Director.

## Prioridade atual

Construir e modificar cenários: cômodos, conexões, portas, móveis e relações espaciais.
Um avanço deve aumentar a variedade de **pedidos atendidos**, sem exigir uma macro
específica para cada casa, corredor ou outro nome usado pelo usuário.

O agente pode pedir esclarecimentos quando uma escolha essencial estiver indefinida.
Deve distinguir informação dada, inferida e ainda desconhecida; registrar uma hipótese
não a transforma em decisão do usuário. Composição procedural precisa respeitar o pedido
e a cena existente, em vez de distribuir objetos sem coerência funcional.

## Divisão de trabalho

- **LLM:** interpretar, perguntar, planejar, escolher ferramentas, investigar alternativas,
  interpretar os resultados e decidir a próxima tentativa dentro da autorização recebida.
- **Código determinístico:** cálculos repetíveis, restrições, representação persistente,
  validação, conciliação, identidade e preparação de alterações.
- **Unreal:** construção por suas APIs/Blueprints e sistemas de motor, física, colisões,
  navegação e, futuramente, animação. Pesquisar e reutilizar capacidade existente antes
  de construir uma substituição própria.
- **Usuário:** intenção criativa, escolhas relevantes e autorização de desenvolvimento.
  Uma tarefa autorizada não deve gerar confirmação a cada ferramenta.

O contrato atual é uma ferramenta de execução, não uma arquitetura definitiva nem o
limite do raciocínio do agente. A LLM pode desenvolver pequenos programas experimentais
no laboratório para resolver uma lacuna. Experimento, resultado e aprendizagem têm
procedência; promover uma descoberta a solução permanente não é automático.

## Ciclo que deve orientar a evolução

Pedido → consulta da cena → plano → execução → observação → comparação → correção.

Antes de compor um objeto, procurar opção pronta adequada na cena, no projeto e na
biblioteca. Um objeto pode ser composto quando necessário, mas deve ter identidade,
dimensões, colisão e física coerentes com a interação pretendida. Existir visualmente
não comprova que alguém consegue usar, atravessar, alcançar ou apoiar algo nele.

Priorizar observação estruturada: geometria, relações espaciais e significado funcional.
Uma dessas camadas não substitui as outras. Usar visão quando acrescentar informação.
Não declarar atendimento a partir de `ok:true`, de um desenho do plano ou apenas da
ausência de colisão. Corrigir localmente, limitar tentativas e relatar o que faltou.

## Critério de resultado: Pedidos Atendidos

Definir antes do teste os critérios verificáveis do pedido. Classificar:

- **ATENDIDO:** resultado principal produzido corretamente.
- **PARCIAL:** parte relevante produzida, com objetivo principal incompleto.
- **NÃO ATENDIDO:** ação principal ausente ou resultado incorreto.

Registrar causa da falha, tentativas, intervenção humana, objetos preservados, diferença
entre plano e execução e tipo de evidência. Testes unitários verificam componentes;
não substituem essa avaliação. Qualidade funcional também não se reduz a medidas geométricas.

## Limites desta etapa

Preservar laboratório separado, trava, identidades, conciliação, validação, recuperação
e registros de experimentos. Dar liberdade de investigação no laboratório sem tratar
o projeto cinematográfico como área de teste. Separar instalação publicada de desenvolvimento.

Animação corporal, IK, sequenciamento e câmera devem orientar compatibilidade futura,
sem ocupar o primeiro ciclo de construção de cenários. Não iniciar uma reconstrução
geral, banco, scheduler, plataforma de agentes ou integração de acervo inteiro por preferência:
é preciso demonstrar a lacuna e confrontar soluções existentes.

O próximo trabalho segue o [pipeline autorizado](pipeline-2026-10-18.md). Este documento
registra a meta; não declara que essas capacidades já estejam implementadas ou validadas.
