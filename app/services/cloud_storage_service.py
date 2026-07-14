import os
import requests
from io import BytesIO
from dotenv import load_dotenv
from app.utils.imagem import baixar_e_converter_para_jpg, validar_imagem

load_dotenv()

def upload_para_imgbb(image_url_or_path):
    """Faz upload para ImgBB e retorna URLs públicas."""
    imgbb_api_key = os.getenv("IMGBB_API_KEY")
    
    if not imgbb_api_key:
        raise Exception("IMGBB_API_KEY não configurada no .env")
    
    try:
        print("📥 Preparando imagem para ImgBB...")
        if isinstance(image_url_or_path, BytesIO):
            image_url_or_path.seek(0)
            image_data = image_url_or_path.read()
            image_url_or_path.seek(0)
        elif image_url_or_path.startswith('http'):
            info = validar_imagem(image_url_or_path)
            if not info['valida']:
                raise Exception(f"Imagem inválida: {info.get('erro')}")
            
            print("🔄 Convertendo para JPG...")
            image_buffer = baixar_e_converter_para_jpg(image_url_or_path)
            image_data = image_buffer.getvalue()
        else:
            with open(image_url_or_path, 'rb') as f:
                image_data = f.read()
        
        print("☁️  Upload para ImgBB...")
        url = "https://api.imgbb.com/1/upload"
        
        response = requests.post(url, files={"image": image_data}, data={"key": imgbb_api_key})
        response.raise_for_status()
        result = response.json()
        
        if result.get('success'):
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


def upload_imagem_para_cloud(image_url_or_path, folder="instagram_posts"):
    return upload_para_imgbb(image_url_or_path)
