# Biblioteca — bloco 3, 18/10/2026

Indice e arquivos locais passam a `Saved/Director/biblioteca` do laboratorio, separados
do checkout. Os seis arquivos do lote anterior foram copiados com hash conferido, preservando
fontes/procedencia/licenca. Nao ha novo SQL, servidor de busca ou download amplo.

Corrigidos aliases especificos e expansao de busca: cabinetBed e criado-mudo, nao cama ou
guarda-roupa; chairDesk e cadeira, nao escrivaninha; bookcaseClosedDoors e estante;
armchair e candidato a cadeira/poltrona. Categoria registrada prevalece sobre fragmentos do nome.
A busca aceita minimo_cm alem de maximo_cm. Dimensoes medidas nao comprovam escala humana.

Consultas PT/EN verificadas no lote: cama de solteiro/single bed -> bedSingle;
cadeira/chair -> Ornate Royal Armchair e chairDesk; armario estreito/narrow wardrobe -> vazio.
O lote NAO contem guarda-roupa. Nao classificar um criado como tal apenas para devolver resultado.
Com minimo 80 x 180 x 30 cm, a cama miniatura (57,1 x 112,5 x 37,5) e recusada.

## Importacao pequena real

Kenney chairDesk GLB (CC0), ja presente localmente. A importacao nativa Interchange gerou
duas StaticMeshes (base e assento/encosto). A primeira tentativa assumia uma so e foi
recusada pelo ensaio, sem alterar atores; assets importados permaneceram. Save da tarefa
nao deixou todos os materiais limpos: os dois pacotes pendentes foram identificados e salvos.

As duas partes foram unidas pela capacidade `object_model(partes)` JA EXISTENTE, com seus
assets/centros/tamanhos medidos pelo motor. Nenhum vertice foi reconstruido em Python.
O resultado e um unico mesh/ator com identidade, oito convexos gerados pelo editor nativo.

- Tamanho offline: 33,495 x 31,4299 x 60,7600 cm.
- Tamanho Unreal unido: 33,5048 x 31,4299 x 60,7600 cm; maior diferenca < 0,01 cm.
- Escala uniforme escolhida para o piloto: 1,35, registrada separadamente das medidas originais.
- Cena separada piloto_biblioteca_20261018, sala 4 x 4 m, cadeira_kenney como unico objeto.
- Play 3 s: fisica ligada, deslocamento 0,15 cm, giro 0,732 graus, velocidades finais zero, estavel.
- Planta e editor: zero diferencas. Retorno a L_sala com inventario integral identico ao inicial.

Registros locais: work/pipeline_20261018/biblioteca. Assets no laboratorio; nada do Fab/Kenney
foi incluido no repositorio. O indice informa importacao e validacoes parciais, nao certificacao
de uso com personagem. Nao se testou sentar, manipulacao nem fidelidade visual final.
O Fab foi catalogado, mas o comprovante de licenca da poltrona nao foi verificado nem ela importada.

#27 continua aberta: faltam candidato real a armario e comparacao dos gerenciadores prontos
antes de qualquer escolha de banco/gerenciador. O piloto comprova reutilizacao local e fisica;
nao autoriza declarar toda a biblioteca pronta. Os acervos grandes permanecem na ordem de #36.

Atualização de 19/10: [comparação e conclusão do piloto](biblioteca-comparacao-2026-10-19.md),
com candidato de armário redimensionado explicitamente e consultas/filtro conferidos.
O estado desse candidato permanece baixado, não importado nem validado fisicamente.
