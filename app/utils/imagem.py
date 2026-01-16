import requests
from io import BytesIO
from PIL import Image
import os


def baixar_imagem(url, caminho_destino):
    """
    Baixa uma imagem de uma URL e salva localmente.
    
    Args:
        url: URL da imagem
        caminho_destino: Caminho onde salvar a imagem
    """
    r = requests.get(url)
    r.raise_for_status()
    with open(caminho_destino, 'wb') as f:
        f.write(r.content)


def baixar_e_converter_para_jpg(url, caminho_destino=None):
    """
    Baixa uma imagem de uma URL e converte para JPG.
    
    Args:
        url: URL da imagem (ex: URL temporária do DALL-E)
        caminho_destino: Caminho onde salvar (opcional). Se None, retorna BytesIO
    
    Returns:
        BytesIO ou caminho do arquivo salvo
    """
    # 1. Baixa a imagem
    response = requests.get(url)
    response.raise_for_status()
    
    # 2. Abre com PIL
    imagem = Image.open(BytesIO(response.content))
    
    # 3. Converte para RGB (necessário para JPG se for PNG/RGBA)
    if imagem.mode in ('RGBA', 'LA', 'P'):
        # Cria um fundo branco
        rgb_imagem = Image.new('RGB', imagem.size, (255, 255, 255))
        rgb_imagem.paste(imagem, mask=imagem.split()[-1] if imagem.mode == 'RGBA' else None)
        imagem = rgb_imagem
    elif imagem.mode != 'RGB':
        imagem = imagem.convert('RGB')
    
    # 4. Salva como JPG
    if caminho_destino:
        # Garante que a extensão seja .jpg
        if not caminho_destino.lower().endswith('.jpg'):
            caminho_destino = os.path.splitext(caminho_destino)[0] + '.jpg'
        
        imagem.save(caminho_destino, 'JPEG', quality=95, optimize=True)
        return caminho_destino
    else:
        # Retorna como BytesIO
        buffer = BytesIO()
        imagem.save(buffer, 'JPEG', quality=95, optimize=True)
        buffer.seek(0)
        return buffer


def converter_imagem_para_jpg(caminho_origem, caminho_destino=None):
    """
    Converte uma imagem local para JPG.
    
    Args:
        caminho_origem: Caminho da imagem original
        caminho_destino: Caminho de destino (opcional)
    
    Returns:
        Caminho do arquivo JPG criado
    """
    imagem = Image.open(caminho_origem)
    
    # Converte para RGB se necessário
    if imagem.mode in ('RGBA', 'LA', 'P'):
        rgb_imagem = Image.new('RGB', imagem.size, (255, 255, 255))
        rgb_imagem.paste(imagem, mask=imagem.split()[-1] if imagem.mode == 'RGBA' else None)
        imagem = rgb_imagem
    elif imagem.mode != 'RGB':
        imagem = imagem.convert('RGB')
    
    # Define caminho de destino
    if not caminho_destino:
        caminho_destino = os.path.splitext(caminho_origem)[0] + '.jpg'
    
    # Salva como JPG
    imagem.save(caminho_destino, 'JPEG', quality=95, optimize=True)
    return caminho_destino


def validar_imagem(caminho_ou_url):
    """
    Valida se uma imagem é válida e retorna informações.
    
    Args:
        caminho_ou_url: Caminho local ou URL da imagem
    
    Returns:
        dict com informações da imagem
    """
    try:
        if caminho_ou_url.startswith('http'):
            response = requests.get(caminho_ou_url)
            response.raise_for_status()
            imagem = Image.open(BytesIO(response.content))
        else:
            imagem = Image.open(caminho_ou_url)
        
        return {
            'valida': True,
            'formato': imagem.format,
            'modo': imagem.mode,
            'tamanho': imagem.size,
            'largura': imagem.width,
            'altura': imagem.height
        }
    except Exception as e:
        return {
            'valida': False,
            'erro': str(e)
        }
