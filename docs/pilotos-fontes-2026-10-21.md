# Item 9 — pilotos pequenos de fontes e pesquisa

## Resultado e custo

Rodada deterministica, sem chamar Hermes, Luna, GLM ou GPU. Nao houve instalacao de dependencias, importacao de assets ou alteracao de atores. Payloads dos cinco downloads: **23.693.319 bytes (22,6 MiB)**, abaixo do teto de 30 MiB; consultas de metadados e codigo-fonte nao entram nesse subtotal. R: tinha aproximadamente 3.605 GiB livres antes da rodada.

Arquivos, manifests SHA256, API original e evidencias locais: `R:/CINF/BD/Director/pilotos-fontes-20261021/`. Catalogo: `R:/CINF/BD/Director/acervo.sqlite3`. Nenhum banco completo foi baixado.

## ambientCG: baixado e catalogado

| Material | Pacote | Bytes | Resultado |
|---|---|---:|---|
| Wood096 | 1K-JPG | 5.358.165 | 6 imagens; madeira clara com veios e nos |
| Tiles133A | 1K-JPG | 4.806.344 | 7 imagens; azulejos claros quadrados com rejunte |

Mapas de 1024x1024, previews de 512x512. Conferencia visual independente dos dois mapas Color confirmou a categoria; isso nao valida aparencia aplicada, escala UV ou iluminacao. Imagens verificadas com Pillow 13.0.0, dependencia ja existente em `requirements-biblioteca.txt`. Fonte e arquivos registrados como CC0-1.0, tags inglesas declaradas e portugues sugerido separados. Mapas e preview pertencem ao mesmo objeto SQL, nao a modelos 3D diferentes.

