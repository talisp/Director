# Observação e leitura pelo GLM — 19/10/2026

## Entrega

`observar CENA --texto SALA --real` consulta o editor, concilia em memória e desenha os
móveis observados. Não grava a planta nem muda de level. Móvel ausente não aparece como
observado. Paredes/salas continuam referência planejada; inclinação, colisão e atores
externos exigem outras consultas. O modo sem `--real` continua offline.

`relacoes_compartilhadas` agora nomeia sala/lado/vizinho/lado do vizinho, evitando exigir
que o operador associe corretamente dois arrays paralelos. Dimensões internas nomeiam
seus eixos. Não se inventou semântica externa a partir de uma bounding box.

## Protocolo e evidência

Cena própria `obs_glm_20261019`: proxies geométricos reconstruídos de snapshot histórico
de 18/10; não são os assets originais nem o quarto original de 17/10. Quarto 271×366 cm,
sete móveis/objetos, porta oeste. Cama deslocada manualmente: 24 cm além do limite interno
leste, 9 cm além da parede externa. Inventário, consulta nativa e CLI candidata concordam.
Vizinhos não foram reconstruídos; compartilhamento é metadado histórico.

Cinco perguntas previamente fixadas: parede da porta; apoio junto à cabeceira; móvel fora
do limite leste; largura interna; parede externa candidata, sem inventar altura de janela.
Nos três casos principais, os números são iguais: JSON; JSON+grade; JSON+foto nativa.
Fotografia ortográfica tem leste à esquerda; grade tem leste à direita, declarado na entrada.

| Entrada / esforço | Tempo observado | Resposta principal |
|---|---:|---|
| JSON / high | 52,986 s do agente; 55,765 s total | 5/5; explicação da parede candidata confusa |
| JSON+grade / high | 51,384 s do agente; 54,016 s total | 5/5; ressalvas melhores sobre móveis ao norte |
| JSON+foto / high | 47,375 s RPC total | 5/5 |
| Foto+legenda reduzida / high | 75,671 s RPC total | 5/5; identificou cama visualmente, sem inventar os 24 cm removidos |
| JSON / low | 10,800 s do agente | 5/5 principais, mas acrescentou alegação frágil de ausência de móveis encostados ao norte |
| JSON+grade / low | 45,212 s do agente | 4/5; confundiu os lados de cômodos diferentes na pergunta da parede externa |

Uma execução por condição, em ordem fixa, caches diferentes, transportes CLI/RPC diferentes.
O caso de legenda reduzida é exploratório: não é equivalente em informação aos três primeiros.
Não há demonstração de ganho geral da imagem, nem de que reduzir esforço sempre preserve
qualidade. O erro com arrays paralelos motivou campos explícitos; não apagar a falha do relatório.

Verificação posterior com os novos campos explícitos, mesma grade e esforço low: 41,189 s,
5/5 respostas principais, distinguindo oeste/corredor e sul/sala1. Isso confirma que o modelo
conseguiu usar a interface corrigida naquele caso; não é comparação estatística nem prova de
que ambiguidade era a única causa. Sessão `local-e87a2fab5148c8efe4ebb02dea6c259408d43e887913f79624fdeef96368ee3f`.

CLI anuncia `--image`, mas sua implementação de gateway recusou anexação antes da inferência.
A anexação funcionou pela API nativa autenticada usada pelo TUI/desktop; isso não é teste da
interface gráfica. Uma falha inicial de arquivo ausente foi do nosso executor de testes, não do GLM.

## Visão local

`/v1/models` do endpoint atual anunciou texto+imagem para `glm-5.3-flash`. Teste direto
de quatro cores respondeu corretamente em 3,765 s. A seleção de imagens do Hermes tratava
o provedor customizado como texto. Foi declarado `supports_vision: true` apenas em
`providers.glm-maya.models.glm-5.3-flash`, após verificar capacidade. Modelo, porta, contexto
e esforço global high preservados. Imagens reais foram processadas pelo perfil Director.
Não se habilitou outro provedor pago.

## Verificação e limites

150 testes Director aprovados, incluindo leitura sem mutação, level incorreto, móvel ausente
e associação explícita dos lados. Cena original `L_sala` restaurada: inventário e navegação
idênticos, sem Play nem pacotes por salvar. Não se afirma restauração de posição da interface.
Logs brutos locais ficam em `work/observacao-20261019`; não contêm prova de física dinâmica
nem representam validação estética de uma cozinha. A revisão de qualidade continua necessária.

Recomendação: dados estruturados explícitos como base; grade e foto sob demanda. Testar
esforço menor em consultas simples antes de considerar qualquer mudança global. Não há
comparação pareada com Qwen que permita decidir a troca por uma perda de velocidade de 70%.
