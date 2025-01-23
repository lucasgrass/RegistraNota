import cv2
import numpy as np
import io
import requests
import base64
import re

import os
from dotenv import load_dotenv

API_KEY = os.getenv('API_KEY')

def preprocess_image(img):
    """
    Realiza pré-processamento para melhorar a detecção de bordas.
    """
    imgGray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    imgBlur = cv2.GaussianBlur(imgGray, (5, 5), 1)
    return imgBlur

def detect_text_and_contours(API_KEY, image_path):
    """
    Detecta texto e retorna contornos usando a Google Vision API com uma API Key.
    """
    # Carregar a imagem como bytes
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()

    # Codificar a imagem em Base64
    base64_image = base64.b64encode(content).decode('utf-8')

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
    Funciona independentemente do uso de ponto ou vírgula.
    """
    # Regex para valores monetários (com ponto ou vírgula)
    valor_regex = r"\d{1,3}(?:[.,]\d{3})*[.,]\d{2}"
    date_regex = r"\b(\d{2}/\d{2}/\d{4})\b|\b(\d{4}-\d{2}-\d{2})\b"  # Regex para datas

    # Encontrar todos os valores monetários e datas no texto
    valores = re.findall(valor_regex, text)
    datas = re.findall(date_regex, text)

    # Palavras-chave relevantes
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
            # Buscar valores próximos à palavra-chave
            substring_around = text[max(0, keyword_index - 50):keyword_index + 50]
            valores_proximos = re.findall(valor_regex, substring_around)
            if valores_proximos:
                # Selecionar maior valor próximo, corrigindo separadores
                valores_proximos_convertidos = [clean_value(v) for v in valores_proximos]
                valor_pago = max(valores_proximos_convertidos)
                break

    # Caso nenhuma palavra-chave seja encontrada, retorna o maior valor geral
    if not valor_pago and valores:
        valor_pago = max([clean_value(v) for v in valores])

    # Extrair a primeira data encontrada
    data_extraida = datas[0][0] if datas else ""

    # Corrigir exibição do valor no formato brasileiro
    valor_pago_formatado = f"{valor_pago:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    return valor_pago_formatado, data_extraida

def correct_perspective(img, vertices):
    """
    Corrige a perspectiva da imagem com base nos vértices detectados.
    """
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

def main(image_path, API_KEY):
    # Carregar a imagem
    img = cv2.imread(image_path)
    if img is None:
        print("Erro ao carregar a imagem.")
        return

    # Pré-processamento
    imgPreprocessed = preprocess_image(img)

    # Detectar texto e contornos
    vertices, text = detect_text_and_contours(API_KEY, image_path)
    if vertices is None:
        print("Nenhum contorno válido encontrado.")
        return

    # Corrigir perspectiva
    corrected_img = correct_perspective(img, vertices)

    # Extrair valor e data
    valor_pago, data_extraida = extract_value_and_date(text)
    print(f"Valor extraído: R$ {valor_pago}")
    print(f"Data extraída: {data_extraida}")

    # Exibir texto completo
    # print("Texto completo detectado:")
    # print(text)

    # Salvar imagem corrigida
    save_path = "imagem_corrigida.jpg"
    cv2.imwrite(save_path, corrected_img)
    print(f"Imagem corrigida salva como: {save_path}")
    cv2.imshow("Imagem Corrigida", corrected_img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

# Caminho para a imagem
image_path = "nota.jpeg"

main(image_path, API_KEY)
