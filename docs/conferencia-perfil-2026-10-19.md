# Conferência do perfil dentro do Hermes — 19/10/2026

Durante o ensaio de cozinha, o GLM executou o comando documentado
`python hermes/instalar_perfil.py director --conferir`. O retorno dizia SOUL/skill
ausentes, embora os arquivos estivessem instalados e a skill tivesse sido lida.

Causa reproduzida: o Hermes passa `HERMES_HOME` apontando para
`.../profiles/director`; `pasta_do_perfil` tratava-o como raiz global e acrescentava
`profiles/director` outra vez. O erro do caminho não é prova de skill desatualizada.

A resolução agora reconhece uma home de perfil e procura o perfil solicitado sob
a raiz correspondente. Também funciona quando o comando parte de outro perfil e
quando HERMES_HOME aponta à raiz global. Não instala nem sobrescreve nada em `--conferir`.

Quatro testes de contrato: dois falhavam antes da correção; os quatro passam depois.
Conferência real com ambiente de perfil aplicada à candidata mostra os mesmos hashes
dos templates instalados. Não se mudou a política de consentimento, o modelo ou as skills.

## Achado separado: escrita intermitente

Nesta mesma sessão CLI, uma chamada de write_file falhou com `No shell found` em
20,171 s; a repetição imediata gravou e verificou o arquivo. Portanto #6 também pode
ocorrer fora do aplicativo. Em processo isolado, 30 descobertas nativas de bash passaram
(máximo 0,125 s); isso não reproduz a condição de falha do gateway e não encerra #6.

O código instalado `pm.shell._bash_starts` testa cada candidato com subprocesso de até
5 s e trata timeout/erro como candidato inutilizável; `LocalEnvironment._run_bash`
refaz a descoberta ao executar comandos. O tempo de 20 s é compatível com vários probes
vencendo o prazo, mas não capturamos os códigos/tempos individuais daquela falha.
Não declarar ausência de bash, PATH errado ou falta de permissões como causa provada.
Não foi aplicado cache ou monkeypatch global para esconder o erro; outros perfis preservados.
