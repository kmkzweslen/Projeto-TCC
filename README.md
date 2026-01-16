# API de Geração de Conteúdo para Instagram 🚀

Sistema automatizado para gerar imagens e textos para Instagram usando LLMs (GPT-3.5 e DALL-E 3) com publicação automática.

## ✨ Novidades - Upload Automático!

**Agora 100% automático!** Não é mais necessário usar ngrok manualmente.

- ✅ Imagens são automaticamente enviadas para cloud storage (Cloudinary ou ImgBB)
- ✅ URLs públicas geradas instantaneamente
- ✅ Pronto para publicar no Instagram sem intervenção manual

---

## 🚀 Como rodar a aplicação

### 1. Configurar ambiente virtual

```bash
python -m venv venv
venv\Scripts\activate
```

### 2. Instalar dependências

```bash
pip install -r requirements.txt
```

### 3. Configurar variáveis de ambiente

Copie o arquivo `.env.example` para `.env` e configure:

```env
# OpenAI (Obrigatório - usado por DALL-E, GPT-3.5 e GPT-4)
OPENAI_API_KEY=sua_chave_aqui

# Instagram
IG_USER_ID=seu_id_aqui
APP_ID=seu_app_id
APP_SECRET=seu_secret
USER_ACCESS_TOKEN=seu_token

# Cloud Storage (escolha Cloudinary OU ImgBB)
CLOUDINARY_CLOUD_NAME=seu_cloud_name
CLOUDINARY_API_KEY=sua_api_key
CLOUDINARY_API_SECRET=seu_api_secret
USE_CLOUDINARY=true

# Modelos Opcionais (configure apenas os que desejar usar)
# Leonardo.ai (desabilitado - serviço pago)
# LEONARDO_API_KEY=sua_chave_leonardo

# Stability AI (API oficial) - geração de imagens
STABILITY_AI_API_KEY=sk-seu_token_stability_ai

# Stable Diffusion (Replicate) - alternativa ao Midjourney (opcional)
# Obtenha sua chave em: https://replicate.com/account/api-tokens
REPLICATE_API_TOKEN=r8_seu_token_replicate

# Anthropic Claude (para legendas)
ANTHROPIC_API_KEY=sua_chave_anthropic

# Google Gemini (para legendas)
GEMINI_API_KEY=sua_chave_gemini

# MongoDB (para salvar imagens e legendas geradas)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=prototipo
```

📖 **Guia completo de configuração de modelos de imagem:** Veja `GUIA_CONFIGURAR_MODELOS_IMAGEM.md`

📖 **Guia completo de configuração:** Veja `SETUP_CLOUD_STORAGE.md`

### 4. Rodar a aplicação

```bash
uvicorn main:app --reload
```

### 5. Acessar a documentação

```
http://127.0.0.1:8000/docs
```

---

## ✨ NOVO: Sistema Multi-Modelo!

**Agora o sistema suporta múltiplos modelos de IA!** 

Quando você faz uma requisição, **todos os modelos configurados** geram conteúdo simultaneamente:
- **Imagens**: DALL-E 3, Stable Diffusion, Gemini/Nano Banana
- **Legendas**: GPT-3.5, GPT-4, Claude, Gemini

Você recebe **todas as opções** e escolhe a melhor combinação!

📖 **Veja o guia completo**: `MULTI_MODELO_GUIDE.md`

---

## 📡 Endpoints Disponíveis

### 1. Gerar Conteúdo com Todos os Modelos

**POST** `/api/`

Gera automaticamente imagens e legendas usando **TODOS os modelos configurados** e faz upload para cloud storage.

**Exemplo de requisição:**

```json
{
  "tema": "beleza",
  "tipo": "imagem",
  "objetivo": "atrair seguidores",
  "publico": "mulheres solteiras entre 20 e 30 anos",
  "tom": "casual",
  "rede_alvo": "Instagram",
  "formato": "carrossel"
}
```

**Resposta (múltiplas opções):**

```json
{
  "tipo": "imagem",
  "imagens": [
    {
      "modelo": "dalle-3",
      "url_publica": "https://res.cloudinary.com/...",
      "status": "success"
    },
    {
      "modelo": "stable-diffusion",
      "url_publica": "https://res.cloudinary.com/...",
      "status": "success"
    }
  ],
  "legendas": [
    {
      "modelo": "gpt-3.5-turbo",
      "legenda": "✨ Sua legenda criativa aqui...",
      "status": "success"
    },
    {
      "modelo": "gpt-4",
      "legenda": "💫 Outra legenda ainda melhor...",
      "status": "success"
    },
    {
      "modelo": "claude",
      "legenda": "🌟 Mais uma opção criativa...",
      "status": "success"
    }
  ],
  "total_combinacoes": 6
}
```

### 2. Publicar no Instagram

**POST** `/api/instagram/publicar_feed`

Publica a imagem e legenda no feed do Instagram. Use este endpoint após gerar conteúdo e escolher a imagem e legenda desejadas.

```json
{
  "image_url": "https://res.cloudinary.com/...",
  "caption": "Sua legenda aqui"
}
```

---

## 🎯 Fluxo Completo Automatizado

```
Usuário → Parâmetros → DALL-E 3 → Cloud Storage → URL Pública → Instagram
                     ↓
                  GPT-3.5 → Legenda
```

**Zero intervenção manual! 🎉**

---

## 📚 Documentação Adicional

- **`MULTI_MODELO_GUIDE.md`** - 🆕 **GUIA COMPLETO: Sistema Multi-Modelo - Como usar múltiplos modelos de IA**
- **`FLUXO_COMPLETO_CODIGO.md`** - 🚀 **Guia passo a passo: Como usar o código (copiar e colar)**
- **`COMO_PUBLICAR_NO_FEED.md`** - 📤 **Guia completo: Como publicar no Instagram após gerar conteúdo**
- **`PROCESSAMENTO_IMAGENS.md`** - 🖼️ **Como funciona o download e conversão de imagens para JPG**
- **`USANDO_IMGBB.md`** - 🆓 **Guia de compatibilidade e uso do ImgBB (100% gratuito)**
- **`SETUP_CLOUD_STORAGE.md`** - Guia completo de configuração do cloud storage


---

## 🛠️ Tecnologias

- **FastAPI** - Framework web
- **LangChain** - Orquestração de LLMs (usado para TODAS as operações de texto)
  - **langchain-openai** - GPT-3.5/GPT-4 para legendas
  - **langchain-anthropic** - Claude para legendas
  - **langchain-google-genai** - Gemini para legendas
- **OpenAI** - DALL-E 3 para geração de imagens (via cliente direto, pois LangChain não suporta DALL-E)
- **Stable Diffusion** (via Replicate) - Geração de imagens versátil
- **Cloudinary/ImgBB** - Cloud storage para imagens
- **Facebook Graph API** - Publicação no Instagram

---

## 📝 Próximas Funcionalidades

- [ ] Sistema de aprovação humana
- [ ] Interface web para visualização
- [ ] Banco de dados para histórico
- [ ] Agendamento de posts
- [ ] Suporte para múltiplas contas
- [ ] Suporte para Stories e Reels

