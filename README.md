# API de Geração de Conteúdo para Instagram 🚀

Sistema automatizado para gerar imagens e textos para Instagram usando LLMs (GPT-3.5 e DALL-E 3) com publicação automática.

## ✨ Novidades - Upload Automático!

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

Copie o conteúdo para `.env` e configure:

```env
# OpenAI (Obrigatório - usado por DALL-E, GPT-3.5 e GPT-4)
OPENAI_API_KEY=sua_chave_aqui

# Instagram
IG_USER_ID=seu_id_aqui
APP_ID=seu_app_id
APP_SECRET=seu_secret
USER_ACCESS_TOKEN=seu_token

# Cloud Storage ( ImgBB)

# Stability AI (API oficial) - geração de imagens
STABILITY_AI_API_KEY=sk-seu_token_stability_ai

# Anthropic Claude (para legendas)
ANTHROPIC_API_KEY=sua_chave_anthropic

# Google Gemini (para legendas)
GEMINI_API_KEY=sua_chave_gemini

# MongoDB (para salvar imagens e legendas geradas)
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DB_NAME=prototipo
```

📖 **Guia completo de configuração de modelos de imagem:** Veja `GUIA_CONFIGURAR_MODELOS_IMAGEM.md`

### 4. Rodar a aplicação

```bash
uvicorn main:app --reload
```

### 5. Acessar a documentação

```
http://127.0.0.1:8000/docs
```

---

## Sistema Multi-Modelo!

Quando você faz uma requisição, **todos os modelos configurados** geram conteúdo simultaneamente:
- **Imagens**: DALL-E 3, Stabality, 
- **Legendas**: GPT-3.5, GPT-4, Claude, Gemini

Você recebe **todas as opções** e escolhe a melhor combinação!

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
