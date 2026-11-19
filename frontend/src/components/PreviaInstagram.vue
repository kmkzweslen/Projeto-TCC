<script setup>
// Prévia aproximada de como o post aparece no feed (não é a interface oficial).
import { computed } from 'vue'

const props = defineProps({
  usuario: { type: String, default: 'seu_perfil' },
  imagem: { type: String, default: '' },
  legenda: { type: String, default: '' },
})

// Destaca as hashtags na prévia, como no aplicativo.
const partes = computed(() =>
  (props.legenda || '').split(/(#[\p{L}\p{N}_]+)/u).map((texto) => ({
    texto,
    hashtag: texto.startsWith('#'),
  })),
)
</script>

<template>
  <div class="previa">
    <div class="previa-topo">
      <div class="avatar">{{ usuario.charAt(0).toUpperCase() }}</div>
      <strong>{{ usuario }}</strong>
      <span class="pontos">•••</span>
    </div>

    <div class="previa-imagem">
      <img v-if="imagem" :src="imagem" alt="Imagem escolhida para o post" />
      <div v-else class="sem-imagem suave pequeno">Escolha uma imagem</div>
    </div>

    <div class="previa-acoes" aria-hidden="true">
      <span>♡</span><span>💬</span><span>➤</span><span class="salvar">🔖</span>
    </div>

    <p class="previa-legenda">
      <strong>{{ usuario }}</strong>
      <template v-if="legenda">
        <span v-for="(parte, i) in partes" :key="i" :class="{ hashtag: parte.hashtag }">{{ parte.texto }}</span>
      </template>
      <span v-else class="suave"> Escolha uma legenda</span>
    </p>
  </div>
</template>

<style scoped>
.previa {
  background: #fff;
  border: 1px solid var(--borda);
  border-radius: var(--raio);
  overflow: hidden;
  box-shadow: var(--sombra);
}

.previa-topo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  font-size: 0.9rem;
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: var(--gradiente);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 700;
  font-size: 0.85rem;
}

.pontos {
  margin-left: auto;
  color: var(--texto-suave);
  letter-spacing: 1px;
}

.previa-imagem {
  aspect-ratio: 1 / 1;
  background: var(--superficie-2);
}

.previa-imagem img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}

.sem-imagem {
  height: 100%;
  display: grid;
  place-items: center;
}

.previa-acoes {
  display: flex;
  gap: 14px;
  padding: 10px 14px 4px;
  font-size: 1.2rem;
}

.salvar {
  margin-left: auto;
}

.previa-legenda {
  margin: 0;
  padding: 4px 14px 14px;
  font-size: 0.9rem;
  white-space: pre-wrap;
  word-break: break-word;
}

.previa-legenda strong {
  margin-right: 6px;
}

.hashtag {
  color: #2b59c3;
}
</style>
