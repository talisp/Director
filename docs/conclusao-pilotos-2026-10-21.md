# Pilotos: complemento, publicacao e auditoria de issues

## Entregue nesta rodada

- `director/editor/materiais_piloto.py`: importacao nativa de Color/NormalDX/Roughness e criacao de dois materiais novos em `/Game/Director/Acervo/PilotoMateriais/Item9_20261021/`. Usa TextureFactory, AssetImportTask e MaterialEditingLibrary efetivamente presentes no Unreal **5.8.3-58210709** instalado. Destino existente e recusado; falha parcial pede inspecao, sem repetir importacao silenciosamente. O modulo e para desenvolvimento/piloto e nao e chamado automaticamente pelo agente.
- `M_madeira_clara_Wood096` e `M_azulejo_branco_Tiles133A`: tres conexoes confirmadas em cada material, assets salvos e reconhecidos como MaterialInterface. Instalacoes ligadas aos mesmos objetos ambientCG no SQL, sem duplicar modelos.
- `revisao.avaliar`: recebe `referencias_layout: [id_do_acervo]`, ate tres IDs. Leitura SQL parametrizada, tipo/fonte restritos, projecao compacta com denominadores, revisao da fonte e limites. Nao modifica notas ou impoe medidas. Exemplo real: ID `dfb276b8cb93bae846ea1e66268183e4b9222b2217dae7e5aa1585f54c37310d` retorna a amostra de 506 comodos/149 dormitorios do piloto anterior.
- Skill **director-research 0.3.1** versionada e instalada no perfil pesquisador existente `hermes-dev`, sem alterar configuracao, fila, estudos ou reiniciar gateway. Instalador confere baseline, recusa conflito/perfil ocupado, faz backup e preserva extras. Conferencia posterior: fonte e instalacao iguais. Nao atualiza a skill de operacao do perfil Director.
- Pesquisa vinculada a problema/issue/pedido/commits; ficha curta com evidencias, variacao, licenca, limites e orcamento. Teto por lote prevalece sobre continuar fila; `partial ... orcamento` preserva checkpoint e ordem de retomada. Caso real SpatialLM e ficha publicados no PR #80; ensaio numerico e distinto de validar schema JSON.

## Provas e limitacoes

**Testes:** sete testes de revisao/referencias/materiais, tres da ficha/fila e dois do instalador passaram; suite funcional preexistente da skill passou, incluindo caminhos protegidos, retomada, checkpoints, rubrica e medicao de contexto. Novos casos comprovam leitura SQL sem alterar bytes do banco, referencia opcional sem alterar notas, entrada ampla recusada e pausa/retomada com proximo item preservado.

Uma primeira execucao de pesquisa em R:/CINF/BD/Director/temporarios foi recusada pela protecao nominal da skill contra pastas Director. Usamos R:/CINF/BD/pesquisa-temporarios, fora desse nome protegido, sem enfraquecer a guarda. Outra rodada em SMB teve WinError5 no replace de fila.md; repeticao da suite passou. Nao afirmamos que essa falha transitoria de armazenamento foi corrigida; a fila real da pesquisa permanece no armazenamento local existente.

**Unreal:** 43 atores com mesmas identidades/classes/transformacoes antes/depois. A comparacao inicial de str(Vector/Rotator) falhou porque a representacao inclui endereco temporario de memoria; removido somente esse endereco, nenhuma diferenca restante nas coordenadas exibidas com seis decimais. `L_sala` permaneceu aberto e sujo, como antes. Nao salvamos/reabrimos o nivel nem aplicamos materiais a seus atores. Assim, esta rodada **nao prova** foto de material aplicado, persistencia na planta apos reabrir, colisao ou navegacao inalteradas por aplicacao. #35 continua aberta.

**Hermes:** um ensaio novo pediu explicitamente gpt-6-luna/openai-codex/low e ate tres turnos. Adaptador gateway recusou --run-budget, apesar de constar no help instalado, antes de criar sessao; nenhuma configuracao global foi alterada. Sem essa flag, init anunciou Luna, mas metadata final da mesma sessao registrou glm-5.3-flash/custom, uma chamada de API e duas ferramentas. A identidade efetivamente servida nao foi certificada no servidor. Isso nao e resultado de teste Luna. Ensaio interrompido via RPC com generation da propria sessao; consulta posterior confirmou **running:false**, generation 1. Nao repetimos inferencias nem reiniciamos outros agentes. Defeito registrado em **[#81](https://github.com/talisp/Director/issues/81)**; investigar rota antes de novos testes. Nao alegamos zero inferencias nesta rodada.

Artefatos locais: `R:/CINF/BD/Director/conclusao-pilotos-20261021/`, incluindo materiais-nativos.json, referencia-sql-revisao.json, validacao-final.json e hermes-cancelamento.json. Logs brutos de Hermes, credenciais e raciocinio privado nao sao publicados.

## Auditoria das issues

Lista aberta do GitHub e criterios examinados antes da decisao. Nao usamos numero de commits como evidencia de conclusao.

| Issue | Decisao | Evidencia ou criterio ainda faltante |
|---|---|---|
| #15 | Encerrar pelo escopo de engenharia/pesquisa | Skill, vinculo/ficha/orcamento, instalador e testes entregues; pesquisa real SpatialLM tem hipotese, fonte, variacao e aceitacao. Isso satisfaz a aceitacao escrita. O teste conversacional Luna permanece inconclusivo em #81, nao foi promovido a sucesso. |
| #35 | Manter | Materiais nativos salvos; faltam aplicacao/foto, planta/save/reopen e medidas de colisao/nav. |
| #36 | Manter | SpatialLM agora pode ser citado pela revisao. HSSD exige aceite/autenticacao; cinco ArtVIP ainda precisam prova completa de escala/colisao. Catalogo Fab nao certifica entitlement/licenca. |
| #75 | Manter | Ficha compacta existe; validade completa de provas nativas/funcionais e generalizacao ainda nao demonstradas. |
| #68 | Manter | Falhas dependentes/IDs/QA exigem os casos adversariais definidos; nao substituir por testes de material. |
| #48 | Manter | Pipeline agregador: ha entregas e gates pendentes. Item 9 nao esta integralmente encerrado. |
| #39 | Manter | Falta medicao comparavel de replay/contexto e compressao; resumo menor sozinho nao prova melhora. |
| #38 | Manter | Mensagens/cancelamento na interface real e testes de concorrencia ainda incompletos. Cancelar nosso ensaio por RPC nao satisfaz toda a issue. |
| #22 | Manter | Sessao atual tem acesso irrestrito; nao comprova novas sessoes restritas Codex/Claude com zero aprovacoes. |
| #17 | Manter | Duas pontes 8080 e recuperacao persistente/queda ainda nao demonstradas. |
| #6 | Manter | Nenhum novo write_file bem-sucedido no aplicativo; teste CLI/terminal nao fecha falha do app. |
| #4 | Manter | Falta bateria PA com variacoes e preservacao, respeitando limite de custo. |
| #81 | Nova, manter | Divergencia de rota solicitada/anunciada/registrada no gateway; conferir antes de inferencias adicionais. |

## Retomada ordenada

Primeiro resolver #81 para poder testar com o modelo autorizado. Depois concluir material em cena controlada, provas restantes ArtVIP e acesso licenciado HSSD/Fab. Nao descarregar bancos inteiros, nao ampliar bateria de modelos e nao transformar este complemento em reconstrucao do Director. O trabalho de hierarquia USD permanece separado e preservado.
