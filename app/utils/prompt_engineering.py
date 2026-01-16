"""
Utilitários para engenharia de prompt usando metodologia Co-STAR
Co-STAR: Context, Statement, Task, Action, Result
"""
from typing import Dict


def _gerar_cta_por_objetivo(objetivo: str) -> str:
    """
    Gera sugestões de call-to-action baseadas no objetivo.
    
    Args:
        objetivo: Objetivo do conteúdo
    
    Returns:
        String com exemplo de CTA
    """
    objetivo_lower = objetivo.lower()
    
    # Mapeamento de objetivos para CTAs
    if 'seguidor' in objetivo_lower or 'seguir' in objetivo_lower or 'engajamento' in objetivo_lower:
        return "Salve este post, compartilhe com quem precisa ou me siga para mais dicas"
    elif 'vender' in objetivo_lower or 'produto' in objetivo_lower or 'comprar' in objetivo_lower:
        return "Deslize para ver mais, acesse o link na bio ou entre em contato"
    elif 'educar' in objetivo_lower or 'ensinar' in objetivo_lower or 'informar' in objetivo_lower:
        return "Deslive para ver mais, salve para não perder ou comente suas dúvidas"
    elif 'motivar' in objetivo_lower or 'inspirar' in objetivo_lower:
        return "Salve para quando precisar de motivação ou compartilhe com quem precisa"
    elif 'marca' in objetivo_lower or 'branding' in objetivo_lower:
        return "Acesse nosso perfil para mais conteúdo ou entre em contato conosco"
    else:
        return "Deslize para ver mais, salve este post ou compartilhe com quem precisa"


def construir_prompt_co_star(params: Dict, tipo: str = "legenda") -> str:
    """
    Constrói um prompt estruturado usando metodologia Co-STAR.
    
    Co-STAR:
    - Context: Contexto do cenário
    - Statement: Declaração do problema/necessidade
    - Task: Tarefa específica a ser realizada
    - Action: Ações esperadas
    - Result: Resultado desejado
    
    Args:
        params: Dicionário com parâmetros de entrada
        tipo: "legenda" ou "imagem"
    
    Returns:
        String com prompt estruturado
    """
    if tipo == "legenda":
        return _prompt_co_star_legenda(params)
    elif tipo == "imagem":
        return _prompt_co_star_imagem(params)
    else:
        return ""


def _prompt_co_star_legenda(params: Dict) -> str:
    """Constrói prompt Co-STAR para geração de legendas"""
    
    # CONTEXT (Contexto)
    context = (
        f"Você é um especialista em marketing digital e criação de conteúdo para redes sociais, "
        f"especialmente para {params.get('rede_alvo', 'Instagram')}. "
        f"O público-alvo é: {params.get('publico', 'geral')}. "
        f"O objetivo é: {params.get('objetivo', 'engajar')}. "
        f"O tom de voz desejado é: {params.get('tom', 'casual')}."
    )
    
    # STATEMENT (Declaração)
    statement = (
        f"É necessário criar uma legenda envolvente e autêntica que ressoe com o público, "
        f"alcançando o objetivo estabelecido através de uma comunicação {params.get('tom', 'casual')}."
    )
    
    # TASK (Tarefa)
    task = (
        f"Crie uma legenda para {params.get('rede_alvo', 'Instagram')} "
        f"sobre o tema: '{params.get('tema', 'geral')}'. "
        f"Formato: {params.get('formato', 'post')}. "
        f"A legenda deve ser adequada para {params.get('rede_alvo', 'Instagram')}."
    )
    
    # ACTION (Ações)
    objetivo = params.get('objetivo', 'engajar')
    
    # Define call-to-action baseada no objetivo
    cta_sugerida = _gerar_cta_por_objetivo(objetivo)
    
    action = (
        f"A legenda deve: "
        f"1) Capturar atenção nos primeiros caracteres com gancho impactante, "
        f"2) Conectar emocionalmente com {params.get('publico', 'o público')}, "
        f"3) Incluir uma CALL-TO-ACTION clara e direta (exemplos: '{cta_sugerida}'), "
        f"4) Usar emojis estrategicamente (2-4 emojis relevantes), "
        f"5) Incluir 3-5 hashtags relevantes no final, "
        f"6) Manter o tom {params.get('tom', 'casual')}, "
        f"7) Ter entre 100-300 caracteres para melhor engajamento."
    )
    
    # RESULT (Resultado)
    result = (
        f"A legenda final deve maximizar o {params.get('objetivo', 'engajamento')} "
        f"com {params.get('publico', 'o público-alvo')}, "
        f"sendo autêntica, envolvente e adequada para {params.get('rede_alvo', 'Instagram')}."
    )
    
    # Combina tudo em um prompt estruturado
    prompt = f"""
{context}

{statement}

TAREFA:
{task}

DIRETRIZES DE CRIAÇÃO:
{action}

RESULTADO ESPERADO:
{result}

Gerar a legenda seguindo rigorosamente todas as diretrizes acima.
"""
    
    return prompt.strip()


