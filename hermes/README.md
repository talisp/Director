# Director no Hermes: a LLM local como operadora

Aqui ficam as instruções do perfil experimental `director` no Hermes. A pessoa descreve a cena em português; a LLM consulta o estado, usa as capacidades existentes e pode investigar outras operações no laboratório quando a ficha atual não atender ao pedido.

O repositório é a fonte destas instruções. O perfil do Hermes é gerado a partir daqui pelo `instalar_perfil.py`.

| Arquivo | O que é |
|---|---|
| `SOUL.md` | Orientação do operador: autonomia no laboratório, perguntas somente quando necessárias, observação e correção do resultado. |
| `skills/director/SKILL.md` | Como trabalhar: passo a passo, como perguntar (formato da ferramenta `clarify`), a ficha, as direções da sala, exemplos, o que cada resposta do Director quer dizer, o que ele ainda não sabe fazer. |
| `instalar_perfil.py` | Copia os dois arquivos para o perfil, trocando `{{DIRECTOR}}` e `{{PYTHON}}` pelos caminhos da máquina; guarda o arquivo antigo do perfil ao lado, com a data. |
| `config.exemplo.yaml` | O `config.yaml` do perfil, sem segredos. |
| `plugins/director-guarda/` | Corrige argumentos de `clarify`, limita esperas e barra alterações concorrentes da mesma cena reconhecidas pela guarda. Não cria cartões de aprovação. Ver [verificação e limites](../docs/esperas-hermes.md). |
| `testes_guarda.py` | Testes do complemento, sem Hermes e sem Unreal: `python -m unittest hermes.testes_guarda`. |

## Montar o perfil

### Conferir antes de reinstalar

`python hermes/instalar_perfil.py director --conferir` compara SOUL e skill com os templates
preenchidos e mostra diff e hashes, sem escrever no perfil. Execute com o mesmo Python usado
na instalacao. Codigo 1 indica diferenca, nao falha de ferramenta: revise notas com sua
procedencia antes de reinstalar. A comparacao nao classifica automaticamente a nota como correta.

1. `hermes profile create director --no-skills`
2. Copie `config.exemplo.yaml` para o `config.yaml` do perfil e troque `<pasta do Director>`. Ponha a chave do servidor do modelo no `.env` do perfil.
3. Use os toolsets e `approvals.mode: "off"` do `config.exemplo.yaml`. O TTS aponta para o serviço local Kokoro na porta 8880; esse serviço precisa estar em execução para gerar áudio.
4. Use uma instalacao dedicada do codigo publicado, separada do desenvolvimento (ver [operador-publicado](../docs/operador-publicado.md)). Na raiz dessa instalacao, com o Python que roda o Director: `python hermes/instalar_perfil.py` (copia também o complemento). O cwd do perfil deve apontar para essa pasta. Conversas existentes podem conservar outro cwd: mova-as pelo mecanismo nativo de workspace e confira.
5. Uma vez: `hermes -p director plugins enable director-guarda`
6. Abra: `hermes -p director`. O laboratório pode ser aberto por `python -m director.lab abrir` quando necessário.

## Histórico do primeiro teste (14/10/2026; regras antigas, não vigentes)
Um teste automático e uma conversa de verdade com o Talis, no aplicativo do Hermes. Não é medição: a medição (o mesmo pedido 10 vezes e umas 10 frases diferentes, contando acertos) ainda não foi feita.

**Funcionou:** o operador leu a skill; montou uma sala nova pedida em uma frase (ficha certa, conferida pelo Director); descreveu a cena certo; foi franco sobre não ver a cena (reconhece as peças pelo nome e pela posição, não pela forma); quando cobrado, testou em vez de afirmar.

**Errou, e o que mudou depois:**
- Preencheu a ferramenta de perguntas no formato errado (opções como objetos; lista escrita como texto), e a pergunta não apareceu → a skill traz o formato exato, com exemplo.
- Ignorou parte do pedido ("do tamanho do quarto", "ter janelas") e disse que a sala não podia ter duas janelas (falso: o Director aceita) → a skill diz o que ele sabe e manda deixar o Director decidir, depois do "sim".
- Depois de uma crítica ("por que ignorou tantas coisas?"), mudou a sala sozinho com um tamanho que ele inventou → `SOUL.md`: pergunta ou crítica não é ordem; nunca chutar medida; e (pedido do Talis) **autorização só existe como "Sim" numa pergunta de sim ou não que traz o resumo do que vai ser feito**: texto solto como "pode fazer" no meio da conversa não autoriza nada.
- Em modo sem tela (`chat -q`), o Hermes manda o modelo "assumir e seguir" quando ninguém responde; o operador seguiu → `SOUL.md`: sem resposta, não faz nada (testado depois: perguntou e não mexeu na cena).

## Problemas conhecidos

As observações de 14/10 acima são históricas; a regra vigente está em SOUL/skill.
Uma ordem de execução autoriza suas operações necessárias, sem exigir a palavra “Sim”
ou cartão por comando. Discussão e crítica não autorizam alteração por si sós.

- **A pergunta às vezes sai no formato errado** (a lista escrita como texto; numa conversa, três vezes seguidas, e o formulário nunca chegou). Desde o complemento `director-guarda`, o formato é consertado antes de a ferramenta rodar. A primeira versão do conserto só lia a lista certinha e falhou no aplicativo: o modelo deixa um `}` sobrando no fim, ou esquece o `]` final. Corrigido; as 15 perguntas gravadas nas conversas passam pela validação do Hermes.
- **No aplicativo do Hermes, a ferramenta de escrever arquivo falhou** ("No shell found"); o operador escreve a ficha pelo terminal (a skill ensina).
- **O Hermes edita a skill sozinho** depois das conversas (revisão automática; registro em `skills/.curator_ledger.jsonl` do perfil). Parte das mudanças é boa, parte é errada. O que for bom é trazido para cá e reinstalado; o que for errado é desfeito ao reinstalar.
- **Política antiga de aprovação:** após alterações não solicitadas, foi introduzido um cartão por comando. Essa política foi substituída em 16/10, a pedido do Talis: o perfil experimental executa tarefas autorizadas sem esses cartões. Uma discussão continua não sendo uma ordem de alterar a cena.
- **Corredores e passagens:** o contrato aceita cômodos estreitos e paredes compartilhadas. Nos testes de 17/10, uma montagem leste–oeste teve passagem física e trajeto completo após reconstrução nativa da navegação; outra montagem norte–sul continuou com caminho parcial. A navegação ainda requer investigação, mesmo quando a geometria passa nas verificações.
# Pesquisa de engenharia

`skills/director-research` contem a fonte versionada 0.3.1 da skill de pesquisa,
com vinculo ao gargalo, ficha de operador, evidencias e limite por lote.
`python hermes/instalar_pesquisa.py hermes-dev` compara a instalacao;
`--aplicar` faz backup e atualiza somente se o perfil estiver ocioso e sem conflitos.
Fila/estudos e skill de operacao do perfil Director sao preservados.
Provas e limites da entrega: [pilotos e auditoria de issues](../docs/conclusao-pilotos-2026-10-21.md).
Antes de novos ensaios Luna, resolver a divergencia de rota registrada na issue #81.

