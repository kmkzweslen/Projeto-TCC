// Comunicação com o back-end (FastAPI).
// Todas as chamadas passam por `requisicao`, que coloca o token, trata erros
// e transforma as mensagens da API em texto legível para o usuário.

const BASE = (import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000').replace(/\/$/, '')
const CHAVE_TOKEN = 'postaia_token'

export const sessao = {
  get token() {
    try {
      return localStorage.getItem(CHAVE_TOKEN)
    } catch {
      return null
    }
  },
  salvar(token) {
    try {
      localStorage.setItem(CHAVE_TOKEN, token)
    } catch {
      /* navegador sem localStorage: a sessão dura só até recarregar */
    }
  },
  limpar() {
    try {
      localStorage.removeItem(CHAVE_TOKEN)
    } catch {
      /* ignorado */
    }
  },
}

/** Data de expiração do JWT (campo exp), sem validar a assinatura. */
export function expiracaoDoToken(token) {
  try {
    const base64 = token.split('.')[1].replace(/-/g, '+').replace(/_/g, '/')
    const payload = JSON.parse(atob(base64.padEnd(base64.length + ((4 - (base64.length % 4)) % 4), '=')))
    return payload.exp ? new Date(payload.exp * 1000) : null
  } catch {
    return null
  }
}

export class ErroSessao extends Error {}

function mensagemDeErro(corpo, status) {
  const detalhe = corpo?.detail ?? corpo
  if (!detalhe) return `Erro ${status} ao falar com o servidor.`
  if (typeof detalhe === 'string') return detalhe
  // Erros de validação do FastAPI/Pydantic: lista de { loc, msg }
  if (Array.isArray(detalhe)) {
    return detalhe
      .map((d) => `${(d.loc || []).filter((p) => p !== 'body').join('.')}: ${d.msg}`)
      .join(' · ')
  }
  // Erros de publicação: { error, etapa, detalhes }
  if (detalhe.error) {
    return detalhe.etapa ? `${detalhe.error} (etapa: ${detalhe.etapa})` : detalhe.error
  }
  return JSON.stringify(detalhe)
}

async function requisicao(caminho, { metodo = 'GET', corpo, autenticar = true } = {}) {
  const cabecalhos = { Accept: 'application/json' }
  if (corpo !== undefined) cabecalhos['Content-Type'] = 'application/json'
  if (autenticar && sessao.token) cabecalhos.Authorization = `Bearer ${sessao.token}`

  let resposta
  try {
    resposta = await fetch(`${BASE}${caminho}`, {
      method: metodo,
      headers: cabecalhos,
      body: corpo !== undefined ? JSON.stringify(corpo) : undefined,
    })
  } catch {
    throw new Error(
      `Não foi possível falar com o servidor em ${BASE}. Verifique se o back-end (uvicorn) está rodando.`,
    )
  }

  let dados = null
  try {
    dados = await resposta.json()
  } catch {
    /* resposta sem JSON */
  }

  if (resposta.status === 401 && autenticar) {
    sessao.limpar()
    window.dispatchEvent(new Event('sessao-expirada'))
    throw new ErroSessao('Sua sessão expirou. Conecte o Instagram de novo.')
  }
  if (!resposta.ok) throw new Error(mensagemDeErro(dados, resposta.status))
  return dados
}

export const api = {
  status: () => requisicao('/api/status', { autenticar: false }),
  urlDeLogin: () => requisicao('/api/auth/instagram/login', { autenticar: false }),
  usuarioAtual: () => requisicao('/api/auth/me'),
  gerar: (dados) => requisicao('/api/', { metodo: 'POST', corpo: dados }),
  publicar: (dados) => requisicao('/api/instagram/publicar_feed', { metodo: 'POST', corpo: dados }),
  historico: (limite = 20) => requisicao(`/api/historico?limite=${limite}`),
}
