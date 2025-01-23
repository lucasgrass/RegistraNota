import requests
import cv2
import numpy as np
import base64
import os
from dotenv import load_dotenv
import re

load_dotenv()
API_KEY = os.getenv('API_KEY')

def preprocess_image(img):
    """
    Realiza pré-processamento para melhorar a detecção de bordas.
    """
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    return imgBlur

def detect_text_and_contours(API_KEY, image_url):
    """
    Detecta texto e retorna contornos usando a Google Vision API com uma API Key.
    """
    # Obter a imagem da URL (ou fazer download temporário)
    img_data = requests.get(image_url).content
    img_array = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    if img is None:
        print("Erro ao carregar a imagem.")
        return None, None

    imgPreprocessed = preprocess_image(img)

    # Codificar a imagem em Base64
    _, img_encoded = cv2.imencode('.jpg', imgPreprocessed)
    base64_image = base64.b64encode(img_encoded).decode('utf-8')

    # Configurar o payload para a API
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

def extract_value_and_date(text):
    """
    Extrai o maior valor monetário próximo às palavras-chave e a data do texto detectado.
    """
    valor_regex = r"\d{1,3}(?:[.,]\d{3})*[.,]\d{2}"
    date_regex = r"\b(\d{2}/\d{2}/\d{4})\b|\b(\d{4}-\d{2}-\d{2})\b"  # Regex para datas

    valores = re.findall(valor_regex, text)
    datas = re.findall(date_regex, text)

    keywords = ["VALOR TOTAL", "VALOR A PAGAR", "VALOR PAGO"]
    lower_text = text.lower()
    valor_pago = 0.0

    def clean_value(value):
        """
        Remove separadores incorretos e converte para float.
        """
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

def execute_ocr(image_url):
    """
    Função principal para realizar o OCR e extrair dados de uma imagem da URL.
    """
    vertices, text = detect_text_and_contours(API_KEY, image_url)
    if vertices is None:
        return {"valor": None, "data": None, "categoria": None}

    # Extrair valor e data
    valor_pago, data_extraida = extract_value_and_date(text)
    return {"valor": valor_pago, "data": data_extraida, "categoria": "Categoria Exemplo"}  # Adapte a categoria conforme necessário
