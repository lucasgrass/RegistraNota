import cv2
import numpy as np
import io
import base64
from fastapi import UploadFile
import requests
import re
import os
from dotenv import load_dotenv
from app.services.gcs import upload_to_gcs

load_dotenv()

API_KEY = os.getenv('API_KEY')

# Função de pré-processamento
def preprocess_image(img):
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    return imgBlur

# Função para detectar texto e contornos
def detect_text_and_contours(image_file):
    # Carregar os dados da imagem
    image_file.file.seek(0)
    img_data = image_file.file.read()

    if not img_data:
        raise ValueError("Imagem vazia ou não foi lida corretamente.")

    # Decodificar a imagem para o OpenCV
    img_array = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        raise ValueError("Falha ao decodificar a imagem.")

    # Codificar a imagem para base64 para envio para a API
    base64_image = base64.b64encode(img_data).decode('utf-8')

    # Enviar para a Google Vision API
    url = f"https://vision.googleapis.com/v1/images:annotate?key={API_KEY}"
    payload = {
        "requests": [
            {
                "image": {"content": base64_image},
                "features": [{"type": "DOCUMENT_TEXT_DETECTION"}],
            }
        ]
    }

    # Enviar a solicitação
    response = requests.post(url, json=payload)
    response_data = response.json()

    if "error" in response_data:
        raise Exception(f"Erro da API Google Vision: {response_data['error']['message']}")

    # Obter as anotações de texto
    annotations = response_data.get("responses", [{}])[0].get("fullTextAnnotation", None)
    if not annotations or "pages" not in annotations:
        print("Nenhum texto detectado.")
        return None, None

    blocks = annotations["pages"][0].get("blocks", [])
    if not blocks:
        print("Nenhum bloco de texto detectado.")
        return None, None

    # Coletar vértices
    all_vertices = []
    for block in blocks:
        bounding_box = block.get("boundingBox", {})
        vertices = bounding_box.get("vertices", [])
        for vertex in vertices:
            x = vertex.get("x", 0)
            y = vertex.get("y", 0)
            all_vertices.append((x, y))

    return all_vertices, annotations.get("text", "")

# Função para corrigir a perspectiva da imagem
def correct_perspective(img, vertices):
    if len(vertices) < 4:
        print("Número insuficiente de vértices para correção.")
        return img

    x_coords = [v[0] for v in vertices]
    y_coords = [v[1] for v in vertices]

    min_x, max_x = min(x_coords), max(x_coords)
    min_y, max_y = min(y_coords), max(y_coords)

    # Definir os pontos de origem e destino para correção
    src_points = np.float32([
        [min_x, min_y],
        [max_x, min_y],
        [max_x, max_y],
        [min_x, max_y]
    ])

    dst_points = np.float32([
        [0, 0],
        [max_x - min_x, 0],
        [max_x - min_x, max_y - min_y],
        [0, max_y - min_y]
    ])

    # Aplicar a transformação de perspectiva
    matrix = cv2.getPerspectiveTransform(src_points, dst_points)
    corrected_img = cv2.warpPerspective(img, matrix, (int(max_x - min_x), int(max_y - min_y)))
    return corrected_img

# Função principal para processar a imagem
def execute_scan(image: UploadFile):
    try:
        # Detectar texto e contornos
        vertices, text = detect_text_and_contours(image)
        if vertices is None:
            raise ValueError("Nenhum contorno válido encontrado.")

        valor_pago, data_extraida = extract_value_and_date(text)
        print(f"Valor extraído: R$ {valor_pago}")
        print(f"Data extraída: {data_extraida}")

        image.file.seek(0)
        img_data = image.file.read()

        if not img_data:
            raise ValueError("Imagem não foi lida corretamente.")

        img_array = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError("Falha ao decodificar a imagem após o pré-processamento.")

        imgPreprocessed = preprocess_image(img)

        # Corrigir perspectiva
        img_scan = correct_perspective(imgPreprocessed, vertices)

        # Salvar a imagem processada em memória para o upload
        _, img_encoded = cv2.imencode('.jpg', img_scan)
        img_bytes = io.BytesIO(img_encoded.tobytes())

        # Criar um novo UploadFile simulando o arquivo processado
        processed_image = UploadFile(
            filename=f"processed_{image.filename}",
            file=img_bytes,
            headers={"content-type": "image/jpeg"}
        )

        # Fazer o upload da imagem processada para o bucket
        imagem_url = upload_to_gcs(processed_image)

        return {
            "imagem_url": imagem_url,
            "valor_pago": valor_pago,
            "data_extraida": data_extraida
        }
    except Exception as e:
        print(f"Erro ao processar a imagem: {e}")
        return None

# Função para extrair o valor e a data do texto
def extract_value_and_date(text):
    valor_regex = r"\d{1,3}(?:[.,]\d{3})*[.,]\d{2}"
    date_regex = r"\b(\d{2}/\d{2}/\d{4})\b|\b(\d{4}-\d{2}-\d{2})\b"
    
    valores = re.findall(valor_regex, text)
    datas = re.findall(date_regex, text)

    keywords = ["VALOR TOTAL", "VALOR A PAGAR", "VALOR PAGO"]
    lower_text = text.lower()
    valor_pago = 0.0

    def clean_value(value):
        if "," in value and "." in value:
            if value.index(",") > value.index("."):
                return float(value.replace(".", "").replace(",", "."))
            else:
                return float(value.replace(",", ""))
        elif "," in value:
            return float(value.replace(",", "."))
        else:
            return float(value)

    for keyword in keywords:
        keyword_index = lower_text.find(keyword.lower())
        if keyword_index != -1:
            substring_around = text[max(0, keyword_index - 50):keyword_index + 50]
            valores_proximos = re.findall(valor_regex, substring_around)
            if valores_proximos:
                valores_proximos_convertidos = [clean_value(v) for v in valores_proximos]
                valor_pago = max(valores_proximos_convertidos)
                break

    if not valor_pago and valores:
        valor_pago = max([clean_value(v) for v in valores])

    data_extraida = datas[0][0] if datas else ""

    valor_pago_formatado = f"{valor_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return valor_pago_formatado, data_extraida
