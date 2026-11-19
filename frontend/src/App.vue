<script setup>
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { api, expiracaoDoToken, sessao } from './api.js'
import TelaLogin from './components/TelaLogin.vue'
import CriarPost from './components/CriarPost.vue'
import Historico from './components/Historico.vue'
import StatusProvedores from './components/StatusProvedores.vue'

const token = ref(sessao.token)
const usuario = ref(null)
const carregando = ref(true)
const erroLogin = ref('')
const aba = ref('criar')
const status = ref(null)
const servidorOffline = ref(false)

const abas = [
  { id: 'criar', rotulo: 'Criar post' },
  { id: 'historico', rotulo: 'Histórico' },
  { id: 'status', rotulo: 'Status' },
]

const sessaoExpiraEm = computed(() => (token.value ? expiracaoDoToken(token.value) : null))

// Aviso para reconectar quando o token da Meta (≈60 dias) estiver perto de vencer.
const diasParaReconectar = computed(() => {
  const expira = usuario.value?.token_expires_at
  if (!expira) return null
  return Math.floor((new Date(expira) - new Date()) / 86400000)
})

function formatarData(data) {
  return data ? data.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit', year: 'numeric' }) : ''
}

/** Lê o retorno do login da Meta: #token=... (sucesso) ou #erro=... (falha). */
function lerRetornoDoLogin() {
  const hash = window.location.hash.replace(/^#/, '')
  if (!hash) return
  const parametros = new URLSearchParams(hash)
  if (parametros.get('token')) {
    sessao.salvar(parametros.get('token'))
    token.value = parametros.get('token')
  }
  if (parametros.get('erro')) erroLogin.value = parametros.get('erro')
  // Remove o token da barra de endereço (não fica no histórico do navegador).
  history.replaceState(null, '', window.location.pathname + window.location.search)
}

async function carregarUsuario() {
  if (!token.value) return
  try {
    usuario.value = await api.usuarioAtual()
  } catch (e) {
    erroLogin.value = e.message
    sair()
  }
}

function sair() {
  sessao.limpar()
  token.value = null
  usuario.value = null
  aba.value = 'criar'
}

function aoExpirarSessao() {
  erroLogin.value = 'Sua sessão expirou. Conecte o Instagram de novo para continuar.'
  sair()
}

onMounted(async () => {
  window.addEventListener('sessao-expirada', aoExpirarSessao)
  lerRetornoDoLogin()
  api
    .status()
    .then((s) => (status.value = s))
    .catch(() => (servidorOffline.value = true))
  await carregarUsuario()
  carregando.value = false
})

onBeforeUnmount(() => window.removeEventListener('sessao-expirada', aoExpirarSessao))
</script>

<template>
  <div v-if="carregando" class="carregando-tela">
    <span class="giro escuro"></span>
  </div>

  <TelaLogin v-else-if="!usuario" :erro="erroLogin" :servidor-offline="servidorOffline" @limpar-erro="erroLogin = ''" />

  <div v-else class="app">
    <header class="topo">
      <div class="topo-conteudo">
        <div class="marca">
          <img src="/icone.svg" alt="" width="34" height="34" />
          <span>PostaIA</span>
        </div>

        <nav class="abas">
          <button
            v-for="item in abas"
            :key="item.id"
            class="aba"
            :class="{ ativa: aba === item.id }"
            @click="aba = item.id"
          >
            {{ item.rotulo }}
          </button>
        </nav>

        <div class="conta">
          <div class="avatar">{{ (usuario.instagram_username || '?').charAt(0).toUpperCase() }}</div>
          <div class="conta-texto">
            <strong>@{{ usuario.instagram_username }}</strong>
            <span class="suave pequeno" v-if="sessaoExpiraEm">sessão até {{ formatarData(sessaoExpiraEm) }}</span>
          </div>
          <button class="botao-texto pequeno" @click="sair">Sair</button>
        </div>
      </div>
    </header>

    <main class="conteudo">
      <div v-if="diasParaReconectar !== null && diasParaReconectar <= 7" class="alerta aviso aviso-topo">
        <span>⚠️</span>
        <span>
          A autorização do Instagram vence em {{ Math.max(diasParaReconectar, 0) }} dia(s).
          Clique em <strong>Sair</strong> e conecte de novo para continuar publicando.
        </span>
      </div>

      <KeepAlive>
        <CriarPost v-if="aba === 'criar'" :usuario="usuario" />
      </KeepAlive>
      <Historico v-if="aba === 'historico'" />
      <StatusProvedores v-if="aba === 'status'" :status="status" />
    </main>

    <footer class="rodape suave pequeno">
      Conteúdo gerado por IA e revisado por você antes de publicar · TCC
    </footer>
  </div>
</template>

<style scoped>
.carregando-tela {
  min-height: 100vh;
  display: grid;
  place-items: center;
}

.topo {
  position: sticky;
  top: 0;
  z-index: 10;
  background: rgba(255, 255, 255, 0.85);
  backdrop-filter: blur(12px);
  border-bottom: 1px solid var(--borda);
}

.topo-conteudo {
  max-width: 1180px;
  margin: 0 auto;
  padding: 12px 24px;
  display: flex;
  align-items: center;
  gap: 24px;
}

.marca {
  display: flex;
  align-items: center;
  gap: 10px;
  font-weight: 800;
  font-size: 1.2rem;
  letter-spacing: -0.02em;
}

.abas {
  display: flex;
  gap: 4px;
  background: var(--superficie-2);
  padding: 4px;
  border-radius: 999px;
  margin: 0 auto;
}

.aba {
  border: none;
  background: none;
  padding: 8px 18px;
  border-radius: 999px;
  font-weight: 600;
  color: var(--texto-suave);
  transition: all 0.15s;
}

.aba.ativa {
  background: var(--superficie);
  color: var(--texto);
  box-shadow: 0 1px 4px rgba(29, 27, 44, 0.12);
}

.conta {
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  background: var(--gradiente);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
}

.conta-texto {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
}

.conteudo {
  max-width: 1180px;
  margin: 0 auto;
  padding: 32px 24px 48px;
}

.aviso-topo {
  margin-bottom: 20px;
}

.rodape {
  text-align: center;
  padding: 24px;
}

@media (max-width: 820px) {
  .topo-conteudo {
    flex-wrap: wrap;
    gap: 12px;
  }
  .abas {
    order: 3;
    width: 100%;
    justify-content: center;
  }
  .conta-texto span {
    display: none;
  }
}
</style>
