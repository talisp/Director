# Director no Hermes: a LLM local como operadora

Aqui ficam as instruções que deixam uma LLM barata (hoje o Qwen local, pelo [Hermes Agent](https://github.com/NousResearch/hermes-agent)) operar o Director. A pessoa descreve a cena em português; a LLM pergunta o que falta, escreve a ficha e chama `python -m director`. Ela **não** mexe no Unreal por outro caminho.

O repositório é a fonte destas instruções. O perfil do Hermes é gerado a partir daqui pelo `instalar_perfil.py`.

| Arquivo | O que é |
|---|---|
| `SOUL.md` | Quem o operador é e as regras dele: português simples, sempre perguntar antes de mexer na cena, pergunta ou crítica não é ordem, sem resposta não faz nada, lacuna se diz em vez de improvisar. |
| `skills/director/SKILL.md` | Como trabalhar: passo a passo, como perguntar (formato da ferramenta `clarify`), a ficha, as direções da sala, exemplos, o que cada resposta do Director quer dizer, o que ele ainda não sabe fazer. |
| `instalar_perfil.py` | Copia os dois arquivos para o perfil, trocando `{{DIRECTOR}}` e `{{PYTHON}}` pelos caminhos da máquina; guarda o arquivo antigo do perfil ao lado, com a data. |
| `config.exemplo.yaml` | O `config.yaml` do perfil, sem segredos. |
| `plugins/director-guarda/` | Complemento do Hermes que faz as regras valerem por programa, não por obediência do modelo: **cartão de aprovação** antes de qualquer comando que possa mudar o Unreal (mostra em português o que a ficha faz; sem aprovação não roda; leituras do Director passam); escrita de arquivo só em `work/fichas/` e `work/propostas/`; comando que mexa na configuração do Hermes, apague ou mova arquivos também pede o cartão; e conserta as perguntas da ferramenta `clarify` quando o modelo manda a lista como texto. |
| `testes_guarda.py` | Testes do complemento, sem Hermes e sem Unreal: `python -m unittest hermes.testes_guarda`. |

## Montar o perfil
1. `hermes profile create director --no-skills`
2. Copie `config.exemplo.yaml` para o `config.yaml` do perfil e troque `<pasta do Director>`. Ponha a chave do servidor do modelo no `.env` do perfil.
3. `hermes -p director tools disable web browser code_execution vision image_gen tts memory session_search connections delegation cronjob computer_use`
4. Na raiz do Director, com o Python que roda o Director: `python hermes/instalar_perfil.py` (copia também o complemento)
5. Uma vez: `hermes -p director plugins enable director-guarda`
6. Abra: `hermes -p director`. O laboratório do Unreal precisa estar aberto pelo programa (`python -m director.lab abrir`).

## O que o primeiro teste mostrou (14/10/2026)
Um teste automático e uma conversa de verdade com o Talis, no aplicativo do Hermes. Não é medição: a medição (o mesmo pedido 10 vezes e umas 10 frases diferentes, contando acertos) ainda não foi feita.

**Funcionou:** o operador leu a skill; montou uma sala nova pedida em uma frase (ficha certa, conferida pelo Director); descreveu a cena certo; foi franco sobre não ver a cena (reconhece as peças pelo nome e pela posição, não pela forma); quando cobrado, testou em vez de afirmar.

**Errou, e o que mudou depois:**
- Preencheu a ferramenta de perguntas no formato errado (opções como objetos; lista escrita como texto), e a pergunta não apareceu → a skill traz o formato exato, com exemplo.
- Ignorou parte do pedido ("do tamanho do quarto", "ter janelas") e disse que a sala não podia ter duas janelas (falso: o Director aceita) → a skill diz o que ele sabe e manda deixar o Director decidir, depois do "sim".
- Depois de uma crítica ("por que ignorou tantas coisas?"), mudou a sala sozinho com um tamanho que ele inventou → `SOUL.md`: pergunta ou crítica não é ordem; nunca chutar medida; e (pedido do Talis) **autorização só existe como "Sim" numa pergunta de sim ou não que traz o resumo do que vai ser feito**: texto solto como "pode fazer" no meio da conversa não autoriza nada.
- Em modo sem tela (`chat -q`), o Hermes manda o modelo "assumir e seguir" quando ninguém responde; o operador seguiu → `SOUL.md`: sem resposta, não faz nada (testado depois: perguntou e não mexeu na cena).

## Problemas conhecidos
- **A pergunta às vezes sai no formato errado** (a lista escrita como texto; numa conversa, três vezes seguidas, e o formulário nunca chegou). Desde o complemento `director-guarda`, o formato é consertado antes de a ferramenta rodar (conferido dentro do Hermes; ao vivo, o modelo ainda não repetiu o erro).
- **No aplicativo do Hermes, a ferramenta de escrever arquivo falhou** ("No shell found"); o operador escreve a ficha pelo terminal (a skill ensina).
- **O Hermes edita a skill sozinho** depois das conversas (revisão automática; registro em `skills/.curator_ledger.jsonl` do perfil). Parte das mudanças é boa, parte é errada. O que for bom é trazido para cá e reinstalado; o que for errado é desfeito ao reinstalar.
- **"Sempre perguntar" era só instrução** e o operador desobedeceu (mudou a cena depois de uma crítica; montou um rascunho da casa quando o pedido era planejar). Agora é o cartão do complemento `director-guarda`: testado em modo sem tela, o comando que mexe no Unreal não rodou; a escrita no código do Director foi barrada. O cartão no aplicativo ainda não foi visto por uma pessoa.
- **Lacuna real que apareceu:** corredor (sala estreita ligada a outra por uma passagem). O limite de tamanho de cômodo (2 a 20 m) foi removido no mesmo dia, a pedido do Talis; falta a parede em comum com passagem entre dois cômodos.
