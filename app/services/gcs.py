from google.cloud import storage
from fastapi import UploadFile
import uuid
import os
from dotenv import load_dotenv

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


def exclude_of_gcs(imagem_url: str):
    client = storage.Client()

    imagem_caminho = imagem_url.split("/")[-1]

    bucket = client.get_bucket(BUCKET_NAME)
    blob = bucket.blob(imagem_caminho)

    try:
        blob.delete()
        print(f"Imagem {imagem_caminho} excluída com sucesso.")
    except Exception as e:
        print(f"Erro ao excluir imagem {imagem_caminho}: {str(e)}")