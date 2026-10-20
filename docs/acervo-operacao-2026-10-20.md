# Operacao do acervo — 20/10/2026

## Entregue

- PR69 incorporado em `617e617`; instalacao fixa avancou por fast-forward e passou
  os 29 testes dirigidos existentes. Sem reiniciar Hermes ou acessar modelo remoto.
- CLI de operacao: planejamento/download seletivo ArtVIP, importacao GLB/glTF nativa,
  leitura USD por pxr do Unreal, sincronizacao da planta apos mutacoes bem-sucedidas,
  verificacoes resumidas na busca e aliases sugeridos com procedencia.
- Fontes, metadados, downloads, backups e evidencias em `R:/CINF/BD`.
  Assets gerados pelo Unreal ficam no Content do laboratorio existente.
- Copiados 19 arquivos de tres pastas Poly Haven ja baixadas (5.476.793 bytes),
  preservando originais e verificando SHA256. Quatro glTF novos no inventario,
  incluindo variante; licenca declarada CC0 mantida pelos manifestos.
- Rotulagem por aliases aplicada a 2.758 candidatos; nao e rotulagem individual
  completa dos 14 mil objetos. Nao inferiu funcao, material ou fisica.

## Piloto ArtVIP real

Objeto selecionado: estojo articulado, revisao
`d22f2095bc9db29fdd4b60f4a3c4f8177e1f5e9e`, cinco arquivos, **78.435 bytes**.
Hashes conferidos contra o catalogo fixado (LFS SHA256 ou hash Git do arquivo).
Licenca declarada no dataset: Apache-2.0; nao se extrapolou para outros pacotes.

Leitor USD nativo do Unreal 5.8.3: Z-up, metro por unidade, 27 prims, cinco meshes,
uma PhysicsRevoluteJoint e uma PhysicsFixedJoint, zero dependencias ausentes.
A leitura nao criou atores, importou assets ou simulou essas juntas no Chaos.
HSSD autenticado/gated e compra/importacao de pacotes Fab nao foram realizados.

## Piloto rigido real

Mesa Kenney GLB ja local, importada por AssetImportTask/Interchange a partir de R:.
Vieram duas malhas (corpo e gaveta) e dois materiais. Nenhum dialogo nem sobrescrita;
foram salvos apenas os novos assets no laboratorio.

Em level de ensaio separado, merge nativo das duas malhas, com transformacoes/bounds
medidos pelo motor. Receita candidata persistida com referencias e dependencias.
Segunda instancia reutilizou o asset da receita. Tres segundos em Play:

| Ator | Fisica ligada | Deslocamento cm | Giro graus | Velocidades finais | Estavel no criterio do piloto |
|---|---|---|---|---|---|
| mesa | sim | 0 | 0 | zero | sim |
| mesa_copia | sim | 0 | 0 | zero | sim |

Criterio existente do verificador: deslocamento <=3 cm, giro <=2 graus,
velocidades linear/angular <1. Exigiu dois atores presentes com simulacao ligada.
Aprovacao registrada apenas para `rigido_composto_estavel_3s_em_duas_instancias`.
Nao valida abrir gaveta, manipulacao, personagem, durabilidade ou escala humana.
O merge tornou a gaveta rigida. Nao e uma solucao para pedidos de gaveta articulada.

Retorno a L_sala: inventario integral de atores identico, mesmo level, fora de Play,
sem pacotes por salvar. Projeto cinematografico nao acessado. Nao houve revisao visual
por screenshot nem teste de pedido humano por LLM.

## Registro e recuperacao

CLI sincroniza apenas a planta da cena afetada e indexa modelos alterados, sem reconstruir
os 14 mil registros por mutacao. Repeticao real medida: 1,861 s neste volume de rede;
medicao isolada, nao garantia universal. Erro SQL nao repete/desfaz uma operacao Unreal
ja aprovada: resposta carrega a pendencia e pede sincronizacao separada.

Instancias preservam historico, sem promover todos os atores a modelos reutilizaveis.
Receita registra contexto, nao pacote portavel independente do projeto. Ainda depende do
asset composto salvo no laboratorio; exportar para outro projeto exige ensaio separado.

## Testes e evidencias

29 testes existentes na instalacao publicada; 27 testes dirigidos da primeira etapa
(6 novos de operacao, 7 SQL, 10 coleta, 4 fontes) e 22 apos ampliacao (8 operacao, 7 SQL,
7 catalogo), todos aprovados. Rodadas sobrepostas: nao somar como casos independentes.
Verificacao adicional cobre indexacao parcial sem perder candidatos nao alterados.

Evidencias reais fora do Git: `R:/CINF/BD/Director/operacao-20261020/`:
`artvip-plano.json`, `artvip-download.json`, `artvip-inspecao-usd.json`,
`importacao-mesa.json`, `piloto-fisico.json`, `preservacao.json`,
`copias-polyhaven.json`, `coleta-arquivos.json`, `sincronizacao-incremental.json`.
Antes das mutacoes, backup SQLite consistente em `antes.sqlite3` nessa pasta.

## Pendencias conservadas

- Validacao conversacional do Hermes apos retorno da LLM; skill preparada nao e prova
  de leitura/uso por uma sessao do agente.
- Inventario completo Fab/outros projetos e rotulagem individual PT/EN com revisao.
  Nao se varreram todos os discos nem se abriu o projeto cinematografico.
- HSSD: aceite/autenticacao e primeiro modelo; Code4Scene: pacotes sao referencias,
  nao malhas redistribuidas. Nao criar outro downloader para contornar licencas.
- ArtVIP: importacao de articulacao real e compatibilidade com Chaos ainda nao provadas.
  USD joint no disco nao equivale a constraint funcional no motor.
- Criterios completos da issue36 (cinco ArtVIP, HSSD fisico e SpatialLM) continuam abertos.

Sondagem anonima HSSD em 20/10: HTTP 401 `GatedRepo` para um GLB selecionado.
Nenhum token foi lido, nenhum aceite foi feito e nenhum modelo HSSD foi baixado.
Evidencia local: `hssd-acesso.json`. O catalogo permanece consultavel sem isso.
