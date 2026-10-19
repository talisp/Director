# Pedidos Atendidos pelo Hermes/GLM — 19/10/2026

Perfil Director, instalação fixa publicada, GLM-5.3-Flash no endpoint local. Sessão
`local-b8e8d54cc97e5116e166ce59b439155c9e717ccfe52827a0754038be2454401c`.
Cena própria `glm_pa_20261019`, inicialmente estar 4,6×4,2 m e mesa 1,4×0,8×0,75 m.
Critérios definidos antes, conferidos independentemente por inventário, planta e medidas nativas.

| Pedido | PA | Tempo do agente | Prova |
|---|---|---:|---|
| Cozinha 3×3 m anexa a leste, sem mesa nova, passagem livre 1,2 m | ATENDIDO | 517,660 s | Largura livre medida 120 cm, dimensões 300×300, rotas nos dois sentidos e caminhada; mesa/estar preservados |
| Ampliar cozinha a 3,5×3 m e mesa a 1,8×1 m, preservando centro/altura/rotação | ATENDIDO | 247,332 s | Dimensões corretas; mesmo caminho de ator e centro/rotação da mesa, passagem e rotas preservadas |
| Abrir a porta da cozinha a 90° | NÃO ATENDIDO: folha inexistente | 35,596 s | Detectou passagem sem folha, perguntou antes de criar; planta/inventário/navegação sem mutação |

O terceiro caso é tratamento correto de ausência, não uma porta aberta. Não anunciar 3/3.
No primeiro, uma rota adicional próxima do canto falhou no destino da malha grossa; o operador
escolheu ponto interior e manteve a tolerância. Caminho principal da conexão já era válido.
No segundo, primeira verificação aprovada, sete chamadas. Não se afrouxou critério para passar.

A escrita de arquivo falhou uma vez com `No shell found` em 20,171 s e funcionou ao repetir.
Isso reproduz #6 também na CLI. Trinta probes isolados depois passaram; não foi capturada a
causa individual da falha. Não aplicar remendo de permissões sem evidência.
A conferência falsa de perfil expôs um defeito separado, corrigido/publicado no PR62.

Depois dos testes, `L_sala` voltou com inventário/navegação idênticos e sem Play/pacotes pendentes.
Não houve revisão visual desses pedidos: evidência é objetiva, não apreciação da aparência.
Logs locais: `work/pa-20261019`, incluindo conferências independentes e restauração.
Contadores reportados pelo Hermes não devem ser somados/subtraídos ingenuamente entre recargas
do perfil; não representam medição confiável do custo líquido.

Esta amostra prova dois pedidos principais e preservação local, não generalização de casas ou
resolução de toda a #4. Ainda faltam variações adversariais e revisão de completude com limite.
