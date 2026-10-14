# Director no Hermes: a LLM local como operadora

Aqui ficam as instruções que deixam uma LLM barata (hoje o Qwen local, pelo [Hermes Agent](https://github.com/NousResearch/hermes-agent)) operar o Director. A pessoa descreve a cena em português; a LLM pergunta o que falta, escreve a ficha e chama `python -m director`. Ela **não** mexe no Unreal por outro caminho.

O repositório é a fonte destas instruções. O perfil do Hermes é gerado a partir daqui pelo `instalar_perfil.py`.

| Arquivo | O que é |
|---|---|
| `SOUL.md` | Quem o operador é e as regras dele: português simples, sempre perguntar antes de mexer na cena, pergunta ou crítica não é ordem, sem resposta não faz nada, lacuna se diz em vez de improvisar. |
| `skills/director/SKILL.md` | Como trabalhar: passo a passo, como perguntar (formato da ferramenta `clarify`), a ficha, as direções da sala, exemplos, o que cada resposta do Director quer dizer, o que ele ainda não sabe fazer. |
| `instalar_perfil.py` | Copia os dois arquivos para o perfil, trocando `{{DIRECTOR}}` e `{{PYTHON}}` pelos caminhos da máquina; guarda o arquivo antigo do perfil ao lado, com a data. |
| `config.exemplo.yaml` | O `config.yaml` do perfil, sem segredos. |

## Montar o perfil
1. `hermes profile create director --no-skills`
2. Copie `config.exemplo.yaml` para o `config.yaml` do perfil e troque `<pasta do Director>`. Ponha a chave do servidor do modelo no `.env` do perfil.
3. `hermes -p director tools disable web browser code_execution vision image_gen tts memory session_search connections delegation cronjob computer_use`
4. Na raiz do Director, com o Python que roda o Director: `python hermes/instalar_perfil.py`
5. Abra: `hermes -p director`. O laboratório do Unreal precisa estar aberto pelo programa (`python -m director.lab abrir`).

## O que o primeiro teste mostrou (14/10/2026)
Um teste automático e uma conversa de verdade com o Talis, no aplicativo do Hermes. Não é medição: a medição (o mesmo pedido 10 vezes e umas 10 frases diferentes, contando acertos) ainda não foi feita.

**Funcionou:** o operador leu a skill; montou uma sala nova pedida em uma frase (ficha certa, conferida pelo Director); descreveu a cena certo; foi franco sobre não ver a cena (reconhece as peças pelo nome e pela posição, não pela forma); quando cobrado, testou em vez de afirmar.

**Errou, e o que mudou depois:**
- Preencheu a ferramenta de perguntas no formato errado (opções como objetos; lista escrita como texto), e a pergunta não apareceu → a skill traz o formato exato, com exemplo.
- Ignorou parte do pedido ("do tamanho do quarto", "ter janelas") e disse que a sala não podia ter duas janelas (falso: o Director aceita) → a skill diz o que ele sabe e manda deixar o Director decidir, depois do "sim".
- Depois de uma crítica ("por que ignorou tantas coisas?"), mudou a sala sozinho com um tamanho que ele inventou → `SOUL.md`: pergunta ou crítica não é ordem; nunca chutar medida; e (pedido do Talis) **autorização só existe como "Sim" numa pergunta de sim ou não que traz o resumo do que vai ser feito**: texto solto como "pode fazer" no meio da conversa não autoriza nada.
- Em modo sem tela (`chat -q`), o Hermes manda o modelo "assumir e seguir" quando ninguém responde; o operador seguiu → `SOUL.md`: sem resposta, não faz nada (testado depois: perguntou e não mexeu na cena).

## Problemas conhecidos
- **A primeira tentativa de pergunta costuma sair no formato errado**; a segunda sai certa. No aplicativo aparece um cartão de erro antes da pergunta.
- **No aplicativo do Hermes, a ferramenta de escrever arquivo falhou** ("No shell found"); o operador escreve a ficha pelo terminal (a skill ensina).
- **O Hermes edita a skill sozinho** depois das conversas (revisão automática; registro em `skills/.curator_ledger.jsonl` do perfil). Parte das mudanças é boa, parte é errada. O que for bom é trazido para cá e reinstalado; o que for errado é desfeito ao reinstalar.
- **"Sempre perguntar" ainda é só instrução.** O operador já desobedeceu instrução escrita. Proposta (não feita): um complemento do Hermes que intercepta todo comando que muda a cena e pede a aprovação da pessoa antes, sem que a LLM consiga pular.
- **Lacuna real que apareceu:** corredor (sala estreita ligada a outra por uma passagem). Hoje o Director exige sala de 2 a 20 m de lado e não tem parede em comum entre salas.
