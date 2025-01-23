import cv2
import numpy as np
import requests

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
    src_points = np.float32([  # Padrão quadrado no caso
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

def execute_scan(image_url: str):
    """
    Função para digitalizar a imagem. Aqui você pode processar a imagem diretamente
    pela URL, sem precisar fazer o download local.
    """
    # Obter a imagem da URL
    img_data = requests.get(image_url).content
    img_array = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)

    # Se você quiser corrigir a perspectiva com base em vértices detectados (exemplo)
    # Simulação de pontos de verificação (você pode querer extrair esses pontos dinamicamente)
    vertices = [(100, 200), (400, 200), (400, 400), (100, 400)]  # Exemplo de vértices
    img_scan = correct_perspective(img, vertices)

    # Salvar imagem digitalizada em algum lugar (por exemplo, temporariamente)
    image_scan_path = "/tmp/scanned_image.jpg"  # Ajuste conforme necessário
    cv2.imwrite(image_scan_path, img_scan)
    
    return image_scan_path
