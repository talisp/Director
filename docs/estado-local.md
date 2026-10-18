# Plantas vinculadas ao laboratorio

`python -m director contexto` informa o level aberto e a fonte real das plantas, sem trocar de level.
O operador retoma esse contexto em vez de selecionar sempre `sala`.

Para migrar uma instalacao antiga, com o laboratorio salvo e fora de Play:

`python -m director vincular CAMINHO_DA_PASTA_CENAS`

O comando valida TODAS as plantas da pasta contra os atores dos levels existentes e restaura
o level inicialmente aberto. Level inexistente nao e criado. Qualquer divergencia recusa a
vinculacao; nao escolhe a maior revisao nem adota uma copia automaticamente. A pasta fonte
e preservada. Cenas e registros sao copiados para `Saved/Director/cenas` do projeto de laboratorio.
Um manifesto `Saved/Director/vinculo.json` ativa a fonte compartilhada somente depois da validacao.

Checkouts atualizados do Director que apontam para o mesmo laboratorio consultam essa fonte.
O codigo e os exemplos versionados continuam separados do estado de trabalho. Um vinculo
corrompido ou um destino ausente falham explicitamente; nao voltam a uma planta velha.
A trava tambem fica no laboratorio (`Saved/Director/unreal_lab.trava`). Nao opere simultaneamente
com versoes antigas que ainda usam travas de checkout; atualize os operadores antes.

Recuperacao: preserve a pasta compartilhada e o manifesto antes de qualquer reparo. Uma falha
anterior a publicacao pode deixar uma pasta `cenas` nao ativada; confira-a e recupere explicitamente,
sem excluir/copiar por cima automaticamente. As plantas fontes continuam disponiveis.
Rollback do codigo exige manter os operadores parados e configurar sua fonte de estado;
uma versao antiga nao reconhece esse manifesto. Nao reverta para uma planta fonte que ja ficou velha.

Verificacao local em 18/10/2026: `sala` rev22 e `hermes_quarto_final` rev78 tiveram zero
diferencas integrais contra os atores controlados. Fontes preservadas, level L_sala restaurado,
sem Play ou pacotes por salvar. Testes incluem recusa por parede ausente, falha em outro level,
preservacao da fonte, vinculo invalido e dois checkouts usando a mesma planta.
