from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from app.schemas.entrada import Entrada
from app.services.multi_model_service import gerar_conteudo_multi_modelo
from app.services.instagram_service import publicar_no_feed

router = APIRouter()

@router.post("/instagram/publicar_feed")
def publicar_feed(data: dict):
    """
    Publica diretamente no Instagram sem precisar gerar conteúdo novamente.
    
    Use este endpoint quando você já tem a URL da imagem e a legenda escolhidas
    da resposta anterior do endpoint /api/
    
    Recebe:
    {
      "image_url": "https://...",
      "caption": "Sua legenda aqui"
    }
    """
    image_url = data.get("image_url")
    caption = data.get("caption")
    
    if not image_url:
        raise HTTPException(status_code=400, detail="image_url é obrigatório")
    if not caption:
        raise HTTPException(status_code=400, detail="caption é obrigatório")
    
    resultado = publicar_no_feed(image_url, caption)
    return {
        "mensagem": "Conteúdo publicado com sucesso!",
        "publicacao": resultado
    }

@router.post("/")
async def gerar_conteudo_route(entrada: Entrada):
    """
    Gera conteúdo usando TODOS os modelos disponíveis.
    Retorna todas as opções de imagens e legendas para o usuário escolher.
    
    ⚠️ ATENÇÃO: Esta requisição pode levar 2-3 minutos pois gera com múltiplos modelos.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    try:
        # Executa em thread separada para não bloquear o event loop
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            resultado = await loop.run_in_executor(
                executor, 
                gerar_conteudo_multi_modelo, 
                entrada.dict()
            )
        
        # Salva no MongoDB
        try:
            from app.services.database_service import salvar_conteudo_completo, salvar_imagem_gerada, salvar_legenda_gerada
            
            # Prepara dados para salvar
            dados_para_salvar = resultado.copy()
            dados_para_salvar.update(entrada.dict())
            
            # Salva conteúdo completo
            conteudo_id = salvar_conteudo_completo(dados_para_salvar)
            
            # Salva cada imagem individualmente
            for imagem in resultado.get("imagens", []):
                imagem_data = imagem.copy()
                imagem_data.update(entrada.dict())
                salvar_imagem_gerada(imagem_data)
            
            # Salva cada legenda individualmente
            for legenda in resultado.get("legendas", []):
                legenda_data = legenda.copy()
                legenda_data.update(entrada.dict())
                salvar_legenda_gerada(legenda_data)
            
            if conteudo_id:
                resultado["mongodb_id"] = conteudo_id
        except Exception as db_error:
            print(f"⚠️ Erro ao salvar no MongoDB (continuando): {str(db_error)}")
        
        return resultado
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao gerar conteúdo: {str(e)}")

@router.post("/editar_imagem")
async def editar_imagem_route(
    imagem: UploadFile = File(..., description="Arquivo de imagem para editar"),
    prompt: str = Form(..., description="Prompt descrevendo as alterações desejadas"),
    strength: float = Form(0.9, ge=0.0, le=1.0, description="Força da edição (0.0-1.0). Para mudanças de cor, use 0.9-1.0. Para outras edições, 0.7-0.8"),
    num_outputs: int = Form(1, ge=1, le=4, description="Número de variações a gerar")
):
    """
    Faz upload de uma imagem e edita ela com base em um prompt usando IA.
    
    Suporta formatos: JPG, PNG, WEBP
    A imagem editada é automaticamente enviada para cloud storage.
    
    Exemplo de uso:
    - prompt: "adicionar efeito de neblina ao fundo, tornar cores mais vibrantes"
    - strength: 0.7 (mantém mais da imagem original, aplica menos transformação)
    - strength: 1.0 (transforma completamente baseado no prompt)
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    # Valida tipo de arquivo
    if not imagem.content_type or not imagem.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400, 
            detail=f"Arquivo deve ser uma imagem. Tipo recebido: {imagem.content_type}"
        )
    
    try:
        # Importa apenas quando necessário para evitar bloqueios na inicialização
        from app.services.image_generators.editar_imagem import editar_imagem_com_prompt
        
        # Executa edição em thread separada
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            resultado = await loop.run_in_executor(
                executor,
                editar_imagem_com_prompt,
                imagem,
                prompt,
                strength,
                num_outputs
            )
        
        if resultado.get('status') != 'success':
            raise HTTPException(
                status_code=500,
                detail=resultado.get('error', 'Erro desconhecido ao editar imagem')
            )
        
        # Salva no MongoDB
        try:
            from app.services.database_service import salvar_imagem_editada
            edicao_id = salvar_imagem_editada(resultado)
            if edicao_id:
                resultado["mongodb_id"] = edicao_id
        except Exception as db_error:
            print(f"⚠️ Erro ao salvar edição no MongoDB (continuando): {str(db_error)}")
        
        return {
            "mensagem": "Imagem editada com sucesso!",
            "resultado": resultado
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao editar imagem: {str(e)}")

@router.post("/editar_imagem_url")
async def editar_imagem_url_route(
    image_url: str = Form(..., description="URL da imagem a ser editada"),
    prompt: str = Form(..., description="Prompt descrevendo as alterações desejadas"),
    strength: float = Form(0.7, ge=0.0, le=1.0, description="Força da edição (0.0-1.0)"),
    num_outputs: int = Form(1, ge=1, le=4, description="Número de variações a gerar")
):
    """
    Edita uma imagem a partir de uma URL usando um prompt.
    
    Útil quando você já tem a URL da imagem e quer editá-la sem fazer upload novamente.
    """
    import asyncio
    from concurrent.futures import ThreadPoolExecutor
    
    if not image_url or not image_url.startswith('http'):
        raise HTTPException(status_code=400, detail="image_url deve ser uma URL válida")
    
    try:
        # Importa apenas quando necessário para evitar bloqueios na inicialização
        from app.services.image_generators.editar_imagem import editar_imagem_com_prompt
        
        loop = asyncio.get_event_loop()
        with ThreadPoolExecutor() as executor:
            resultado = await loop.run_in_executor(
                executor,
                editar_imagem_com_prompt,
                image_url,
                prompt,
                strength,
                num_outputs
            )
        
        if resultado.get('status') != 'success':
            raise HTTPException(
                status_code=500,
                detail=resultado.get('error', 'Erro desconhecido ao editar imagem')
            )
        
        # Salva no MongoDB
        try:
            from app.services.database_service import salvar_imagem_editada
            edicao_id = salvar_imagem_editada(resultado)
            if edicao_id:
                resultado["mongodb_id"] = edicao_id
        except Exception as db_error:
            print(f"⚠️ Erro ao salvar edição no MongoDB (continuando): {str(db_error)}")
        
        return {
            "mensagem": "Imagem editada com sucesso!",
            "resultado": resultado
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao editar imagem: {str(e)}")
