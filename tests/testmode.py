import torch
import cv2
from pathlib import Path
from ultralytics import YOLO # Importar a classe YOLO do ultralytics

# Caminho base do seu projeto (ajuste se necessário)
# Isso ajuda a construir caminhos relativos de forma mais robusta
PROJECT_ROOT = Path("C:/AI_Totem/AI-Totem")

# 1. Carregue seu modelo YOLO
# Recomendado: Usar o modelo 'best.pt' treinado com suas frutas
# Substitua pelo caminho correto do seu best.pt (o que você treinou)
MODEL_PATH = PROJECT_ROOT / "runs" / "detect" / "fruits_yolo3" / "weights" / "best.pt"

# Ou, se quiser testar o yolov8n.pt (modelo pré-treinado geral):
# MODEL_PATH = PROJECT_ROOT / "yolov8n.pt"

try:
    modelo = YOLO(MODEL_PATH)
    print(f"Modelo carregado com sucesso de: {MODEL_PATH}")
except Exception as e:
    print(f"Erro ao carregar o modelo de {MODEL_PATH}: {e}")
    exit() # Sai do script se o modelo não puder ser carregado

# 2. Configure limites de confiança
modelo.conf = 0.25 # Threshold mínimo para considerar uma detecção válida (0.25 é um bom valor inicial)
modelo.iou = 0.7   # Threshold de Intersection Over Union (para agrupar caixas - NMS)

# 3. Função para testar com uma imagem
def testar_imagem(caminho_imagem):
    # Converte o caminho para um objeto Path para melhor compatibilidade
    caminho_imagem_path = Path(caminho_imagem)

    # Carregue a imagem usando OpenCV
    img = cv2.imread(str(caminho_imagem_path)) # str() necessário para cv2.imread

    if img is None:
        print(f"Erro: Não foi possível carregar a imagem em {caminho_imagem_path}")
        return

    print(f"\n✅ Imagem carregada: {caminho_imagem_path}")

    # Execute a detecção
    # O método predict do YOLOv8 já cuida da conversão de cores e outros pré-processamentos
    resultados = modelo.predict(source=img, save=False, conf=modelo.conf, iou=modelo.iou) # save=False para não salvar automaticamente aqui

    # Iterar sobre os resultados (se houver múltiplas imagens no 'source')
    for r in resultados:
        # Mostre os resultados no console (formato Pandas DataFrame)
        # O YOLOv8 retorna os resultados como objetos 'Results' que contêm 'boxes'
        # que podem ser convertidos para pandas.
        if r.boxes: # Verifica se há detecções
            detecções_df = r.boxes.data.cpu().numpy() # Pega os dados dos boxes
            print("\n📊 Detecções (xmin, ymin, xmax, ymax, confidence, class_id):")
            # Para uma visualização mais amigável, você pode converter para DataFrame
            # e adicionar os nomes das classes se o modelo as tiver.
            # No entanto, a forma mais simples de ver é o próprio plot.
            print(detecções_df) # Mostra o array numpy

            # Plotar os resultados na imagem (desenha as bounding boxes)
            im_com_bboxes = r.plot() # Retorna a imagem com as caixas desenhadas

            # Mostre a imagem com detecções usando OpenCV
            cv2.imshow("Detecções YOLOv8", im_com_bboxes)
            cv2.waitKey(0) # Aguarda uma tecla ser pressionada
            cv2.destroyAllWindows() # Fecha a janela

            # Salve a imagem com detecções (opcional)
            output_dir = PROJECT_ROOT / "teste_output"
            output_dir.mkdir(parents=True, exist_ok=True) # Cria a pasta se não existir
            output_path = output_dir / f"deteccao_{caminho_imagem_path.name}"
            cv2.imwrite(str(output_path), im_com_bboxes)
            print(f"🖼️ Imagem com detecções salva em: {output_path}")

        else:
            print("❌ Nenhuma detecção encontrada para esta imagem.")
            # Se não houver detecções, ainda podemos mostrar a imagem original
            cv2.imshow("Detecções YOLOv8", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()


# 4. Teste!
if __name__ == "__main__":
    # Substitua pelo caminho da SUA imagem de teste usando o PROJECT_ROOT
    imagem_teste = PROJECT_ROOT / "tests" / "fotostestes" / "uva.jpg"
    
    testar_imagem(imagem_teste)