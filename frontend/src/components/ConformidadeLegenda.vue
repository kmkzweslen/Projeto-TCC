<script setup>
// Mostra as regras da legenda (componente "Response" do CO-STAR) verificadas
// pelo back-end em app/utils/conformidade.py.
defineProps({
  conformidade: { type: Object, default: null },
  compacto: { type: Boolean, default: false },
})

const ROTULOS = {
  tamanho: 'Tamanho',
  emojis: 'Emojis',
  hashtags: 'Hashtags',
  hashtags_no_final: 'Hashtags no final',
  cta_unica: 'CTA única',
  sem_preambulo: 'Sem introdução',
}
</script>

<template>
  <div v-if="conformidade" class="conformidade" :class="{ compacto }">
    <span class="selo" :class="conformidade.conforme ? 'ok' : 'aviso'">
      {{ conformidade.conforme ? '✓ Segue todas as regras' : '! Fora de alguma regra' }}
    </span>
    <template v-if="!compacto">
      <span
        v-for="(ok, regra) in conformidade.regras"
        :key="regra"
        class="selo"
        :class="ok ? 'ok' : 'falha'"
        :title="ok ? 'Regra atendida' : 'Regra não atendida'"
      >
        {{ ok ? '✓' : '✕' }} {{ ROTULOS[regra] || regra }}
      </span>
      <span class="suave pequeno numeros">
        {{ conformidade.caracteres }} caracteres · {{ conformidade.emojis }} emojis ·
        {{ conformidade.hashtags }} hashtags · {{ conformidade.ctas_detectadas }} CTA
      </span>
    </template>
  </div>
</template>

<style scoped>
.conformidade {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
}

.numeros {
  width: 100%;
}
</style>
