# Comandos novos — exemplos de uso

Execute na raiz do repositorio. Arquivos de pedido sao JSON UTF-8. IDs e
coordenadas abaixo sao exemplos; consulte a cena aberta. Unidades da ficha e
objeto: metros. Medidas, rotas, solver e partes compostas: centimetros.

| Comando | Exemplo | Para que usar |
|---|---|---|
| ensaio criar | `python -m director ensaio criar tentativa pedido.txt` | Pasta oficial e pedido preservado; retorna ID |
| ensaio executar | `python -m director ensaio executar ID work/ensaios/ID/teste.py` | Python no editor, hash e inventario antes/depois, inclusive erro |
| ensaio listar | `python -m director ensaio listar ID` | Consultar registros locais |
| relatorio | `python -m director relatorio cena quarto` | Solicitado/plano/medido/nao verificado |
| verificar | `python -m director verificar cena verificar.json` | Contencao, apoio, colisoes e circulacao solicitada |
| objeto | `python -m director objeto cena objeto.json` | Adotar, duplicar, compor ou colocar objeto registrado |
| procurar | `python -m director procurar cadeira` | Cena, projeto e biblioteca; cena primeiro |
| catalogo | `python -m director catalogo atualizar` | Atualizar metadados locais |
| planejar | `python -m director planejar cena planejamento.json` | Proposta CP-SAT, sem aplicar |
| navegacao | `python -m director navegacao navegacao.json` | Escopo, backup e restauracao; ainda parcial |
| api atualizar | `python -m director api atualizar` | Gerar cache a partir da instalacao |
| api consultar | `python -m director api get_linear_damping` | Consultar trechos do cache offline |
| biblioteca indexar | `python -m director biblioteca indexar biblioteca.json` | Inspecionar arquivos sem Unreal |
| biblioteca consultar | `python -m director biblioteca cadeira` | Consulta offline sem ponte |
| preparar | `python -m director preparar nova_cena work/restauracao/cena/SNAPSHOT` | Copia independente; nao executa pedido do quarto |

Exemplo `verificar.json`:
```json
{"salas":["quarto"],"simular":true,"segundos":3,"rotas":[{"nome":"entrada","de":[200,515,1],"ate":[8,575,1],"tolerancia_cm":10}]}
```
`simular` cria personagem temporario e roda Play. Sem essa opcao e leitura.
`baseline` recebe caminho de inventario anterior; `foto` recebe PNG opcional e
requer Pillow no Python cliente. Sobreposicao de envelopes e indicio conservador.

Exemplo `objeto.json` para adotar a cadeira existente:
```json
{"acao":"adotar","ator":"Cadeira_mesa1","id":"cadeira_estudos","sala":"quarto","categoria":"cadeira","x_m":1.5,"y_m":1.5}
```
Duplicar: trocar acao por `duplicar`. Colocar: `acao: colocar` e
`asset: /Game/Pasta/SM_Modelo`. Compor: `acao: compor` e
`partes: [{"centro_cm":[0,0,25],"tamanho_cm":[40,40,50]}]`.
A cadeira de referencia e DynamicMesh e pode ser convertida pelo GeometryScript.
As massas padrao sao estimativas: cama 45, criado_mudo 12, guarda_roupa 80,
escrivaninha 25, cadeira 8 kg; ajuste com massa_kg quando conhecido. Nao transfere
comportamento de Blueprint para uma malha convertida.

Exemplo `planejamento.json`:
```json
{"sala":"quarto","objetos":[{"id":"armario","dimensoes_cm":[100,60,180],"uso_frente_cm":80,"girar":true}],"segundos":5}
```
Para compactar: use `minimo_cm: [200,200]` e `maximo_cm: [400,400]` sem sala fixa.
Com `sala` e `minimo_cm`/`maximo_cm`, testa outros tamanhos com as portas reais
da sala sem abrir a ponte e sem mudar a cena (`origem` diz isso). Giros
0/90/180/270; moveis encostados na parede por padrao (`encostar: false` solta).
`na_frente_de` (cadeira encostada e virada para a mesa) e `ao_lado_de`
(criado-mudo junto da cama). Se o filtro 2D reprova, o planejar tenta outras
arrumacoes (`tentativas`, padrao 40; `tentativas_por_tamanho` 6, depois o
tamanho sobe 3%). Moveis registrados fora do pedido ficam reservados
(`mantidos_da_cena`). `planejar` e `verificar` respondem primeiro com
`veredito` (APROVADO/REPROVADO/ERRO), `motivo` e `proxima_acao`.

Objeto apoiado: `{"acao":"colocar","asset":"/Game/...","sala":"quarto","id":"travesseiro1","sobre":"cama1","categoria":"travesseiro"}`.
Peca fixa: `"fixo": true` (padrao para box, chuveiro, vaso_sanitario, pia,
bancada, divisoria, parede) registra sem simular fisica.
Para examinar paredes compartilhadas da proposta, inclua
`nova_sala: {"id":"quarto_novo","x_m":-2.15,"y_m":0}`. A proposta deve passar
pelo nucleo e pela verificacao do editor depois; o solver usa retangulos 0/90.
Instalacao opcional local: `python -m venv .venv-planejamento` e depois
`.venv-planejamento/Scripts/python.exe -m pip install -r requirements-planejamento.txt`.

Exemplo `navegacao.json`:
```json
{"acao":"ajustar","escopo":"regiao","regiao":[[-1000,-200,-20],[-500,400,300]],"celula_cm":5,"altura_cm":2}
```
Diagnosticar: `{"acao":"diagnosticar"}`. Restaurar:
`{"acao":"restaurar","backup":"CAMINHO_RETORNADO.json"}`. `escopo: level`
afeta toda a malha. Regiao tambem pode afetar outros modificadores HIGH e tiles.
Regional ainda nao corrigiu norte-sul no ensaio: nao declarar resolvido.

Exemplo `biblioteca.json`:
```json
{"fontes":[{"arquivos":["work/biblioteca/cadeira.glb"],"licenca":"CC0","proveniencia":"origem e versao verificadas"}]}
```
FBX exige `blender: CAMINHO_DO_EXECUTAVEL`. Ambiente opcional `.venv-biblioteca`
com requirements-biblioteca.txt. So indexa arquivos locais; nao e downloader.
Nao altera o editor nem importa modelos. Nao decide SQL/RAG permanente.

Filtro adicional, sem abrir a ponte: `python -m director planta2d cena quarto`.
Depende de Shapely no mesmo ambiente opcional do solver. Usa apenas a planta;
objetos externos nao entram. `planejar` reserva portas e janelas e submete o
candidato ao filtro; uma reprovacao nao prova que inexiste outra distribuicao.
