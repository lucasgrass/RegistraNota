from google.cloud import storage
from fastapi import UploadFile
import uuid
import os
from dotenv import load_dotenv
from fastapi import HTTPException, status
from datetime import datetime, timedelta

load_dotenv()

BUCKET_NAME = os.getenv('BUCKET_NAME')

def upload_to_gcs(image: UploadFile):
    try:
        client = storage.Client()
    except Exception as e:
        print(f"Erro ao autenticar no Google Cloud: {e}")
        return None

    try:
        bucket = client.get_bucket(BUCKET_NAME)
    except Exception as e:
        print(f"Erro ao acessar o bucket: {e}")
        return None

    file_uuid = str(uuid.uuid4())
    blob = bucket.blob(f"{file_uuid}")

    try:
        blob.upload_from_file(image.file, content_type=image.content_type)
    except Exception as e:
        print(f"Erro ao fazer o upload da imagem: {e}")
        return None

    imagem_url = blob.public_url

    return imagem_url


def exclude_from_gcs(imagem_url: str):
    client = storage.Client()
    
    # Extrair o nome do arquivo da URL da imagem
    imagem_caminho = imagem_url.split("/")[-1]  # Pega a última parte da URL (nome do arquivo)
    
    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(imagem_caminho)
    
    try:
        blob.delete()  # Exclui a imagem do GCS
        print(f"Imagem {imagem_caminho} excluída com sucesso.")
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao excluir imagem {imagem_caminho}: {str(e)}"
        )
    

def generate_signed_url(blob_name: str, expiration: int = 30) -> str:
    """
    Gera uma URL assinada para um arquivo no Google Cloud Storage.

    :param blob_name: Nome do arquivo (blob) no bucket.
    :param expiration: Tempo de expiração da URL em minutos (padrão: 15 minutos).
    :return: URL assinada.
    """
    try:
        client = storage.Client()
        bucket = client.get_bucket(BUCKET_NAME)
        blob = bucket.blob(blob_name)

        # Define o tempo de expiração
        expiration_time = datetime.utcnow() + timedelta(minutes=expiration)

        # Gera a URL assinada
        signed_url = blob.generate_signed_url(
            version="v4",
            expiration=expiration_time,
            method="GET",  # Ação permitida (GET para leitura)
        )

        return signed_url
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao gerar URL assinada: {str(e)}"
        )