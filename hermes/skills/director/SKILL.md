---
name: director
description: "Como montar e mudar a cena no laboratório do Unreal pelo programa Director (fichas JSON). Ler antes de qualquer pedido sobre a sala, as paredes, a porta, a janela, a mesa, o prato ou o copo."
version: 0.2.0
author: Talis / Claude Code
license: MIT
platforms: [windows]
---

# Director: do pedido à cena

Você não mexe no Unreal. Você escreve uma **ficha** (um JSON pequeno com a lista de operações) e o Director faz o resto: abre a cena, aplica, confere, salva, e desfaz sozinho se algo der errado. Tudo acontece no **projeto de laboratório** (não é o projeto do filme).

O terminal é Bash. Todos os comandos começam assim (chamado de `DIRECTOR` abaixo):

```
cd "{{DIRECTOR}}" && "{{PYTHON}}" -m director
```

## Passo a passo de cada pedido

1. **O laboratório está aberto?** (uma vez por conversa)
   `cd "{{DIRECTOR}}" && "{{PYTHON}}" -m director.lab estado`
   Se `"responde": true`, siga. Se não, abra com o mesmo comando trocando `estado` por `abrir` (leva uns 30 s; pode levar minutos) e confira de novo.
2. **O que o Director sabe fazer:** `DIRECTOR capacidades` (uma vez por conversa). É a lista oficial de operações, campos e valores padrão. Não invente campo que não está lá.
3. **O que já está na cena:** `DIRECTOR estado sala`. Mostra os nomes das peças (`sala1`, `porta1`, `mesa1`…) e as `diferencas` entre a planta e o Unreal (vazio = tudo certo). Para ver medidas e posições, leia (só leia) `{{DIRECTOR}}/director/cenas/sala/planta.json`. **Atenção: a planta está em centímetros; a ficha é em metros.**
4. **Pergunte antes de fazer** (sempre): conte ao Talis, em palavras simples, o que vai mudar na cena e pergunte se pode, com a ferramenta `clarify` (ver "Como perguntar ao Talis"). Se faltar informação, pergunte isso também, na mesma chamada. Só siga depois do "sim".
5. **Escreva a ficha** num arquivo novo em `{{DIRECTOR}}/work/fichas/`, com nome que diga o que é (ex.: `copo_e_sala_5m.json`). Se a ferramenta de escrever arquivo der erro, escreva pelo terminal:
   ```
   cd "{{DIRECTOR}}" && cat > work/fichas/copo_e_sala_5m.json <<'FIM'
   {"pedido": "...", "operacoes": [ ... ]}
   FIM
   ```
6. **Mande:** `DIRECTOR fazer sala work/fichas/copo_e_sala_5m.json`
7. **Leia a resposta e conte ao Talis** em palavras simples (ver "Respostas" abaixo).

A cena padrão é `sala`. Use outro nome de cena só se o Talis pedir uma cena nova (nome curto, minúsculas, sem espaço); uma cena nova começa vazia.

## Como perguntar ao Talis (ferramenta `clarify`)

O argumento `questions` é uma **lista de verdade** (colchetes direto no JSON), **nunca um texto entre aspas** com a lista dentro. Errado: `{"questions": "[{\"question\": ...}]"}`. Certo: `{"questions": [{"question": ...}]}`. Cada pergunta é um objeto com `question` (texto) e, se quiser opções, `choices`: uma **lista de textos simples** (no máximo 4). **Nada de objeto dentro de `choices`** (sem `label`, sem `description`) e **nada de lista escrita como texto**. Exemplo exato, para copiar o formato:

```json
{"questions": [
  {"question": "Vou deixar a porta da sala aberta, como se ela ficasse sempre aberta. Nada mais muda. Posso fazer?",
   "choices": ["Sim, pode fazer", "Sim, mas com uma mudança (eu escrevo qual)", "Não, deixe como está"]}
]}
```

Duas perguntas na mesma vez (quando uma resposta não muda a outra):

```json
{"questions": [
  {"question": "Que tamanho você quer para a sala, em metros (largura × comprimento)?",
   "choices": ["3 × 4 metros", "4 × 4 metros", "4 × 5 metros"]},
  {"question": "Onde fica a janela? Imagine que você está na porta, olhando para dentro da sala.",
   "choices": ["Na parede da frente", "Na parede da direita", "Na parede da esquerda"]}
]}
```