def _prompt_co_star_imagem(params: Dict) -> str:
    """Constrói prompt Co-STAR para geração de imagens (em inglês)"""
    
    # CONTEXT (Contexto)
    context = (
        f"Professional photography context for {params.get('rede_alvo', 'social media')}, "
        f"targeting {params.get('publico', 'general audience')}. "
        f"Format: {params.get('formato', 'square')}."
    )
    
    # STATEMENT (Declaração)
    statement = (
        f"A high-quality, realistic photograph is needed that aligns with the theme '{params.get('tema', 'general')}' "
        f"and appeals to {params.get('publico', 'the target audience')}."
    )
    
    # TASK (Tarefa)
    task = (
        f"Create a realistic, professional photograph "
        f"representing the theme: '{params.get('tema', 'general')}', "
        f"optimized for {params.get('rede_alvo', 'social media')} "
        f"in {params.get('formato', 'square')} format."
    )
    
    # ACTION (Ações) - Importante: sem texto na imagem
    action = (
        f"The image must: "
        f"1) Be photorealistic and high-quality, "
        f"2) Have professional lighting and composition, "
        f"3) Use natural colors and realistic details, "
        f"4) Be optimized for {params.get('formato', 'square')} format, "
        f"5) NOT contain any text, words, letters, or written content, "
        f"6) NOT include watermarks or labels, "
        f"7) Be visually appealing and engaging for social media, "
        f"8) Represent the theme authentically and realistically."
    )
    
    # RESULT (Resultado)
    result = (
        f"The final image should be a professional, realistic photograph "
        f"that effectively represents '{params.get('tema', 'the theme')}' "
        f"without any text, ready for use on {params.get('rede_alvo', 'social media')}."
    )
    
    # Combina tudo em um prompt estruturado
    prompt = f"""
{context}

{statement}

TASK:
{task}

GUIDELINES:
{action}

EXPECTED RESULT:
{result}
"""
    
    return prompt.strip()


def construir_prompt_imagem_simples(params: Dict, em_portugues: bool = False) -> str:
    """
    Constrói prompt simples e direto para geração de imagens.
    Versão otimizada para APIs de geração de imagem.
    """
    tema = params.get('tema', '')
    publico = params.get('publico', '')
    rede_alvo = params.get('rede_alvo', 'Instagram')
    formato = params.get('formato', 'quadrado')
    
    # Traduz formato para inglês
    formato_traduzido = {
        'carrossel': 'carousel',
        'quadrado': 'square',
        'stories': 'stories',
        'reels': 'reels',
        'post': 'post'
    }.get(formato.lower(), formato)
    
    if em_portugues:
        # Versão em português (para DALL-E que aceita)
        prompt = (
            f"Fotografia profissional realista de alta qualidade sobre o tema '{tema}', "
            f"destinada ao público '{publico}', para uso em {rede_alvo}, formato {formato_traduzido}. "
            f"Estilo fotográfico profissional, iluminação natural, cores realistas, composição equilibrada. "
            f"IMPORTANTE: A imagem NÃO deve conter nenhum texto, letras, palavras, frases ou escrita. "
            f"Sem marcas d'água, sem etiquetas, sem texto de qualquer tipo. "
            f"Fotografia pura e profissional, visual atraente para redes sociais."
        )
    else:
        # Versão em inglês (para Stability AI e outros)
        prompt = (
            f"Professional realistic high-quality photography of '{tema}', "
            f"targeting {publico}, for {rede_alvo}, {formato_traduzido} format. "
            f"Professional photographic style, natural lighting, realistic colors, balanced composition. "
            f"IMPORTANT: The image MUST NOT contain any text, words, letters, phrases, or written content. "
            f"No watermarks, no labels, no text of any kind. "
            f"Pure professional photography, visually appealing for social media."
        )
    
    return prompt

