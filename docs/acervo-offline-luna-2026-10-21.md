# Aquisicao e reutilizacao reais pelo Hermes/Luna — 21/10/2026

## Ambiente e pedido

Director publicado c9bab4b, skill 0.5.20. Perfil director; modelo gpt-6-luna,
provider openai-codex, reasoning low, seis rodadas de ferramentas e orcamento
180 s. Fonte/modelo conferidos no estado da sessao, nao inferidos de metadata
antiga. Sem Unreal/Blender, sem preparar/importar/inspecionar_usd. Nenhuma mudanca
de cena, configuracao ou codigo feita pelo Hermes.

Pedido: localizar a mesa ArtVIP ja identificada no ensaio de recusa, planejar e
baixar ate 2 MiB, confirmar registro e repetir. O ID foi fornecido para repetir
o caso conhecido; este ensaio nao comprova escolha autonoma do melhor modelo.

Objeto: `8975207ff2ec6e45bc809c1261eab850c2aacb1fa4e6604ea7f95c74fba134cf`.
Revisao ArtVIP: `d22f2095bc9db29fdd4b60f4a3c4f8177e1f5e9e`, Apache-2.0.

## Resultado e conferencia independente

| Criterio previamente pedido | Resultado |
|---|---|
| Buscar e consultar plano | Executados pela CLI publicada |
| Respeitar fonte/licenca/teto de 2.097.152 bytes | Cinco arquivos, 1.337.456 bytes |
| Baixar e registrar | Cinco novos arquivos no cache R:, um principal indexado no SQL |
| Repetir sem baixar/duplicar | Cinco de cinco arquivos reutilizados |
| Preservar acervo existente | 14.510 objetos antes/depois; hashes dos arquivos anteriores iguais |
| Preservar importacoes/medidas/provas | Instalacoes, variantes, metadados, partes e verificacoes identicos |
| Integridade SQL | quick_check ok; zero violacoes FK |
| Nao inventar fisica/dimensoes | Ficha nao inspecionada, geometria null, fisica nao_testada; relato coerente |
| Respeitar sessao sem Unreal | Seis ferramentas terminal somente; buscar, ajuda, plano, baixar, ficha, baixar |

Principal: `R:/CINF/BD/ArtVIP/d22f2095bc9db29fdd4b60f4a3c4f8177e1f5e9e/Articulated_objects/small_furniture/table/table/model_table.usd`.
SHA256 de todos os cinco arquivos e tamanho foram recalculados pelo Codex.
SQL arquivos: 43 -> 44; dependencias estao no manifesto, nao sao cinco objetos
ou cinco linhas da tabela arquivos. Nada foi promovido a asset importado.

Classificacao PA **ATENDIDO para o pedido offline acima**, nao para colocar mesa
ou notebook na cena. Dimensoes, apoio, articulacoes, texturas no motor e fisica
permanecem sem nova prova. Fonte pode ter dependencias externas nao resolvidas.

## Tempo e contexto observados

Sessao `local-39463d4d3422c06852e579fe6b067dbcecbf9263d20192a650c2dc2ea404c5d8`:
33,635 s, cinco chamadas API, seis ferramentas. Contadores do Hermes: 97.560
tokens de entrada acumulados, 74.752 de leitura de cache, 989 de saida. Nao sao
uma janela de 97 mil tokens nem uma medicao independente do faturamento.

Medidor nativo: cinco requisicoes; bytes das mensagens 1.485, 10.388, 15.959,
19.574 e 24.203; prefixo repetido 0, 1.485, 10.388, 15.959 e 19.574 bytes.
System e schema sao contabilizados separadamente. Nao ha comparacao controlada
contra GLM/Qwen nem demonstracao de reducao de custo nesta rodada.

Dados brutos/backup consistente/comparacoes ficam em
`R:/CINF/BD/Director/correcoes-sem-unreal-20261021/`; nao foram publicados prompts,
estado pessoal, credenciais ou banco no GitHub. Evidencias: aquisicao-positivo-luna.jsonl,
snapshot-antes/depois.json e verificacao-positivo.json.

## Falha encontrada na propria publicacao e correcao

A regressao ampliada no checkout publicado executou 68 testes: 67 passaram e
um reaplicador falhou. O arquivo patch sofre conversao CRLF no checkout Windows.
Normalizar apenas a leitura nao basta: stdin em modo texto tambem traduz LF
para CRLF no Windows. Reaplicador agora le texto normalizado e envia bytes UTF-8
ao git apply. Teste adicional cobre patch CRLF; recusa de base/conflito e backups
continuam ativos. Hermes ativo ja estava corrigido; nenhum rollback ou novo
restart foi necessario. Testes afetados: 15 passaram apos o ajuste.

Novo teste de download: falha de rede na segunda dependencia nao registra lote
incompleto, remove .part e retoma reutilizando o principal validado. E uma falha
injetada em copia isolada, nao interrupcao real deliberada da rede de producao.

O terminal tem permissao do usuario Windows: validacao da API e skill nao sao
sandbox de SO contra SQL arbitrario. O ensaio comprova adesao ao caminho, nao
impossibilidade de outro agente burlar esse caminho.