Proveniencia: [API oficial](https://docs.ambientcg.com/api/v2/full_json/), [licenca incluindo previews](https://docs.ambientcg.com/license/), [Wood096](https://ambientcg.com/view?id=Wood096), [Tiles133A](https://ambientcg.com/view?id=Tiles133A), consultados em 21/10/2026. Tamanho remoto, SHA local e CRC ZIP conferidos. O fornecedor nao forneceu SHA remoto neste fluxo: nao alegamos autenticidade por hash remoto.

O coletor `director/fontes_piloto.py` limita downloads, revalida cache, recusa sobrescrita divergente e arquivos existentes sem manifesto. A extracao aceita somente PNG/JPEG, recusa traversal, nomes duplicados, links e excesso de tamanho; nao executa conteudo. Reuso desta rodada nao repetiu downloads. Nao constitui nova permissao generica para baixar qualquer fonte.

**Pendente #35:** importar texturas e construir materiais Unreal; aplicar madeira/azulejo; verificar visualmente; salvar/reabrir; provar preservacao de geometria, colisao e navegacao. O nivel `/Game/Director/Cenas/L_sala` ja estava sujo e permaneceu com o mesmo pacote sujo na consulta posterior. Foi preservado, sem salvar/reabrir. Existiam materiais de madeira no projeto; nao foi encontrado azulejo por nome. Existencia por nome nao prova adequacao.

## SpatialLM: plantas separadas funcionam

[Dataset oficial](https://huggingface.co/datasets/manycore-research/SpatialLM-Dataset), revisao `ab8de0983f48490a0a8850baa32308982d6fbacc`, CC-BY-NC-4.0, atribuicao Manycore Research registrada no SQL. Baixados somente `layout/chunk_000.zip` (1.854.742 bytes), `split.csv` (11.655.272) e LICENSE (18.796), sem pointclouds.

O chunk tem 2.000 arquivos de layout, validados pela gramatica numerica restrita sem eval/exec. Deduplicacao por `scene_id,room_id`, preferindo menor sample: **506 comodos**, nao 2.000 plantas independentes. Zero falhas de contagem na leitura.

Filtro explicito `room_type` contendo `bedroom`: **149 dormitorios**, sendo **120 com janela, 148 com porta, 134 com cama**. `guest room` e `child room` nao entram nesse filtro. Sao dados do primeiro chunk, nao amostragem aleatoria representativa de todo o banco.

134 distancias entre centro da cama e centro da porta mais proxima em XY: mediana **2,5881**, minimo 1,3762, maximo 4,3716, em unidades nativas do layout. Nao certificamos metros nem passagem livre. Em um caso, translacao conjunta preservou a medida exatamente e rotacao de 90 graus teve erro de 4,44e-16. Isso testa nossa conta, nao o funcionamento da biblioteca oficial.

O [codigo SpatialLM](https://github.com/manycore-research/SpatialLM/tree/8913c44d84a450c53e9340b13317f8cf7144a738), `layout/layout.py:from_str` e `layout/entity.py`, foi lido. Exige SciPy, ausente nos tres runtimes consultados; a tentativa de executa-lo falhou antes da analise. Nao instalamos dependencias. Licenca do codigo: **Llama 3.2 Community**, distinta da licenca dos dados. Nao foi incorporado ao Director. O script independente usa apenas biblioteca padrao.

Reproducao offline, escrevendo somente os dois resumos na pasta de evidencias indicada:

```powershell
python docs/pilotos/spatiallm_estatisticas.py R:/CINF/BD/Director/pilotos-fontes-20261021
```

[Resumo versionado](pilotos/spatiallm-resumo-20261021.json). SQL guarda amostra de layout, estatisticas, licenca e atribuicao; nao finge tratar-se de um modelo 3D instalavel. **Pendente #36/#31:** a revisao consumir/citar o resumo e demonstrar utilidade no pedido humano. Nao transformar frequencias em restricoes obrigatorias.

## ArtVIP, HSSD e Fab: limites atuais

- **ArtVIP:** cinco objetos ja constavam instalados no SQL. Isso nao certifica a meta de cinco objetos com escala comparada ao banco em ate 2 cm e colisao medida. Nenhuma nova rodada de importacao/fisica foi executada aqui. Montagem e articulacao continuam pendentes; a coleta USD em hierarquia esta em trabalho separado.
- **HSSD:** HEAD anonimo retornou **401 GatedRepo**. [Fonte oficial](https://huggingface.co/datasets/hssd/hssd-models) exige aceite/autenticacao. Nao aceitei termos em nome do usuario nem li tokens. Catalogo existente pode ser consultado; download/importacao e estabilidade fisica continuam bloqueados.
- **Fab/Code4Scene:** referencias de catalogo nao comprovam entitlement, download ou licenca dos packs. Nenhum pack foi comprado/baixado; priorizar assets locais quando adequados. A descoberta da biblioteca e o piloto de importacao Fab continuam pendentes.

## Pesquisa GitHub orientada a uma lacuna

[Ficha real](pilotos/ficha-spatiallm-20261021.json): problema, commits, algoritmo/inspiracao, prova, variacao, licencas distintas, limites e procedimento de operador. Passou no validador de forma local `hermes/skills/director-research/scripts/verificar_ficha.py`; passar no schema nao e auditoria de funcionamento. O ensaio de dados foi executado separadamente.

O desenvolvimento local da skill 0.3.0 ja tem essa ficha e orcamento. Nao o instalamos nem sobrescrevemos o trabalho existente. Ha uma incoerencia a resolver antes de liberar: SKILL manda continuar ate esvaziar a fila, enquanto a ficha aceita teto de custo. A regra futura precisa encerrar **o lote ao atingir o orcamento autorizado**, preservar cursor/fila e relatar pendencia; retomada nao pode ampliar custo por conta propria. Separar chamadas LLM, HTTP e bytes, em vez de uma contagem ambigua. Na ficha deste ensaio `chamadas` significa inferencias LLM (zero).

**Pendente #15:** harmonizar essa regra no protocolo, revisar/instalar a skill e validar uma pesquisa curta pelo Hermes/Luna em sessao nova. Nenhuma inferencia foi disparada nesta rodada.

## Verificacao e retomada

Seis testes offline passaram: cache/hash, limite/tamanho, descarte de parcial, manifesto ausente, ZIP hostil e escopo de armazenamento. A primeira rodada teve uma falha na fixture de ZIP com barra invertida normalizada pelo Windows; fixture corrigida para representar cabecalho externo real, teste repetido com sucesso. Testes de plantas e variacoes acima executados; nao sao testes de cena Unreal.

Ordem restante: (1) resolver aceite HSSD com o usuario quando necessario; (2) material nativo e verificacao em cena controlada; (3) metas de escala/colisao dos cinco ArtVIP; (4) consulta das estatisticas pela revisao; (5) pesquisa curta Hermes/Luna. Nao fechar #35, #36 ou #15 so porque existem downloads e um resumo SQL.
