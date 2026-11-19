<script setup>
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { api, ErroSessao } from '../api.js'
import ConformidadeLegenda from './ConformidadeLegenda.vue'
import PreviaInstagram from './PreviaInstagram.vue'

const props = defineProps({
  usuario: { type: Object, required: true },
})

// Os valores dos objetivos contêm as palavras-chave que o back-end usa para
// escolher a CTA única (app/utils/prompt_engineering.py → selecionar_cta).
const OBJETIVOS = [
  { valor: 'vender produto', rotulo: '🛍️ Vender um produto' },
  { valor: 'ganhar seguidores', rotulo: '📈 Ganhar seguidores' },
  { valor: 'gerar engajamento e comentários', rotulo: '💬 Gerar comentários' },
  { valor: 'educar o público com dicas', rotulo: '💡 Educar / dar dicas' },
  { valor: 'inspirar e motivar', rotulo: '✨ Inspirar' },
  { valor: 'fortalecer a marca', rotulo: '🏷️ Fortalecer a marca' },
]
const TONS = ['descontraído', 'profissional', 'acolhedor', 'inspirador', 'divertido', 'elegante']
const EXEMPLOS = [
  {
    tema: 'lançamento da coleção de verão',
    objetivo: 'vender produto',
    publico: 'mulheres de 20 a 35 anos que gostam de moda praia',
    tom: 'descontraído',
  },
  {
    tema: 'dicas de lanches saudáveis para levar ao trabalho',
    objetivo: 'educar o público com dicas',
    publico: 'adultos de 25 a 45 anos com rotina corrida',
    tom: 'acolhedor',
  },
  {
    tema: 'novo café especial da casa',
    objetivo: 'gerar engajamento e comentários',
    publico: 'amantes de café da região',
    tom: 'divertido',
  },
]

const form = reactive({ tema: '', objetivo: '', publico: '', tom: '' })
const objetivoPersonalizado = ref(false)
const tomPersonalizado = ref(false)

// formulario → gerando → escolha → publicando → publicado
const etapa = ref('formulario')
const erro = ref('')
const resultado = ref(null)
const imagemEscolhida = ref(null)
const legendaEscolhida = ref(null)
const legendaEditada = ref('')
const confirmando = ref(false)
const publicacao = ref(null)

// Cronômetro exibido durante a geração e a publicação
const segundos = ref(0)
let cronometro = null
function iniciarCronometro() {
  segundos.value = 0
  clearInterval(cronometro)
  cronometro = setInterval(() => segundos.value++, 1000)
}
function pararCronometro() {
  clearInterval(cronometro)
}
onBeforeUnmount(pararCronometro)

const formularioValido = computed(
  () =>
    form.tema.trim().length >= 2 &&
    form.objetivo.trim().length >= 2 &&
    form.publico.trim().length >= 2 &&
    form.tom.trim().length >= 2,
)

const mensagemGerando = computed(() => {
  if (segundos.value < 5) return 'Montando o prompt (CO-STAR + CTA)…'
  if (segundos.value < 15) return 'As IAs estão escrevendo as legendas…'
  if (segundos.value < 35) return 'Criando as imagens…'
  return 'Finalizando e hospedando as imagens…'
})

