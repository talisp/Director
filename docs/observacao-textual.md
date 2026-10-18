# Observacao compacta — bloco 4, 18/10/2026

`observar CENA --texto SALA` desenha a planta desejada sem conectar ao editor. Norte em cima,
escala declarada, legenda por id, folhas/dobradicas, janelas, zonas reservadas e moveis.
Inclui compartilhamento de paredes e excesso de pegada alem dos limites internos planejados.
Nao prova que a cena real corresponde ao desenho. Nao e chamado automaticamente em toda consulta.

`observar` normal agora declara convencoes: canto sudoeste interno da sala, dimensoes internas,
centro do movel em coordenadas do mundo. Para moveis com caixa real, reutiliza `contencao`
do verificador e devolve excesso interno/externo, sem fazer a LLM repetir a conta.

## Verificacao e resultado do experimento

Tres testes do desenho: centro dentro de uma celula, norte/escala, objeto fora da parede nao
recortado e limites explicitos. 16 testes direcionados de desenho/interface aprovados.
O comando real funcionou com porta do laboratorio configurada como 1, comprovando caminho offline.
A leitura real de mesa1 no editor devolveu a contencao pelo mesmo verificador existente.

Comparacao curta com o Qwen pelo Hermes, somente perguntas sobre o quarto atual rev78:

| Entrada | Tempo | Entrada acumulada | Saida | Observacao |
|---|---:|---:|---:|---|
| JSON reduzido | 79,835 s | 12.718 | 5.172 | acertou porta, criado e parede candidata; confundiu largura interna/externa |
| Texto + legenda | 124,551 s | 13.127 (11.532 cache) | 9.110 | acertou largura interna; nao demonstrou ganho de custo/latencia |
| Texto + legenda, reasoning low | 97,792 s | 13.126 (sem cache) | 6.471 | largura correta, mas chamou parede norte de livre apesar dos moveis |

Nao e benchmark geral. JSON tinha 1.919 bytes e texto/legenda 3.488; o segundo explicita
`interno_cm`, portanto a comparacao mistura representacao e rotulagem. Isso motivou corrigir
primeiro os rotulos do JSON. A pergunta sobre movel que 'sai da parede' era ambigua:
o modelo interpretou como projetar-se para dentro; nao atribuir uma nota objetiva a esse item.
No protocolo futuro, perguntar se ULTRAPASSA o limite interno para FORA e usar a contencao calculada.
O objeto cama estava dentro; a cena nao foi alterada para produzir esse experimento.

Nao foi medida a condicao fotografia/visao, nem repetido o JSON com os rotulos corrigidos.
As tres rodadas nao isolam efeito de reasoning ou cache. O perfil continua em high;
nao ha evidencia suficiente para reduzir globalmente nem recomendar texto por economia.
#30 permanece aberta para essa comparacao controlada. A grade e opcional; se os dados
estruturados bastarem, nao envia-la. Nenhuma inferencia adicional foi feita apenas para obter
uma nota melhor. Sessoes e respostas brutas ficam em work/pipeline_20261018/comparacao_*.

Aprendizado: o retorno deve explicitar referencias geometricas e trazer contas deterministicas
ja prontas. Uma imagem/desenho nao substitui convencoes, relacoes nem evidencia nativa.
