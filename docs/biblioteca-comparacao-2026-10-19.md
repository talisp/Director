# Biblioteca: conclusão do piloto e comparação — 19/10/2026

## Alternativas existentes

| Opção | O que resolve | Limite relevante para este ambiente |
|---|---|---|
| Connecter Suite | Gestão de arquivos/metadados, API HTTP e pacote Python, integração com Unreal | Assinatura e internet para licença/administração; não é operação totalmente desconectada. Changelog consultado confirma até UE 5.7; não comprovamos 5.8 nem instalamos o produto |
| Add-on oficial Poly Haven | Biblioteca integrada ao Asset Browser do Blender; código GPL-3.0, assets CC0 | Não é gerenciador nativo do Unreal nem do cache Fab. Exigiria Blender no fluxo; não usamos Blender. API tem termos próprios, separados da licença dos assets |
| RN0000/polyhaven-mcp | README declara busca, metadados e links pela API Poly Haven | Requer Node/npm; licença não identificada no metadado GitHub consultado; não demonstrado gerenciamento offline de Fab, importação ou validação física |
| Ponte/índice atual do Director | Busca no projeto, cena e arquivos locais, procedência/estado/dimensões e inspeção por trimesh | Piloto pequeno em JSON; busca por aliases não certifica função; não medimos milhares de assets nem concluímos necessidade de SQL |

Fontes primárias consultadas nesta data:
[Connecter/API](https://connecterapp.com/api-overview),
[produto e limites de conexão](https://connecterapp.com/),
[changelog Unreal](https://designconnected.zendesk.com/hc/en-us/articles/10900917928466-Unreal-Engine-Integration-Changelog),
[Poly Haven/licença](https://polyhaven.com/license),
[add-on oficial](https://github.com/Poly-Haven/polyhavenassets),
[MCP inspecionado](https://github.com/RN0000/polyhaven-mcp).
Poly Haven add-on: repositório não arquivado, push observado em 02/10/2026. MCP:
push observado em 08/07/2026, não arquivado. Atividade e declarações não comprovam integração.
Não instalamos, compramos ou adotamos essas alternativas para declarar uma comparação completa.

**Recomendação do piloto:** manter o índice e o importador nativo já existentes. Não construir
SQL, outro MCP ou gerenciador antes de medir uma necessidade não atendida. Connecter merece
teste se a gestão de uma biblioteca maior justificar licença/conectividade e se 5.8 for
confirmado. Para obter poucos assets Poly Haven, a API oficial evita introduzir Blender
ou um novo servidor no caminho. Isso não significa criar downloader permanente agora.

## Candidatos e medidas reais

O cache Fab e o lote Kenney já catalogados, a importação da cadeira Kenney e o ensaio
físico permanecem documentados em [biblioteca-piloto.md](biblioteca-piloto.md). O cache
da poltrona não prova licença: ela continua sem comprovante e não foi importada.

Triagem adicional: três modelos Poly Haven CC0, só glTF 1k com dependências declaradas,
total 5.467.198 bytes. Espaço livre antes do lote: 60,3 GiB. Cada arquivo foi conferido
por tamanho/MD5 do fornecedor e SHA256 local. Sem download amplo, pacote executável ou
asset binário no Git. Inspeção pelo trimesh 5.1.1, em centímetros com Z para cima:

| Modelo original | Largura × profundidade × altura (cm) | Conclusão |
|---|---|---|
| GothicCabinet_01 | 171,91 × 111,65 × 236,09 | Não serve como candidato estreito |
| modern_wooden_cabinet | 244,00 × 52,00 × 68,01 | Armário baixo/largo; não confundir com guarda-roupa alto |
| painted_wooden_cabinet_02 | 99,69 × 72,23 × 256,86 | Armário alto, três meshes nomeados corpo/gaveta/porta; requer tamanho adequado ao pedido |

Foi preparada uma variante **explícita de escala uniforme 0,8** do último, preservando
proporções: 79,75 × 57,79 × 205,49 cm. A transformação está no glTF derivado; não se
adulteraram os números do arquivo original no catálogo. Origem, fator, dimensões originais
e limite funcional constam na procedência. É candidato a armário de armazenamento;
não certificamos pendurar roupa, articulação da porta, interação com personagem ou física.

Fontes dos modelos: [Gothic](https://polyhaven.com/a/GothicCabinet_01),
[Modern](https://polyhaven.com/a/modern_wooden_cabinet),
[Painted](https://polyhaven.com/a/painted_wooden_cabinet_02).

Consultas verificadas no mesmo índice de sete itens:

- `cama de solteiro` / `single bed`: bedSingle.
- `cadeira` / `chair`: poltrona Fab e chairDesk, como candidatos com estados/licenças separados.
- `armario estreito` / `narrow wardrobe`: variante de armário 0,8, não um criado-mudo.
- Filtro mínimo 60×40×180 e máximo 90×60×220 cm: somente a variante.

Estado da variante: **baixado_nao_importado**. A prova nativa de importação/física do
piloto é a cadeira Kenney já registrada, não esse armário. Nem busca nem proximidade de
tamanho dispensam inspeção funcional antes de escolher um objeto para uma cena.
Lote e manifestos locais: `Saved/Director/biblioteca/arquivos/polyhaven-*`; inspeções e
scripts descartáveis: `work/polyhaven-*-20261019*`. Nenhuma licença Fab foi presumida.

[Extratos reproduzíveis das consultas e hash da variante](biblioteca-evidencias-2026-10-19.json).
