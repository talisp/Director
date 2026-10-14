# Director, primeira entrega: criar e modificar um cenário funcional (13/10/2026)

Critérios de aceite escritos antes de rodar. O que se aprendeu e como retomar: [CONHECIMENTO.md](../CONHECIMENTO.md).

- **Onde rodou:** Unreal 5.8.3, projeto de laboratório (porta 8011), cena `sala`. O editor do projeto do filme ficou aberto e sem chamadas.
- **Código:** o deste repositório, antes de o pacote ser renomeado de `director2` para `director` (ver a rodada 4, abaixo). Comando: `python -m director.demonstracao tudo sala`.
- **Resultado:** **64 de 64 itens** na passada final (20:10 a 20:11). Medidas brutas em [medidas/](medidas/).

## Os três comandos (cada um é uma ficha em `director/fichas/`, aplicada pelo programa)
| Comando | O que o programa fez no Unreal | Medido |
|---|---|---|
| 1. "Crie uma sala de 4 × 4 metros, com porta, janela e uma mesa." | criou 9 peças: piso, 4 paredes, volume de navegação, porta, janela, mesa | medida interna 400,0 × 400,0 cm (raios); chão em z = 1,0 cm; as 4 paredes barram; a janela está no vão e a parede abaixo do peitoril |
| 2. "Aumente a sala para 5 × 4 metros e mude a porta para a parede oposta." | atualizou 7 peças; **nenhuma criada nem apagada** | 500,0 × 400,0 cm; porta na parede norte, abrindo para dentro; vão antigo virou parede cheia; **os mesmos 9 atores** |
| 3. "Coloque um prato e um copo sobre a mesa." | criou 2 peças (prato e copo); as outras 9 ficaram idênticas | prato e copo pousados no tampo (topo da mesa a 76 cm) |

## Critérios, com o caso que tinha de reprovar
| | Critério | Resultado | Controle (tem de reprovar) |
|---|---|---|---|
| A2 | porta fechada barra, aberta libera (varredura com a cápsula do personagem) | fechada: barrada pela folha; aberta a 90°: livre | a mesma varredura numa parede cheia: barrada |
| A5 | caminho de fora da porta até o lado da mesa, **com a porta aberta** | existe e é completo (678 cm no comando 1; 317 cm no comando 2) | destino fora da área: sem caminho. Porta fechada: caminho só até a porta (parcial) |
| A6 | um `Character` do Unreal entra pela porta aberta | chegou a 8,6 cm do destino em 3,7 s de jogo | porta fechada: o Unreal recusa o pedido (`FAILED`) e ele não sai do lugar |
| B | edição manual preservada | a mesa empurrada 30 cm "à mão" ficou onde estava (0,0 cm de diferença) e a planta adotou a posição; o cubo sem etiqueta ficou igual | — |
| C | prato e copo ficam sobre a mesa com a física ligada (3,1 s de jogo) | cada um desceu 0,1 cm e andou 0,0 cm | o copo levado para fora da borda caiu 77 cm |
| D | salvar, **fechar o editor** (4,7 s), reabrir (10,1 s) | 11 de 11 peças iguais (classe, ator, posição, giro, escala, parâmetros, pontos de uso); 0 diferenças entre a planta e o Unreal; medidas da sala e porta fechada conferidas de novo | — |
| E | `incorporar` | o copo empurrado no Play deslizou 13,7 cm; a posição nova ficou gravada no cenário (0,0 cm de diferença) e na planta | sem `incorporar`, parar o Play devolveu o copo ao lugar salvo |
| F | segurança | ficha inválida recusada sem tocar na cena; falha provocada no meio do lote: level recarregado do disco, cena igual à de antes; a sala seguiu funcionando | — |
| G | núcleo sem Unreal | 33 de 33 testes (`director/testes/testes_nucleo.py`), com 14 fichas que têm de ser recusadas | — |

## O que mudou nos critérios depois de ver o resultado (só endureceu)
- **A5** passou a ser medido com a porta **aberta**, e ganhou o controle "porta fechada tira o caminho". Motivo: no ensaio o personagem entrou e ficou preso na folha aberta, porque a folha não fazia parte da malha de navegação. A folha passou a fazer parte, e o laboratório passou a refazer a malha com o jogo rodando.

## As rodadas, sem esconder nada
1. **Ensaio** (cena `sala_demo`, etapa por etapa, 20:01 a 20:06): serviu para achar três defeitos meus (o personagem de teste não podia ser criado dentro do Play; a folha da porta fora da navegação; a colisão "grudada" da parede, ver CONHECIMENTO.md). Depois deles, todas as etapas passaram.
2. **Primeira passada completa** (cena nova, 20:07): **63 de 64**. Falhou o caminho pela porta aberta logo depois do comando 2: a malha de navegação ainda estava sendo refeita e o motor informava que não. Repetida a consulta, o caminho estava completo. Correção: o executor só considera a malha pronta depois de 4 leituras seguidas sem obra, e a medida de caminho espera até 5 s. Resumo guardado em `medidas/passada1_RESUMO_63de64.json`.
3. **Passada final** (cena nova, 20:10): **64 de 64**.
4. **Depois da troca de nome do pacote** (`director2` para `director`), a passada completa foi repetida numa cena nova (22:52): **64 de 64**. Resumo em `medidas/apos_renomear_RESUMO.json`.

## O que NÃO foi provado nesta entrega
- **A LLM pequena preenchendo as fichas.** As três fichas foram escritas à mão, como uma LLM escreveria. Nenhuma LLM participou.
- **Corpo e animação.** O personagem é a cápsula do `Character` do motor. A porta gira por parâmetro: ninguém a "abre" com a mão.
- **Aparência.** Tudo é cubo e cilindro do motor; o copo é um cilindro maciço.
- **Smart Objects, PCG e Geometry Script:** não foram usados. A porta e a mesa têm pontos de uso e de apoio como componentes simples.
- Duas aberturas na mesma parede (a divisão da parede está testada só sem o Unreal), mais de uma sala, sala girada, cenário de verdade.
- Sequência editável, câmera, vídeo.
- Itens que passam por construção: a medida interna dá 400,0 exato porque as peças são calculadas a partir do mesmo número; o que a medida prova é que a colisão está onde a planta diz.
