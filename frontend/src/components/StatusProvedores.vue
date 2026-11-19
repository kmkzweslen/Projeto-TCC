<script setup>
import { onMounted, ref, watch } from 'vue'
import { api } from '../api.js'

const props = defineProps({
  status: { type: Object, default: null },
})

const dados = ref(props.status)
const carregando = ref(false)
const erro = ref('')

watch(
  () => props.status,
  (novo) => {
    if (novo) dados.value = novo
  },
)

async function atualizar() {
  carregando.value = true
  erro.value = ''
  try {
    dados.value = await api.status()
  } catch (e) {
    erro.value = e.message
  } finally {
    carregando.value = false
  }
}

onMounted(() => {
  if (!dados.value) atualizar()
})
</script>

<template>
  <section class="status">
    <div class="titulo">
      <div>
        <h2>Status do sistema</h2>
        <p class="suave">Quais inteligências artificiais e serviços estão configurados no servidor.</p>
      </div>
      <button class="botao botao-secundario" :disabled="carregando" @click="atualizar">↻ Atualizar</button>
    </div>

    <div v-if="erro" class="alerta erro"><span>⚠️</span><span>{{ erro }}</span></div>

    <div v-if="dados" class="grade">
      <div class="cartao">
        <h3>✍️ Legendas (texto)</h3>
        <ul>
          <li v-for="p in dados.texto" :key="p.provedor">
            <span class="ponto" :class="{ ligado: p.configurado }"></span>
            <div>
              <strong>{{ p.provedor }}</strong>
              <span class="suave pequeno">{{ p.modelo }}</span>
            </div>
            <span class="selo" :class="p.configurado ? 'ok' : 'falha'">
              {{ p.configurado ? 'Ativo' : 'Sem chave' }}
            </span>
          </li>
        </ul>
      </div>

      <div class="cartao">
        <h3>🎨 Imagens</h3>
        <ul>
          <li v-for="p in dados.imagem" :key="p.provedor">
            <span class="ponto" :class="{ ligado: p.configurado }"></span>
            <div>
              <strong>{{ p.provedor }}</strong>
              <span class="suave pequeno">{{ p.modelo }}</span>
            </div>
            <span class="selo" :class="p.configurado ? 'ok' : 'falha'">
              {{ p.configurado ? 'Ativo' : 'Sem chave' }}
            </span>
          </li>
        </ul>
      </div>

      <div class="cartao">
        <h3>🔌 Serviços</h3>
        <ul>
          <li>
            <span class="ponto" :class="{ ligado: dados.hospedagem_imagens }"></span>
            <div><strong>Hospedagem de imagens</strong><span class="suave pequeno">ImgBB</span></div>
            <span class="selo" :class="dados.hospedagem_imagens ? 'ok' : 'falha'">
              {{ dados.hospedagem_imagens ? 'Ativo' : 'Desligado' }}
            </span>
          </li>
          <li>
            <span class="ponto" :class="{ ligado: dados.banco_de_dados }"></span>
            <div><strong>Banco de dados</strong><span class="suave pequeno">MongoDB</span></div>
            <span class="selo" :class="dados.banco_de_dados ? 'ok' : 'falha'">
              {{ dados.banco_de_dados ? 'Ativo' : 'Desligado' }}
            </span>
          </li>
          <li>
            <span class="ponto ligado"></span>
            <div><strong>Instagram Graph API</strong><span class="suave pequeno">versão {{ dados.graph_api_version }}</span></div>
          </li>
        </ul>
      </div>
    </div>

    <div v-else-if="carregando" class="grade">
      <div v-for="n in 3" :key="n" class="esqueleto bloco-esqueleto"></div>
    </div>
  </section>
</template>

<style scoped>
.status {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.titulo {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 16px;
}

.titulo h2 {
  font-size: 1.5rem;
}

.titulo p {
  margin: 4px 0 0;
}

.grade {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 16px;
}

h3 {
  font-size: 1.05rem;
  margin-bottom: 12px;
}

ul {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

li {
  display: flex;
  align-items: center;
  gap: 12px;
}

li > div {
  display: flex;
  flex-direction: column;
  line-height: 1.25;
  margin-right: auto;
  min-width: 0;
}

.ponto {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--erro);
  flex-shrink: 0;
}

.ponto.ligado {
  background: var(--sucesso);
  box-shadow: 0 0 0 4px var(--sucesso-claro);
}

.bloco-esqueleto {
  height: 180px;
}
</style>
