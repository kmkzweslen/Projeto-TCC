<script setup>
import { ref } from 'vue'
import { api } from '../api.js'

defineProps({
  erro: { type: String, default: '' },
  servidorOffline: { type: Boolean, default: false },
})
const emit = defineEmits(['limpar-erro'])

const conectando = ref(false)
const erroLocal = ref('')
const mostrarAjuda = ref(false)

async function conectar() {
  emit('limpar-erro')
  erroLocal.value = ''
  conectando.value = true
  try {
    const { authorization_url } = await api.urlDeLogin()
    // Vai para a tela da Meta; ao final ela devolve o usuário para cá já logado.
    window.location.href = authorization_url
  } catch (e) {
    erroLocal.value = e.message
    conectando.value = false
  }
}
</script>

<template>
  <div class="login">
    <section class="lado-apresentacao">
      <div class="marca">
        <img src="/icone.svg" alt="" width="40" height="40" />
        <span>PostaIA</span>
      </div>

      <h1>Do tema ao post publicado, <span class="destaque">em um só lugar.</span></h1>
      <p class="subtitulo">
        Descreva o que você quer divulgar. A IA cria as legendas e as imagens, você escolhe a melhor
        combinação e publica direto no Instagram, sem copiar, baixar ou trocar de ferramenta.
      </p>

      <ol class="passos">
        <li><span>1</span><div><strong>Descreva</strong> o tema, o objetivo, o público e o tom.</div></li>
        <li><span>2</span><div><strong>Gere</strong> opções de legenda e imagem com várias IAs ao mesmo tempo.</div></li>
        <li><span>3</span><div><strong>Escolha</strong> e ajuste o que quiser.</div></li>
        <li><span>4</span><div><strong>Publique</strong> no Instagram com um clique.</div></li>
      </ol>
    </section>

    <section class="lado-acao">
      <div class="cartao cartao-login">
        <h2>Conecte seu Instagram</h2>
        <p class="suave">
          Você vai para a página oficial da Meta (Facebook), autoriza o acesso e volta para cá já conectado.
          Não pedimos sua senha.
        </p>

        <div v-if="erro || erroLocal" class="alerta erro">
          <span>⚠️</span>
          <span>{{ erro || erroLocal }}</span>
        </div>

        <button class="botao botao-primario botao-grande largo" :disabled="conectando" @click="conectar">
          <span v-if="conectando" class="giro"></span>
          <span v-else>📷</span>
          {{ conectando ? 'Abrindo a Meta…' : 'Conectar com Instagram' }}
        </button>

        <div class="o-que-esperar">
          <strong class="pequeno">Na tela da Meta:</strong>
          <ul class="pequeno suave">
            <li>Entre com o Facebook que administra a Página da sua empresa.</li>
            <li>Marque a <strong>Página</strong> e a <strong>conta do Instagram</strong> que quer usar.</li>
            <li>Mantenha as permissões ligadas e clique em <strong>Continuar</strong> até o fim.</li>
          </ul>
        </div>

        <button class="botao-texto pequeno ajuda-botao" @click="mostrarAjuda = !mostrarAjuda">
          {{ mostrarAjuda ? '▾' : '▸' }} Primeira vez? Veja o que precisa antes de conectar
        </button>
        <div v-if="mostrarAjuda" class="ajuda pequeno">
          <p><strong>1. Conta profissional.</strong> No Instagram: Perfil → ☰ → Tipo de conta e ferramentas →
            Mudar para conta profissional (Criador ou Empresa).</p>
          <p><strong>2. Página do Facebook.</strong> Crie uma Página para o seu negócio (pode ter o mesmo nome do perfil).</p>
          <p><strong>3. Ligar os dois.</strong> No Instagram: Editar perfil → Página → Conectar, e escolha a Página.</p>
          <p class="suave">Isso é feito uma única vez. Depois, é só clicar em “Conectar com Instagram”.</p>
        </div>
      </div>

      <p v-if="servidorOffline" class="pequeno aviso-servidor">
        ⚠️ Não consegui falar com o servidor. Verifique se o back-end está rodando.
      </p>
    </section>
  </div>
</template>

<style scoped>
.login {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 1fr;
}

.lado-apresentacao {
  background: var(--gradiente);
  color: #fff;
  padding: 56px 64px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  gap: 28px;
  position: relative;
  overflow: hidden;
}

.lado-apresentacao::after {
  content: '';
  position: absolute;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.08);
  right: -180px;
  bottom: -200px;
}

.marca {
  display: flex;
  align-items: center;
  gap: 12px;
  font-weight: 800;
  font-size: 1.35rem;
}

.marca img {
  border-radius: 12px;
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5);
}

h1 {
  font-size: clamp(2rem, 3.4vw, 2.9rem);
  letter-spacing: -0.03em;
  max-width: 560px;
}

.destaque {
  opacity: 0.85;
}

.subtitulo {
  font-size: 1.08rem;
  opacity: 0.92;
  max-width: 520px;
  margin: 0;
}

.passos {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 14px;
  max-width: 480px;
  position: relative;
  z-index: 1;
}

.passos li {
  display: flex;
  gap: 14px;
  align-items: center;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 14px;
  padding: 12px 16px;
}

.passos li > span {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #fff;
  color: var(--primaria);
  font-weight: 800;
  display: grid;
  place-items: center;
  flex-shrink: 0;
}

.lado-acao {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 40px 32px;
  gap: 16px;
}

.cartao-login {
  width: 100%;
  max-width: 440px;
  display: flex;
  flex-direction: column;
  gap: 18px;
  padding: 32px;
}

.cartao-login h2 {
  font-size: 1.5rem;
}

.cartao-login p {
  margin: 0;
}

.largo {
  width: 100%;
}

.o-que-esperar ul {
  margin: 6px 0 0;
  padding-left: 18px;
  display: grid;
  gap: 4px;
}

.ajuda-botao {
  align-self: flex-start;
  padding-left: 0;
}

.ajuda {
  background: var(--superficie-2);
  border-radius: var(--raio-p);
  padding: 14px 16px;
  display: grid;
  gap: 8px;
}

.ajuda p {
  margin: 0;
}

.aviso-servidor {
  color: var(--aviso);
}

@media (max-width: 900px) {
  .login {
    grid-template-columns: 1fr;
  }
  .lado-apresentacao {
    padding: 40px 28px;
  }
}
</style>