- Tudo em português simples, como para quem nunca usou o Unreal. Explicação vai no texto da pergunta, não nas opções.
- **Sempre ofereça opções: 3 (no máximo 4)**, cada uma curta e diferente das outras. A primeira é a que você recomenda. Não escreva "(Recomendado)": a tela marca sozinha. A tela também acrescenta sozinha, no fim, uma linha para o Talis escrever a resposta dele se não gostar de nenhuma: não crie essa opção você mesmo.
- Mesmo para pedir um número (tamanho, distância), dê 3 sugestões razoáveis como opções (ex.: "3 × 4 metros", "4 × 4 metros", "4 × 5 metros"); se ele quiser outro, escreve na linha livre.
- Para a licença antes de mexer, as opções são, por exemplo: "Sim, pode fazer", "Sim, mas com uma mudança (eu escrevo qual)", "Não, deixe como está".
- A resposta volta em `responses[0].user_response`. Se vier `"outcome"` diferente de `submitted`, ou erro, ou "not available", ele **não** respondeu: escreva a pergunta como texto normal e termine a sua vez. Nunca use o valor padrão no lugar da resposta dele.

## A ficha

```json
{
 "pedido": "a frase do Talis, copiada",
 "operacoes": [
  {"operacao": "...", "...": "..."}
 ]
}
```

- As operações rodam em ordem. **Ou entram todas, ou nenhuma.**
- Cinco operações: `criar_sala`, `mudar_sala`, `colocar`, `mudar`, `remover`. Os campos de cada uma estão em `capacidades`.
- Peças que dá para colocar: `porta`, `janela` (numa parede), `mesa` (no chão), `prato`, `copo` (sobre uma mesa).
- Medidas em **metros**, ângulos em **graus**.
- Campo que o Talis não disse fica de fora: o Director usa o padrão.
- **Nunca invente valor e vista como ideia do Talis.** Medida, parede, nome ou ângulo que não saíram da fala dele (nem do `estado`/planta) não entram na ficha: pergunte antes com `clarify`. "Do tamanho do X" com X inexistente = número inexistente; a resposta é pergunta, não chute. Ao narrar o que fez, "escolhi ..." e não "entendi que ..." — chute se assume, não se disfarça de interpretação. Encrenca real (rev. 9–11): inventei "quarto = 3×3", encolhi a sala e descrevi o chute como algo natural do pedido. Tamanho de cômodo só mexe com valor explícito ou confirmado. E sempre cite ao Talis o número que vai usar *antes* de mandar a ficha, para dar tempo de um "não".
- Limites da sala comprovados por teste: menor sala aceita é 2 × 2 m (2 a 20 m; altura 2,2 a 5 m). Corredor estreito e cômodos ligados por vão continuam impossíveis.
- Nomes: se você não der `id`, o Director dá (`porta1`, `mesa2`…). Para mudar ou remover, use o nome que aparece no `estado`.

### Direções da sala
- Paredes: `sul`, `norte`, `leste`, `oeste`. Em `mudar`, a porta ou a janela também aceita `"parede": "oposta"`.
- O canto **sudoeste** é a origem. `largura_m` é leste-oeste; `comprimento_m` é sul-norte.
- Posição da mesa (`x_m`, `y_m`): a partir do canto sudoeste, para leste (`x`) e para norte (`y`).
- Posição de porta e janela (`posicao_m`): centro do vão ao longo da parede, a partir do canto oeste (paredes sul e norte) ou do canto sul (paredes leste e oeste).
- `mudar_sala` mantém o canto sudoeste parado; móveis, porta e janela **não saem do lugar** (a sala cresce para leste e para norte).

### Exemplos

"Crie uma sala de 4 × 4 metros, com porta, janela e uma mesa."
```json
{"pedido": "Crie uma sala de 4 × 4 metros, com porta, janela e uma mesa.",
 "operacoes": [
  {"operacao": "criar_sala", "largura_m": 4, "comprimento_m": 4},
  {"operacao": "colocar", "tipo": "porta"},
  {"operacao": "colocar", "tipo": "janela"},
  {"operacao": "colocar", "tipo": "mesa"}]}
```

"Aumente a sala para 5 × 4 metros e mude a porta para a parede oposta."
```json
{"pedido": "Aumente a sala para 5 × 4 metros e mude a porta para a parede oposta.",
 "operacoes": [
  {"operacao": "mudar_sala", "largura_m": 5, "comprimento_m": 4},
  {"operacao": "mudar", "id": "porta1", "parede": "oposta"}]}
```

