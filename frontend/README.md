# PostaIA: front-end (Vue 3 + Vite)

Interface web da ferramenta. Ela consome a API FastAPI desta pasta
(`Projeto-TCC`) e implementa o fluxo integrado de 4 ações:

1. **Descrever**: tema, objetivo, público e tom (entradas do prompt CO-STAR).
2. **Gerar**: legendas e imagens de todos os provedores ao mesmo tempo.
3. **Escolher**: a imagem e a legenda (a legenda pode ser editada).
4. **Publicar**: direto no feed do Instagram.

Telas: login, criar post, histórico e status dos provedores.

## Requisitos

- Node.js **20.19 ou mais recente** (confira com `node -v`)
- Back-end rodando em `http://127.0.0.1:8000`, com `FRONTEND_URL=http://localhost:5173` no `.env` do back-end

## Como rodar

```bash
cd frontend
npm install      # só na primeira vez
npm run dev      # abre em http://localhost:5173
```

Para mudar o endereço da API, copie `.env.example` para `.env` e altere `VITE_API_URL`.

## Como funciona o login

1. O botão **Conectar com Instagram** pede a URL de autorização ao back-end
   (`GET /api/auth/instagram/login`) e leva o usuário à página oficial da Meta.
2. Ao final, a Meta chama o callback do back-end, que troca o código pelo token,
   vincula a conta e redireciona para `http://localhost:5173/#token=<jwt>`.
   Em caso de erro, redireciona para `#erro=<mensagem>`.
3. O front-end guarda o token no navegador e apaga o `#token` da barra de endereço.

A sessão dura 30 dias (`JWT_EXPIRE_HOURS` no back-end, até 60 dias). Quando a
autorização da Meta estiver perto de vencer, aparece um aviso para reconectar.

## Estrutura

```
src/
  api.js                       chamadas à API, token e mensagens de erro
  App.vue                      topo, abas e leitura do retorno do login
  style.css                    estilos globais (cores, botões, campos)
  components/
    TelaLogin.vue              tela inicial e botão "Conectar com Instagram"
    CriarPost.vue              formulário → geração → escolha → publicação
    PreviaInstagram.vue        prévia aproximada do post no feed
    ConformidadeLegenda.vue    regras da legenda verificadas pelo back-end
    Historico.vue              gerações e publicações anteriores
    StatusProvedores.vue       IAs e serviços configurados
```
