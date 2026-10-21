# Acervo sob demanda — 21/10/2026

## Fluxo implementado

`buscar → ficha → preparar → comparar → importar → posicionar → verificar pedido`.
Preparar cobre download/registro/medida e, opcionalmente, importação de malhas.
Posicionamento e verificação da interação usam as ferramentas existentes do Director;
preparar não cria atores, não altera a planta e não escolhe sozinho o melhor candidato.

```json
{"acao":"preparar","objeto":"ID_SQL","autorizar_download":true,
 "origem":"usuario/sessao/pedido","pedido_id":"pedido-estavel","sessao":"ID_HERMES"}
```

Enviar por `python -m director acervo pedido -` ou JSON literal em um argumento.
Não exige arquivo temporário. O pedido identifica a autorização existente; não
representa assinatura criptográfica do usuário. Não perguntar de novo por cada
etapa já autorizada. `importar:true` acrescenta importação nativa, em pasta nova
determinada pelo controlador. A consulta `preparacao` com `id` mostra o checkpoint.

O backend determina banco, URLs, revisão, destino e limite. Aceita somente ArtVIP
Apache-2.0 neste fluxo; não aceita SQL, URL, dimensão, aprovação ou destino fornecidos
no pedido. Limite do operador: `DIRECTOR_ACERVO_MAX_BYTES`, padrão 10 MiB/candidato,
até 512 MiB. Não há quota global de downloads por conversa: o agente deve selecionar
poucos candidatos relevantes, respeitando o escopo autorizado. Todos os dados ficam
em R:. Sem R: disponível, não há fallback para C:.

O download existente valida tamanho e SHA256/git-blob, espaço livre e diretório,
reutiliza bytes válidos, não sobrescreve arquivo divergente e remove `.part` falho.
O preparo reutiliza a trava por objeto e a trava global da ponte para chamadas ao motor.
Várias conversas podem pesquisar; alterações do editor continuam serializadas.
Não foi implementada edição colaborativa simultânea de cenas.

## SQL v4 e procedência

Migração aditiva/transacional, backup SQLite consistente antes de v1/v2/v3:
`acervo.sqlite3.antes-v4.sqlite3`. O backup anterior não é sobrescrito. O journal
permanece DELETE: WAL não foi habilitado no compartilhamento SMB. SQLite ainda
depende das garantias de bloqueio/armazenamento do share; laboratório não é prova
de confiabilidade desse armazenamento sob toda falha de rede.

| Tabela | Responsabilidade |
|---|---|
| variantes | Modelo, assinatura dos arquivos/dependências, coletor e versão do motor |
| preparacoes | Pedido/sessão, etapas, erro, retomada e resultado da importação |
| metadados | Assunto, valor, unidade, referencial, origem, método e evidência |
| partes_modelo | Caminhos, relações e dados de partes/juntas declaradas |
| capacidades_modelo | Resultado por capacidade, variante, escopo, método e evidência |
| derivados_modelo | Relação original/derivado, hashes, método e perdas |
| anotacoes_acervo | Sugestões/declaracões, sem certificação |

As tabelas preexistentes de modelos, arquivos, instalações, instâncias, receitas,
coletas e registros permanecem. A estrutura aceita superfícies, folgas, massa,
atrito, rigs e animações como metadados tipados, sem preenchê-los artificialmente.
Esta entrega preenche bounds/unidades/eixos/dependências, tipos de juntas declaradas,
manifestos e snapshots da importação. Não extrai automaticamente superfícies úteis,
limites de juntas, rigs, massa ou animações. `derivados_modelo` prepara a persistência;
um coletor automático de conversões ainda não foi implementado.

`acao:verificacao` passou a registrar uma **anotação não validada**. Essa é uma
mudança intencional: strings de versão/evidência enviadas pela LLM não comprovam
teste. As verificações antigas continuam preservadas e aparecem por capacidade,
sem corte nas três últimas; sua vigência de variante não foi demonstrada.
Somente o coletor determinístico deste fluxo escreve medidas e o teste limitado
de dependências da fonte. Não existe `fisica_ok` global.

## Validade e observação compacta

`ficha` com objeto retorna resumo; `assunto` permite geometria, partes, física,
animações, superfícies, importação, origem ou anotações. `detalhe` com `assunto`
também entrega esse recorte, evitando despejar a ficha legada. A busca inclui um recorte compacto.
As leituras conferem hashes das entradas e dependências resolvidas, revisão do
catálogo, versão do coletor/script e Build.version instalado. Dados alterados ficam
obsoletos, sem apagar o histórico; o resumo não oferece dimensões obsoletas como atuais.

As dimensões são AABB mundial do USD, no eixo nativo, default/render e tempo padrão,
em centímetros. Não são envelope animado, escala humana certificada ou bounds do ator.
Juntas do USD são declarações da fonte; não equivalem a juntas Chaos funcionando.
Massa, apoio, rigidez e articulação permanecem desconhecidos até teste próprio.