const legendaFoiEditada = computed(
  () => legendaEscolhida.value && legendaEditada.value !== legendaEscolhida.value.legenda,
)
const contagem = computed(() => ({
  caracteres: [...legendaEditada.value].length,
  hashtags: (legendaEditada.value.match(/#[\p{L}\p{N}_]+/gu) || []).length,
}))

const podePublicar = computed(
  () =>
    imagemEscolhida.value &&
    legendaEditada.value.trim().length > 0 &&
    contagem.value.caracteres <= 2200 &&
    contagem.value.hashtags <= 30,
)

function usarExemplo(exemplo) {
  Object.assign(form, exemplo)
  objetivoPersonalizado.value = !OBJETIVOS.some((o) => o.valor === exemplo.objetivo)
  tomPersonalizado.value = !TONS.includes(exemplo.tom)
}

function escolherLegenda(legenda) {
  legendaEscolhida.value = legenda
  legendaEditada.value = legenda.legenda
}

function tratarErro(e) {
  if (e instanceof ErroSessao) return // o App volta para a tela de login
  erro.value = e.message
}

async function gerar() {
  erro.value = ''
  etapa.value = 'gerando'
  iniciarCronometro()
  try {
    const dados = await api.gerar({ ...form, tipo: 'imagem' })
    resultado.value = dados
    imagemEscolhida.value = dados.imagens[0] || null
    // Sugere a primeira legenda que segue todas as regras.
    const sugerida = dados.legendas.find((l) => l.conformidade?.conforme) || dados.legendas[0]
    if (sugerida) escolherLegenda(sugerida)
    else {
      legendaEscolhida.value = null
      legendaEditada.value = ''
    }
    etapa.value = 'escolha'
  } catch (e) {
    tratarErro(e)
    etapa.value = 'formulario'
  } finally {
    pararCronometro()
  }
}

async function publicar() {
  erro.value = ''
  confirmando.value = false
  etapa.value = 'publicando'
  iniciarCronometro()
  try {
    const resposta = await api.publicar({
      image_url: imagemEscolhida.value.url_publica,
      caption: legendaEditada.value,
      conteudo_id: resultado.value?.conteudo_id || null,
    })
    publicacao.value = resposta.publicacao
    etapa.value = 'publicado'
  } catch (e) {
    tratarErro(e)
    etapa.value = 'escolha'
  } finally {
    pararCronometro()
  }
}

function novoPost() {
  etapa.value = 'formulario'
  resultado.value = null
  imagemEscolhida.value = null
  legendaEscolhida.value = null
  legendaEditada.value = ''
  publicacao.value = null
  erro.value = ''
}

function segundosTexto(valor) {
  return typeof valor === 'number' ? `${valor.toFixed(1).replace('.', ',')} s` : '—'
}
</script>

<template>
  <div class="criar">
    <!-- Indicador das 4 ações do fluxo integrado -->
    <ol class="trilha">
      <li :class="{ atual: etapa === 'formulario', feito: etapa !== 'formulario' }"><span>1</span> Descrever</li>
      <li :class="{ atual: etapa === 'gerando', feito: ['escolha', 'publicando', 'publicado'].includes(etapa) }">
        <span>2</span> Gerar
      </li>
      <li :class="{ atual: etapa === 'escolha', feito: ['publicando', 'publicado'].includes(etapa) }">
        <span>3</span> Escolher
      </li>
      <li :class="{ atual: etapa === 'publicando', feito: etapa === 'publicado' }"><span>4</span> Publicar</li>
    </ol>

    <div v-if="erro" class="alerta erro bloco-erro">
      <span>⚠️</span>
      <span>{{ erro }}</span>
      <button class="botao-texto pequeno fechar" @click="erro = ''">Fechar</button>
    </div>

    <!-- 1. FORMULÁRIO -->
    <section v-if="etapa === 'formulario'" class="cartao formulario">
      <div class="cabecalho">
        <div>
          <h2>Sobre o que vamos postar?</h2>
          <p class="suave">Preencha os quatro campos. A ferramenta monta o prompt para as IAs.</p>
        </div>
        <div class="exemplos">
          <span class="suave pequeno">Testar com um exemplo:</span>
          <button v-for="(ex, i) in EXEMPLOS" :key="i" class="chip pequeno" @click="usarExemplo(ex)">
            {{ ['Loja de roupas', 'Nutricionista', 'Cafeteria'][i] }}
          </button>
        </div>
      </div>

      <div class="campo">
        <label for="tema">Tema do post</label>
        <textarea
          id="tema"
          v-model="form.tema"
          class="entrada"
          maxlength="200"
          rows="2"
          placeholder="Ex.: lançamento da coleção de verão"
        ></textarea>
      </div>

      <div class="campo">
        <label>Objetivo</label>
        <div class="chips">
          <button
            v-for="o in OBJETIVOS"
            :key="o.valor"
            class="chip"
            :class="{ ativo: !objetivoPersonalizado && form.objetivo === o.valor }"
            @click="(form.objetivo = o.valor), (objetivoPersonalizado = false)"
          >
            {{ o.rotulo }}
          </button>
          <button
            class="chip"
            :class="{ ativo: objetivoPersonalizado }"
            @click="(objetivoPersonalizado = true), (form.objetivo = '')"
          >
            ✏️ Outro
          </button>
        </div>
        <input
          v-if="objetivoPersonalizado"
          v-model="form.objetivo"
          class="entrada"
          maxlength="200"
          placeholder="Descreva o objetivo"
        />
        <span class="dica">O objetivo define a chamada para ação (CTA) da legenda, uma só por post.</span>
      </div>

      <div class="campo">
        <label for="publico">Público-alvo</label>
        <input
          id="publico"
          v-model="form.publico"
          class="entrada"
          maxlength="200"
          placeholder="Ex.: mulheres de 20 a 35 anos que gostam de moda praia"
        />
      </div>

      <div class="campo">
        <label>Tom de voz</label>
        <div class="chips">
          <button
            v-for="t in TONS"
            :key="t"
            class="chip"
            :class="{ ativo: !tomPersonalizado && form.tom === t }"
            @click="(form.tom = t), (tomPersonalizado = false)"
          >
            {{ t.charAt(0).toUpperCase() + t.slice(1) }}
          </button>
          <button class="chip" :class="{ ativo: tomPersonalizado }" @click="(tomPersonalizado = true), (form.tom = '')">
            ✏️ Outro
          </button>
        </div>
        <input v-if="tomPersonalizado" v-model="form.tom" class="entrada" maxlength="100" placeholder="Descreva o tom" />
      </div>

      <div class="acoes">
        <button class="botao botao-primario botao-grande" :disabled="!formularioValido" @click="gerar">
          ✨ Gerar opções
        </button>
      </div>
    </section>

    <!-- 2. GERANDO -->
    <section v-else-if="etapa === 'gerando'" class="cartao gerando">
      <div class="gerando-topo">
        <span class="giro escuro"></span>
        <div>
          <h2>{{ mensagemGerando }}</h2>
          <p class="suave">Todas as IAs trabalham ao mesmo tempo. Costuma levar de 20 a 40 segundos · {{ segundos }} s</p>
        </div>
      </div>
      <div class="esqueletos">
        <div class="esqueleto quadrado"></div>
        <div class="esqueleto quadrado"></div>
        <div class="linhas">
          <div class="esqueleto linha"></div>
          <div class="esqueleto linha"></div>
          <div class="esqueleto linha curta"></div>
        </div>
      </div>
    </section>

    <!-- 3. ESCOLHA / 4. PUBLICANDO -->
    <section v-else-if="etapa === 'escolha' || etapa === 'publicando'" class="escolha">
      <div class="coluna-opcoes">
        <div class="cartao">
          <div class="titulo-secao">
            <h2>Escolha a imagem</h2>
            <span class="suave pequeno">gerado em {{ segundosTexto(resultado?.tempo_total_s) }}</span>
          </div>

          <div v-if="resultado.imagens.length" class="grade-imagens">
            <button
              v-for="img in resultado.imagens"
              :key="img.provedor"
              class="opcao-imagem"
              :class="{ escolhida: imagemEscolhida === img }"
              :disabled="etapa === 'publicando'"
              @click="imagemEscolhida = img"
            >
              <img :src="img.url_publica" :alt="`Imagem gerada por ${img.provedor}`" loading="lazy" />
              <span class="rotulo-opcao">
                <strong>{{ img.provedor }}</strong>
                <span>{{ segundosTexto(img.tempo_s) }}</span>
              </span>
              <span v-if="imagemEscolhida === img" class="marcado">✓</span>
            </button>
          </div>
          <p v-else class="alerta aviso">Nenhuma imagem foi gerada. Tente gerar de novo.</p>

          <p v-for="f in resultado.imagens_falhas" :key="'fi' + f.provedor" class="falha-provedor pequeno">
            ✕ {{ f.provedor }} não gerou imagem: {{ f.error }}
          </p>
        </div>

        <div class="cartao">
          <h2>Escolha a legenda</h2>
          <div class="lista-legendas">
            <button
              v-for="leg in resultado.legendas"
              :key="leg.provedor"
              class="opcao-legenda"
              :class="{ escolhida: legendaEscolhida === leg }"
              :disabled="etapa === 'publicando'"
              @click="escolherLegenda(leg)"
            >
              <div class="opcao-legenda-topo">
                <strong>{{ leg.provedor }}</strong>
                <span class="suave pequeno">{{ leg.modelo }} · {{ segundosTexto(leg.tempo_s) }}</span>
              </div>
              <p>{{ leg.legenda }}</p>
              <ConformidadeLegenda :conformidade="leg.conformidade" :compacto="legendaEscolhida !== leg" />
            </button>
          </div>
          <p v-for="f in resultado.legendas_falhas" :key="'fl' + f.provedor" class="falha-provedor pequeno">
            ✕ {{ f.provedor }} não gerou legenda: {{ f.error }}
          </p>
        </div>
      </div>

      <aside class="coluna-previa">
        <div class="cartao previa-cartao">
          <h2>Prévia</h2>
          <PreviaInstagram
            :usuario="props.usuario.instagram_username || 'seu_perfil'"
            :imagem="imagemEscolhida?.url_publica"
            :legenda="legendaEditada"
          />

          <div class="campo">
            <label for="legenda-final">Legenda final (pode editar)</label>
            <textarea
              id="legenda-final"
              v-model="legendaEditada"
              class="entrada"
              rows="6"
              :disabled="etapa === 'publicando'"
            ></textarea>
            <span class="dica" :class="{ excedido: contagem.caracteres > 2200 || contagem.hashtags > 30 }">
              {{ contagem.caracteres }}/2200 caracteres · {{ contagem.hashtags }}/30 hashtags
              <template v-if="legendaFoiEditada"> · editada por você</template>
            </span>
          </div>

          <div v-if="etapa === 'publicando'" class="alerta info">
            <span class="giro escuro"></span>
            <span>Publicando… o Instagram está processando a imagem ({{ segundos }} s).</span>
          </div>

          <template v-else>
            <div v-if="confirmando" class="confirmar">
              <p>Publicar agora em <strong>@{{ props.usuario.instagram_username }}</strong>?</p>
              <div class="confirmar-botoes">
                <button class="botao botao-secundario" @click="confirmando = false">Cancelar</button>
                <button class="botao botao-primario" @click="publicar">Sim, publicar</button>
              </div>
            </div>
            <button
              v-else
              class="botao botao-primario botao-grande largo"
              :disabled="!podePublicar"
              @click="confirmando = true"
            >
              🚀 Publicar no Instagram
            </button>
            <button class="botao-texto pequeno" @click="novoPost">← Voltar e mudar o pedido</button>
          </template>
        </div>
      </aside>
    </section>

    <!-- 5. PUBLICADO -->
    <section v-else-if="etapa === 'publicado'" class="cartao publicado">
      <div class="publicado-icone">🎉</div>
      <h2>Publicado no Instagram!</h2>
      <p class="suave">
        Post publicado em @{{ props.usuario.instagram_username }} em {{ segundosTexto(publicacao?.tempo_s) }}.
      </p>
      <div class="publicado-previa">
        <PreviaInstagram
          :usuario="props.usuario.instagram_username || 'seu_perfil'"
          :imagem="imagemEscolhida?.url_publica"
          :legenda="legendaEditada"
        />
      </div>
      <div class="confirmar-botoes">
        <a
          v-if="publicacao?.permalink"
          class="botao botao-primario"
          :href="publicacao.permalink"
          target="_blank"
          rel="noopener"
        >
          Ver no Instagram ↗
        </a>
        <button class="botao botao-secundario" @click="novoPost">Criar outro post</button>
      </div>
      <p v-if="publicacao?.limite_publicacao" class="suave pequeno">
        Publicações via API nas últimas 24 h: {{ publicacao.limite_publicacao.usadas + 1 }} de
        {{ publicacao.limite_publicacao.total }}.
      </p>
    </section>
  </div>
</template>

<style scoped>
.criar {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.trilha {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  gap: 8px;
  justify-content: center;
  flex-wrap: wrap;
}

.trilha li {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 14px 6px 6px;
  border-radius: 999px;
  background: var(--superficie);
  border: 1px solid var(--borda);
  color: var(--texto-suave);
  font-weight: 600;
  font-size: 0.9rem;
}

.trilha li span {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--superficie-2);
  font-size: 0.8rem;
}

.trilha li.atual {
  color: var(--primaria-escura);
  border-color: var(--primaria);
}

.trilha li.atual span {
  background: var(--gradiente);
  color: #fff;
}

.trilha li.feito span {
  background: var(--sucesso-claro);
  color: var(--sucesso);
}

.bloco-erro {
  align-items: center;
}

.fechar {
  margin-left: auto;
}

h2 {
  font-size: 1.2rem;
}

/* Formulário */
.formulario {
  max-width: 820px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 22px;
  padding: 32px;
}

.cabecalho {
  display: flex;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}

.cabecalho h2 {
  font-size: 1.5rem;
  margin-bottom: 4px;
}

.cabecalho p {
  margin: 0;
}

.exemplos {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
}

.exemplos .chip {
  padding: 5px 12px;
}

.acoes {
  display: flex;
  justify-content: flex-end;
}

/* Gerando */
.gerando {
  max-width: 820px;
  width: 100%;
  margin: 0 auto;
  display: flex;
  flex-direction: column;
  gap: 24px;
  padding: 32px;
}

.gerando-topo {
  display: flex;
  gap: 16px;
  align-items: center;
}

.gerando-topo .giro {
  width: 32px;
  height: 32px;
  border-width: 3px;
}

.gerando-topo p {
  margin: 4px 0 0;
}

.esqueletos {
  display: grid;
  grid-template-columns: 1fr 1fr 1.4fr;
  gap: 16px;
}

.quadrado {
  aspect-ratio: 1 / 1;
}

.linhas {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.linha {
  height: 22px;
}

.linha.curta {
  width: 60%;
}

/* Escolha */
.escolha {
  display: grid;
  grid-template-columns: minmax(0, 1.5fr) minmax(320px, 1fr);
  gap: 20px;
  align-items: start;
}

.coluna-opcoes {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.coluna-opcoes .cartao {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.titulo-secao {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}

.grade-imagens {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
  gap: 14px;
}

.opcao-imagem {
  position: relative;
  padding: 0;
  border: 2px solid var(--borda);
  border-radius: var(--raio);
  overflow: hidden;
  background: var(--superficie-2);
  text-align: left;
  transition: border-color 0.15s, transform 0.15s;
}

.opcao-imagem:hover:not(:disabled) {
  transform: translateY(-2px);
}

.opcao-imagem.escolhida {
  border-color: var(--primaria);
  box-shadow: 0 0 0 4px var(--primaria-clara);
}

.opcao-imagem img {
  width: 100%;
  aspect-ratio: 1 / 1;
  object-fit: cover;
  display: block;
}

.rotulo-opcao {
  display: flex;
  justify-content: space-between;
  padding: 8px 12px;
  background: var(--superficie);
  font-size: 0.85rem;
}

.marcado {
  position: absolute;
  top: 10px;
  right: 10px;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: var(--gradiente);
  color: #fff;
  display: grid;
  place-items: center;
  font-weight: 800;
}

.lista-legendas {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.opcao-legenda {
  text-align: left;
  border: 2px solid var(--borda);
  border-radius: var(--raio);
  padding: 14px 16px;
  background: var(--superficie);
  display: flex;
  flex-direction: column;
  gap: 8px;
  transition: border-color 0.15s;
}

.opcao-legenda:hover:not(:disabled) {
  border-color: #c9c2ff;
}

.opcao-legenda.escolhida {
  border-color: var(--primaria);
  background: #faf9ff;
}

.opcao-legenda p {
  margin: 0;
  white-space: pre-wrap;
  font-size: 0.95rem;
}

.opcao-legenda-topo {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;
}

.falha-provedor {
  margin: 0;
  color: var(--erro);
}

.coluna-previa {
  position: sticky;
  top: 84px;
}

.previa-cartao {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.excedido {
  color: var(--erro);
  font-weight: 600;
}

.largo {
  width: 100%;
}

.confirmar {
  background: var(--primaria-clara);
  border-radius: var(--raio-p);
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.confirmar p {
  margin: 0;
}

.confirmar-botoes {
  display: flex;
  gap: 10px;
  justify-content: center;
  flex-wrap: wrap;
}

.confirmar .confirmar-botoes {
  justify-content: flex-end;
}

/* Publicado */
.publicado {
  max-width: 560px;
  width: 100%;
  margin: 0 auto;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 14px;
  align-items: center;
  padding: 36px;
}

.publicado h2 {
  font-size: 1.6rem;
}

.publicado p {
  margin: 0;
}

.publicado-icone {
  font-size: 3rem;
}

.publicado-previa {
  width: 100%;
  max-width: 360px;
  text-align: left;
}

@media (max-width: 960px) {
  .escolha {
    grid-template-columns: 1fr;
  }
  .coluna-previa {
    position: static;
  }
  .esqueletos {
    grid-template-columns: 1fr 1fr;
  }
  .linhas {
    grid-column: span 2;
  }
}
</style>