"Coloque um prato e um copo sobre a mesa."
```json
{"pedido": "Coloque um prato e um copo sobre a mesa.",
 "operacoes": [
  {"operacao": "colocar", "tipo": "prato"},
  {"operacao": "colocar", "tipo": "copo"}]}
```

"Abra a porta e tire o prato."
```json
{"pedido": "Abra a porta e tire o prato.",
 "operacoes": [
  {"operacao": "mudar", "id": "porta1", "angulo": 90},
  {"operacao": "remover", "id": "prato1"}]}
```

## Respostas do Director
- `"ok": true`: deu certo e foi salvo. Conte ao Talis o que mudou (veja `acoes` e `resumo`). `atores_mantidos` são as peças que ficaram intactas.
- `"motivo": "recusado"`: nada foi feito (`"tocou_na_cena": false`). O `porque` diz a razão. Se for erro seu na ficha (campo errado, nome que não existe), corrija **uma vez** e mande de novo. Se for limite do Director, conte ao Talis.
- Outro `motivo` (`"recuperado": true`): o Director tentou, algo falhou e ele voltou a cena ao que era. Conte ao Talis o motivo; **não** tente de novo sozinho.
- "o editor está em Play": peça ao Talis para parar o Play.
- Erro de trava ou "ocupado": outro programa está usando o laboratório. Espere um minuto e tente uma vez; se continuar, avise o Talis.

## Quando o Talis mexe à mão
- Se ele moveu peças no editor (fora do Play), o Director percebe e **adota** a mudança no próximo `fazer` (aparece em `adotados`).
- Se ele mexeu durante o Play e quer guardar onde os objetos ficaram: com o Play ainda rodando, `DIRECTOR incorporar sala` (ou `DIRECTOR incorporar sala copo1 prato1` para só alguns).

## O que o Director ainda não sabe fazer
Personagem, corpo, animação, câmera, sequência, vídeo, foto, aparência (as peças são blocos cinza), outros móveis e objetos; **ligar um cômodo a outro** (parede em comum com passagem); cômodo com menos de 2 m de lado (um corredor de 1 m é recusado por isso). Pedido assim: responda "o Director ainda não sabe fazer: …" e ofereça os três caminhos do `SOUL.md` (usar o que existe, adaptar, investigar numa cópia). Não altere a cena do Talis enquanto isso.

**Cômodo é cômodo:** sala, quarto, cozinha, banheiro, corredor, garagem são todos `criar_sala` (o `id` é o nome que você quiser, ex.: `"id": "banheiro"`). Dois cômodos lado a lado na mesma cena são aceitos (testado sem o Unreal; no Unreal ainda não); o que falta é a passagem entre eles.

O que ele **sabe**, e o Qwen já negou por engano: mais de uma janela ou porta na mesma sala (em paredes diferentes; na mesma parede só se os vãos não encostarem um no outro nem no canto — senão ele recusa sozinho). Na dúvida, mande a ficha depois do "sim" do Talis e deixe o Director decidir: se ele não puder, recusa sem mexer na cena.

### Pedido misto (parte dá, parte não)
Quando o pedido junta coisas que o Director sabe e coisas que ele não sabe: explique ao Talis, em palavras simples, o que dá e o que não dá, **proponha** fazer a parte que dá e pergunte se pode (`clarify`). Exemplo real: "porta sempre aberta + corredor com 3 portas" → "O corredor eu ainda não sei fazer. Posso deixar a porta da sala aberta?". "Porta sempre aberta" = `mudar` com `angulo: 90`.
- Se o Talis usar uma medida que o Director não conhece ("do tamanho do quarto"), pergunte quantos metros.

### "O que você vê na cena?"
Não há câmera: você nunca vê a cena, só o registro. Os objetos são reconhecidos por **nome + posição + caixa** (`estado`, `planta.json`), nunca pela forma ou textura — as peças todas são blocos cinza. Diga isso com franqueza quando o Talis perguntar como você sabe que "o prato é prato": a conferência do Director garante que o registrado bate com o Unreal; quem julga a aparência é o Talis, de olho no editor. Se ele descrever algo diferente da planta, pode ser mudança feita à mão (o Director adota no próximo `fazer`).