Importações repetidas recuperam o registro anterior e consultam novamente o motor:
existência/classe de cada malha, bounds e configuração de colisão. Isso não detecta
toda alteração de topologia que preserve bounds/configuração, nem certifica materiais
ou interação física. A consulta offline de importação é explicitamente um snapshot.

## Falha e recuperação

- Queda no download/inspeção: corrigir a causa e repetir o mesmo pedido. Arquivos
  válidos são reutilizados; cada tentativa persiste etapa/erro e histórico em registros,
  preservando o erro anterior depois da retomada.
- Arquivo divergente: revisar origem. Não sobrescrever silenciosamente nem registrar
  a medida anterior como vigente.
- Checkpoint `importando`, inclusive após queda da ponte/SQL: conferir pasta nativa
  retornada e os registros antes de repetir. Não importar em outro destino para esconder
  uma mutação parcial. Não há rollback automático de assets novos após falha.
- Banco indisponível depois do motor: não repetir a operação nativa. Reconciliar os
  registros com o estado real antes de uma retomada manual.
- Restaurar backup exige parar os escritores e autorização para substituir o banco;
  não foi criado mecanismo de restauração automática sobre conexões ativas.

**Limite de segurança:** as validações da API não isolam um terminal com acesso ao
mesmo usuário Windows. Ele ainda pode abrir SQLite ou arquivos diretamente. A skill
orienta não fazer isso; não se afirma que há sandbox de sistema operacional.

## Evidências da implementação

17 testes novos de preparação e 34 regressões dos módulos de acervo/coleta/fontes/
operação: 51 testes distintos aprovados. Incluem migração/backup/rollback,
arquivos e dependências alterados, retomada, identidade entre pedidos, importação
incerta, assets alterados, recusa de SQL/medidas e declarações sem certificação.
São verificações determinísticas; não equivalem a Pedidos Atendidos por uma LLM.

Validação real em cópia consistente do SQL: ArtVIP table 4 e cabinet005, 173.283 bytes
em onze arquivos, baixados para cache global R:/CINF/BD/ArtVIP. Inspeção OpenUSD do
Unreal: 200 × 55,83366 × 80,5 cm e 90 × 50,38784 × 190 cm, respectivamente.
Inventário antes/depois idêntico; sem criação de atores. SQL: quick_check ok,
foreign_key_check vazio. Evidências locais:
`R:/CINF/BD/Director/evolucao-sob-demanda-20261021/`.

Na instalação estável: migração do SQL principal para v4, 14.507 modelos e oito
verificações antigas preservados, table4 importado e reutilizado sem nova importação;
cabinet005 preparado. Quick_check ok, FK check vazio e inventário preservado.

Hermes real, perfil director e ferramentas normais, endpoint local anunciando
`glm-5.3-flash` e substituição por chamada, sem alterar padrão Luna do perfil:

- Sessão `local-2446bd364b9e335a3dcc9b11399a97e08b46b3a49486ec15f8b88fe0e675d992`,
  44,330 s: procurou chair2, baixou 1.583.440 bytes, mediu
  49,13 × 83,53 × 88,89 cm e registrou dados. Três materiais MDL externos ausentes
  bloquearam a importação. Relatou corretamente o bloqueio e não inventou juntas Chaos.
  Aquisição/diagnóstico atendidos; objetivo de importar não atendido por dependências.
- Sessão `local-5b270164741a2c3f48e46c73057ea9cf0040f46068de6e962183b3c3f3f929d6`,
  28,762 s: preparou/importou cabinet005 (sete malhas), repetiu o mesmo pedido e
  reutilizou os assets após conferência nativa. Porém omitiu a chamada `anotar` pedida,
  embora a resposta dissesse que a hipótese de 80 kg ficava anotada. Pedido completo:
  **PARCIAL**. Não transformar sucesso de importação em PA integral.

O caso motivou retorno com ID na gravação da nota e consulta `ficha assunto:anotacoes`
(cinco últimas, texto até 1.000 caracteres, sempre não validado). A skill 0.5.18 exige
conferir essa leitura antes de alegar persistência. Isso não prova que o modelo
deixará de omitir requisitos sem assistência. Issue #4 acompanha a lacuna.

Bounds de malhas isoladas do cabinet005 chegam a 2.540 cm, enquanto a AABB da fonte
montada mede 90 × 50,4 × 190 cm. Referenciais e transformações de montagem diferem:
não concluir erro de escala do conjunto apenas por essa comparação. Importar malhas
não produz automaticamente montagem utilizável/articulada. Essa etapa permanece fora
da entrega; não há prova de armário corretamente montado/posicionado na cena.

O PR #77 permanece a prova anterior, isolada; #78 implementa o fluxo e #79 registra
correções dos retornos/observação. Não foi feito benchmark Qwen Q8/Q4 ou teste de
uma hora com contexto saturado. Evidências de conclusão/correção dirigida ficam
também nas issues #75, #36 e #48.

