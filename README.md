# API de Conteúdo com IA para Instagram

Back-end do TCC *Ferramenta Integrada de IA Generativa para Criação e Publicação de
Conteúdo no Instagram*. A partir de sete parâmetros, a API:

1. monta o prompt de legenda no framework **CO-STAR** (Context, Objective, Style,
   Tone, Audience, Response), com **uma única CTA** escolhida pelo objetivo;
2. gera, **em paralelo**, legendas (OpenAI GPT e Google Gemini) e imagens
   (OpenAI GPT Image e Stability AI);
3. converte as imagens para JPEG e as hospeda no ImgBB (requisitos da Graph API);
4. verifica cada legenda contra as regras do componente Response (conformidade);
5. publica no feed do Instagram o par imagem + legenda **escolhido pelo usuário**.

## Como rodar

```bash
python -m venv venv
venv\Scripts\activate            # Windows
pip install -r requirements.txt
copy .env.example .env           # e preencha as chaves
uvicorn main:app --reload
```

Documentação interativa: http://127.0.0.1:8000/docs

## Endpoints

| Método | Rota | Função |
|---|---|---|
| GET | `/api/auth/instagram/login` | URL de autorização OAuth (Facebook Login) |
| GET | `/api/auth/instagram/callback` | Troca o código por token e emite o JWT |
| GET | `/api/auth/me` | Usuário autenticado |
| GET | `/api/status` | Provedores configurados e modelos em uso |
| POST | `/api/` | Gera legendas e imagens (requer `Authorization: Bearer <jwt>`) |
| POST | `/api/instagram/publicar_feed` | Publica o par escolhido (requer JWT) |
| GET | `/api/historico` | Gerações e publicações do usuário (requer JWT) |
| GET | `/health` | Verificação de disponibilidade |

Com `FRONTEND_URL` configurado, o callback envia o usuário de volta ao
front-end: `FRONTEND_URL/#token=<jwt>` em caso de sucesso ou
`FRONTEND_URL/#erro=<mensagem>` em caso de falha (o token vai no fragmento,
não na query string). Para receber o JSON, como nos testes pelo `/docs`, use
`?redirect=false` ou deixe `FRONTEND_URL` vazio.

A sessão (JWT) dura `JWT_EXPIRE_HOURS` horas: o padrão é 720 (30 dias) e o
máximo é 1440 (60 dias), que é a validade do token de longa duração da Meta.

O front-end (Vue 3 + Vite) está em `frontend/`; veja `frontend/README.md`.

### Exemplo de geração

```json
POST /api/
{
  "tema": "lançamento da coleção de verão",
  "tipo": "imagem",
  "objetivo": "vender produto",
  "publico": "mulheres de 20 a 35 anos",
  "tom": "descontraído",
  "rede_alvo": "Instagram",
  "formato": "post de feed com imagem única"
}
```

Cada item de `legendas` traz `provedor`, `modelo`, `legenda`, `tempo_s` e
`conformidade` (caracteres, emojis, hashtags, CTAs detectadas e o resultado de
cada regra). Cada item de `imagens` traz `url_publica` e `tempo_s`. Falhas e
estouros de tempo aparecem em `imagens_falhas` / `legendas_falhas`, sem impedir
o retorno das demais opções.

### Publicação

```json
POST /api/instagram/publicar_feed
{ "image_url": "https://i.ibb.co/...", "caption": "...", "conteudo_id": "..." }
```

Fluxo: valida a URL e a legenda → consulta o limite de publicações em 24 h →
cria o contêiner → consulta `status_code` até `FINISHED` → publica → retorna o
`permalink`. Cada tentativa é gravada na coleção `publicacoes`.

## Estrutura

```
app/
  api/            rotas (auth.py, conteudo.py)
  core/config.py  todas as variáveis de ambiente
  schemas/        entrada (CO-STAR), respostas e auth
  services/
    text_generators/   gpt.py, gemini.py        (adaptadores REST)
    image_generators/  openai_image.py, stability_ai.py
    multi_model_service.py   orquestração paralela
    instagram_service.py     publicação com consulta de status
    cloud_storage_service.py JPEG + ImgBB
    auth_service.py / user_service.py / database_service.py
  utils/
    prompt_engineering.py  CO-STAR, CTA e regras da legenda
    conformidade.py        verificação da legenda (critério C5)
    criptografia.py        tokens da Meta criptografados no banco
    imagem.py              conversão para JPEG
scripts/avaliar_cenarios.py  avaliação dos cenários S1–S3 (CSV + resumo)
tests/                       testes automatizados (pytest)
```

Cada provedor é um adaptador com a mesma interface (`disponivel()`, `modelo()`,
`gerar_texto()`/`gerar_imagem()`). Para trocar de modelo, basta alterar o `.env`.

## Testes e avaliação

```bash
pip install -r requirements-dev.txt
python -m pytest                                   # testes, sem chamar APIs reais
python -m scripts.avaliar_cenarios --repeticoes 5  # cenários S1–S3 com as APIs reais
```

O script grava um CSV (separador `;`, abre direto no Excel) e imprime, por
cenário e provedor, a taxa de sucesso, o tempo médio, o desvio-padrão e as
legendas conformes, que são os dados da tabela de validação técnica do artigo.
