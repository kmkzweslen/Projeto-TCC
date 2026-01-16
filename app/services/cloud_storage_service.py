import os
import requests
from io import BytesIO
from dotenv import load_dotenv
import cloudinary
import cloudinary.uploader
from PIL import Image
from app.utils.imagem import baixar_e_converter_para_jpg, validar_imagem

load_dotenv()

# Configura cloudinary apenas se as variáveis estiverem definidas
# Evita bloqueios na inicialização se não estiver configurado
try:
    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")
    
    if cloud_name and api_key and api_secret:
        cloudinary.config(
            cloud_name=cloud_name,
            api_key=api_key,
            api_secret=api_secret
        )
except Exception as e:
    print(f"⚠️ Aviso: Cloudinary não configurado corretamente: {str(e)}")

def upload_imagem_para_cloud(image_url_or_path, folder="instagram_posts"):
    """
    Faz upload de uma imagem para o Cloudinary e retorna a URL pública.
    
    PROCESSO:
    1. Baixa a imagem da URL do DALL-E (formato PNG)
    2. Converte para JPG (formato aceito pelo Instagram)
    3. Faz upload para Cloudinary
    4. Retorna URL pública permanente
    
    Args:
        image_url_or_path: URL da imagem gerada pelo DALL-E ou caminho local
        folder: Pasta no Cloudinary para organizar as imagens
    
    Returns:
        dict: Contém 'public_url', 'secure_url', 'public_id', 'format', etc.
    """
    try:
        print(f"📥 Baixando imagem de: {image_url_or_path[:50]}...")
        
        # Aceita URL, caminho de arquivo ou BytesIO
        if isinstance(image_url_or_path, BytesIO):
            image_data = image_url_or_path
        elif image_url_or_path.startswith('http'):
            info = validar_imagem(image_url_or_path)
            if not info['valida']:
                raise Exception(f"Imagem inválida: {info.get('erro')}")
            
            print(f"✅ Imagem válida: {info['formato']} {info['largura']}x{info['altura']}")
            print("🔄 Convertendo para JPG...")
            image_data = baixar_e_converter_para_jpg(image_url_or_path)
            print("✅ Conversão concluída!")
        else:
            # É um caminho de arquivo
            with open(image_url_or_path, 'rb') as f:
                image_data = BytesIO(f.read())
        
        print("☁️  Fazendo upload para Cloudinary...")
        upload_result = cloudinary.uploader.upload(
            image_data,
            folder=folder,
            resource_type="image",
            format="jpg",
            quality="auto:best",
            transformation=[
                {'width': 1080, 'height': 1080, 'crop': 'limit'},
            ]
        )
        
        print(f"✅ Upload concluído! URL: {upload_result['secure_url']}")
        
        return {
            'public_url': upload_result['url'],
            'secure_url': upload_result['secure_url'],
            'public_id': upload_result['public_id'],
            'format': upload_result['format'],
            'width': upload_result['width'],
            'height': upload_result['height']
        }
    
    except Exception as e:
        print(f"❌ Erro no upload: {str(e)}")
        raise Exception(f"Erro ao fazer upload da imagem: {str(e)}")


def deletar_imagem_cloud(public_id):
    """
    Deleta uma imagem do Cloudinary usando seu public_id.
    Útil para limpar imagens antigas e economizar espaço.
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result
    except Exception as e:
        raise Exception(f"Erro ao deletar imagem: {str(e)}")

def upload_para_imgbb(image_url_or_path):
    """
    Alternativa usando ImgBB (100% gratuito, sem necessidade de cartão).
    Requer apenas uma API key gratuita de https://api.imgbb.com/
    
    PROCESSO:
    1. Baixa a imagem da URL do DALL-E (formato PNG)
    2. Converte para JPG (formato aceito pelo Instagram)
    3. Faz upload para ImgBB
    4. Retorna URL pública permanente
    """
    imgbb_api_key = os.getenv("IMGBB_API_KEY")
    
    if not imgbb_api_key:
        raise Exception("IMGBB_API_KEY não configurada no .env")
    
    try:
        print(f"📥 Baixando imagem para ImgBB...")
        
        # Aceita URL, caminho de arquivo ou BytesIO
        if isinstance(image_url_or_path, BytesIO):
            # Garante que o buffer está no início
            image_url_or_path.seek(0)
            image_data = image_url_or_path.read()
            # Reseta o buffer para o início caso seja usado novamente
            image_url_or_path.seek(0)
        elif image_url_or_path.startswith('http'):
            info = validar_imagem(image_url_or_path)
            if not info['valida']:
                raise Exception(f"Imagem inválida: {info.get('erro')}")
            
            print(f"✅ Imagem válida: {info['formato']} {info['largura']}x{info['altura']}")
            
            print("🔄 Convertendo para JPG...")
            image_buffer = baixar_e_converter_para_jpg(image_url_or_path)
            image_data = image_buffer.getvalue()
            print("✅ Conversão concluída!")
        else:
            # É um caminho de arquivo
            with open(image_url_or_path, 'rb') as f:
                image_data = f.read()
        
        # Upload para ImgBB
        print("☁️  Fazendo upload para ImgBB...")
        url = "https://api.imgbb.com/1/upload"
        
        response = requests.post(url, files={"image": image_data}, data={"key": imgbb_api_key})
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
            print(f"✅ Upload concluído! URL: {result['data']['url']}")
            
            return {
                'public_url': result['data']['url'],
                'secure_url': result['data']['url'], 
                'delete_url': result['data'].get('delete_url'),
                'display_url': result['data'].get('display_url'),
                'width': result['data'].get('width', 1024),
                'height': result['data'].get('height', 1024),
                'format': 'jpg',
                'size': result['data'].get('size', 0), 
                'thumb_url': result['data'].get('thumb', {}).get('url'), 
                'medium_url': result['data'].get('medium', {}).get('url'),
                'image_url': result['data'].get('image', {}).get('url')
            }
        else:
            error_msg = result.get('error', {}).get('message', 'Falha desconhecida no upload')
            raise Exception(f"Falha no upload para ImgBB: {error_msg}")
    
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro de conexão com ImgBB: {str(e)}")
        raise Exception(f"Erro de conexão ao fazer upload para ImgBB: {str(e)}")
    except Exception as e:
        print(f"❌ Erro no upload para ImgBB: {str(e)}")
        raise Exception(f"Erro ao fazer upload para ImgBB: {str(e)}")
