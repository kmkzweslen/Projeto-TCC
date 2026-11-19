<script setup>
import { onMounted, ref } from 'vue'
import { api, ErroSessao } from '../api.js'

const itens = ref([])
const carregando = ref(true)
const erro = ref('')

async function carregar() {
  carregando.value = true
  erro.value = ''
  try {
    const dados = await api.historico(30)
    itens.value = dados.itens
  } catch (e) {
    if (!(e instanceof ErroSessao)) erro.value = e.message
  } finally {
    carregando.value = false
  }
}

function dataHora(iso) {
  if (!iso) return ''
  // O back-end grava em UTC; sem fuso explícito, tratamos como UTC.
  const data = new Date(/[zZ]|[+-]\d\d:?\d\d$/.test(iso) ? iso : `${iso}Z`)
  return data.toLocaleString('pt-BR', { dateStyle: 'short', timeStyle: 'short' })
}

function publicada(item) {
  return item.publicacoes.find((p) => p.status === 'success')
}

function segundosTexto(valor) {
  return typeof valor === 'number' ? `${valor.toFixed(1).replace('.', ',')} s` : '—'
}

onMounted(carregar)
</script>

<template>
  <section class="historico">
    <div class="titulo">
      <div>
        <h2>Histórico</h2>
        <p class="suave">Tudo o que você gerou e publicou. Os dados ficam salvos no banco do sistema.</p>
      </div>
      <button class="botao botao-secundario" :disabled="carregando" @click="carregar">↻ Atualizar</button>
    </div>

    <div v-if="erro" class="alerta erro"><span>⚠️</span><span>{{ erro }}</span></div>

    <div v-if="carregando" class="lista">
      <div v-for="n in 3" :key="n" class="esqueleto item-esqueleto"></div>
    </div>

    <div v-else-if="!itens.length && !erro" class="cartao vazio">
      <div class="vazio-icone">🗂️</div>
      <p><strong>Nada por aqui ainda.</strong></p>
      <p class="suave">Quando você gerar um post, ele aparece nesta lista.</p>
    </div>

    <div v-else class="lista">
      <article v-for="item in itens" :key="item.id" class="cartao item">
        <div class="miniaturas">
          <img
            v-for="img in item.imagens || []"
            :key="img.url_publica"
            :src="img.url_publica"
            :alt="`Imagem de ${img.provedor}`"
            loading="lazy"
          />
          <div v-if="!(item.imagens || []).length" class="sem-imagem suave pequeno">sem imagem</div>
        </div>

        <div class="detalhes">
          <div class="linha-topo">
            <span class="suave pequeno">{{ dataHora(item.criado_em) }}</span>
            <a
              v-if="publicada(item)?.permalink"
              class="selo ok"
              :href="publicada(item).permalink"
              target="_blank"
              rel="noopener"
            >
              ✓ Publicado ↗
            </a>
            <span v-else-if="publicada(item)" class="selo ok">✓ Publicado</span>
            <span v-else-if="item.publicacoes.length" class="selo falha">✕ Falha ao publicar</span>
            <span v-else class="selo">Não publicado</span>
          </div>

          <h3>{{ item.tema }}</h3>
          <p class="pequeno suave">
            Objetivo: {{ item.objetivo }} · Público: {{ item.publico }} · Tom: {{ item.tom }}
          </p>

          <p v-if="publicada(item)?.caption" class="legenda pequeno">{{ publicada(item).caption }}</p>

          <p class="pequeno suave metricas">
            {{ (item.imagens || []).length }} imagem(ns) · {{ (item.legendas || []).length }} legenda(s) ·
            geração em {{ segundosTexto(item.tempo_total_s) }}
            <template v-if="publicada(item)"> · publicação em {{ segundosTexto(publicada(item).tempo_s) }}</template>
          </p>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.historico {
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

.lista {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.item-esqueleto {
  height: 140px;
}

.item {
  display: flex;
  gap: 20px;
  padding: 18px;
}

.miniaturas {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}

.miniaturas img,
.sem-imagem {
  width: 104px;
  height: 104px;
  border-radius: var(--raio-p);
  object-fit: cover;
  background: var(--superficie-2);
}

.sem-imagem {
  display: grid;
  place-items: center;
}

.detalhes {
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-width: 0;
}

.detalhes p {
  margin: 0;
}

.linha-topo {
  display: flex;
  gap: 10px;
  align-items: center;
}

a.selo {
  text-decoration: none;
}

.legenda {
  background: var(--superficie-2);
  border-radius: var(--raio-p);
  padding: 10px 12px;
  white-space: pre-wrap;
}

.vazio {
  text-align: center;
  padding: 48px;
}

.vazio p {
  margin: 4px 0;
}

.vazio-icone {
  font-size: 2.4rem;
}

@media (max-width: 700px) {
  .item {
    flex-direction: column;
  }
}
</style>
