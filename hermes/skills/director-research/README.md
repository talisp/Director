# Atualização dirigida 0.3.1

Fonte versionada em `talisp/Director`, mantendo a fila externa e os estudos existentes.
Adiciona vínculo por gargalo, ficha curta validada, orçamento e prova de variação; não integra código automaticamente.
Novos arquivos: `references/GARGALOS.md`, `templates/FICHA_OPERADOR.json`, `scripts/verificar_ficha.py`.
Testes existentes continuam obrigatórios; `scripts/teste_ficha.py` cobre o novo contrato e o finish.

# Director Research — Skill para Hermes/Qwen (0.2.0)

## O que mudou na 0.2.0 (16/10/2026, Claude Code, a pedido do Talis)

Feita a partir da auditoria do Codex e da lista do ChatGPT sobre a primeira pesquisa (CityGenerator, sessão de 16/10), e do que o Claude Code achou na mesma sessão.
- **Segue a fila:** o `finish` diz o proximo; inicia-lo depende de ainda caber no lote autorizado; `next` retoma `PARCIAL` antes dos pendentes (a 0.1 o esquecia, e o teste aceitava). Para várias rodadas seguidas, use `/goal` no Hermes.
- **Foco por link:** `fila.py add URL --foco "texto"`; a avaliação tem de responder ao foco.
- **Painel para o Talis:** `PAINEL.md`, com o que copiar, o que inspira e o que dá para usar, de cada projeto.
- **Checkpoints** com feito / falta / arquivos; versão e hashes da skill gravados em cada pesquisa; `git status` do Director e do `unreal-macros` medido no começo e no fim.
- **Notas honestas:** 10, 11 e 13 positivas só com o caminho real; 16 só com medição própria; `ALEGADO` só com `?`; revisão de 5 notas; placar PASS / FAIL / OBSERVAÇÃO / NÃO TESTADO e "esperava X, deu Y".
- **Contexto medido:** `scripts/medir_contexto.py` (erros de ferramenta por faixa de contexto).
- **Unreal liberado** quando o teste precisar, pelo laboratório do Director.
- A skill não deve ser reescrita pela revisão de fundo do Hermes; sugestões vão para `estudos/sugestoes-skill.md`.

**Onde fica instalada nesta máquina:** `%LOCALAPPDATA%\hermes\profiles\hermes-dev\skills\director-research\` (não em `.hermes\skills
esearch`). Não deixe outra cópia com o mesmo nome em outra pasta de skills: o Hermes tira o comando `/director-research` quando acha duas. Skill nova ou renomeada só vira comando depois de reiniciar o gateway (`hermes gateway restart`).

---


**Não é instalação do Director e não altera o projeto Unreal.** É uma Skill que ensina o Hermes a investigar projetos do GitHub e conservar relatórios e avaliações numa pasta separada.

## Instalação em Windows 11 (Hermes)

1. Feche/reinicie a sessão de Hermes após instalar a Skill.
2. Extraia o ZIP para que o seguinte arquivo exista (com a mesma subpasta `director-research`):

   `%USERPROFILE%\.hermes\skills\research\director-research\SKILL.md`

   No PowerShell, se o ZIP estiver na pasta Downloads:

   ```powershell
   $dest = Join-Path $env:USERPROFILE '.hermes\skills\research'
   New-Item -ItemType Directory -Path $dest -Force | Out-Null
   Expand-Archive -LiteralPath (Join-Path $env:USERPROFILE 'Downloads\director-research-skill.zip') -DestinationPath $dest -Force
   ```

3. Use `hermes skills list` no CLI ou `/skills` no chat para confirmar. No Hermes, uma Skill local instalada vira comando `/director-research`. Fonte: https://hermes-agent.nousresearch.com/docs/guides/work-with-skills/
4. **Inicie uma nova sessão** após a instalação para atualizar o catálogo. Evite o perfil antigo `director` se impedir gravação em `~/pesquisas-director/estudos`; use uma sessão/perfil de pesquisa com acesso **somente leitura ao Director** e escrita apenas na pasta de pesquisa. Não afrouxe o `director-guarda` para testar esta Skill.

## Primeiro teste (um projeto)

```text
/director-research Pesquise https://github.com/AlexKorotkin-creator/CityGenerator . Acesse o Director apenas para leitura e salve os resultados em pesquisas-director/estudos.
```

O CityGenerator é um alvo sugerido porque gera áreas urbanas e permite exercitar o critério de **planejamento territorial antes dos prédios**. Outro repo de sua escolha serve igualmente.

Durante a pesquisa, experimente:

```text
/steer Adicione https://github.com/evanpetersen919/VantageCV-Remastered à fila.md via o script desta Skill; não interrompa a pesquisa atual. Continue a atual e processe esse projeto em seguida.
```

**O link só está realmente em fila após a chamada de script e a conferência em `fila.md`.** O Hermes documenta que `/steer` entra durante a execução, após o próximo resultado de ferramenta; `/queue` agenda outro turno. Isso não cria um worker persistente que execute após encerrar sessões. Fonte: https://hermes-agent.nousresearch.com/docs/user-guide/cli/

Depois:

```text
/director-research continuar
/director-research mostre a fila e as cinco descobertas mais promissoras
```

## O que será gerado

- `~/pesquisas-director/estudos/fila.json`: fila persistente, operada pelo script.
- `~/pesquisas-director/estudos/fila.md`: espelho visível da fila, atualizado automaticamente.
- `~/pesquisas-director/estudos/repositorios/<owner--repo>/AVALIACAO.md`: **cartão amigável** com 17 notas, descoberta-chave e síntese curta.
- `analise.md`, `evidencias.md`, `experimentos.md`, `estado.md`: prova técnica e checkpoints.
- `conhecimentos/`: fichas de técnicas transversais para comparar dezenas de projetos.
- `indice.md`, `sintese-geral.md`, `comparativo.md`: visão agregada.

Leia `references/RUBRICA.md` para âncoras dos 17 critérios, `references/PROTOCOLO.md` para pipeline e `references/ARQUIVOS.md` para formatos.

## Testes locais do pacote, sem tocar no Director

```powershell
python "$env:USERPROFILE\.hermes\skills\research\director-research\scripts\teste_skill.py"
```

O script testa fila, idempotência, transições e validação de avaliação em uma pasta temporária. Não acessa GitHub, Unreal ou Director.

## Limites honestos

- A Skill não cria agendamento externo, não mantém inferência por horas após o Hermes encerrar o turno nem contorna `max_turns` ou aprovação de ações. Ela escreve checkpoints para retomar depois.
- O parser de fila aceita links de repositório GitHub (`owner/repo`). Outros provedores podem ser adicionados em versão futura.
- A verificação automática da avaliação confirma **formato, não a veracidade das notas**. O Qwen precisa pesquisar e provar.
- Instalação pode precisar de adaptação se seu Hermes usa `HERMES_HOME`/diretório externo; veja a documentação da versão instalada em caso de divergência.
