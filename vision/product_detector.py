import cv2
from ultralytics import YOLO
import numpy as np
from pathlib import Path

class ProductDetector:
    # O construtor não precisa de model_path como argumento se ele for sempre o mesmo
    # Ou se você quer um valor padrão, mas calculado dinamicamente
    def __init__(self):
        
        try:
            # Assumindo que a raiz do projeto é a pasta "AI-Totem"
            # Path(__file__).resolve() -> C:\Ai_Totem\AI-Totem\vision\product_detector.py
            # .parents[0] -> C:\Ai_Totem\AI-Totem\vision
            # .parents[1] -> C:\Ai_Totem\AI-Totem (Esta é a raiz do seu projeto)
            project_root = Path(__file__).resolve().parents[1] 

            # Agora construa o caminho para o seu best.pt a partir da raiz do projeto
            # ESTA É A LINHA CORRETA para definir self.model_path
            self.model_path = project_root / "runs" / "detect" / "fruits_yolo3" / "weights" / "best.pt"
            
            # OU se preferir usar o yolov8n.pt global que você tem:
            # self.model_path = project_root / "yolov8n.pt"

            if not self.model_path.exists():
                raise FileNotFoundError(f"Modelo não encontrado em: {self.model_path}")

            self.model = YOLO(str(self.model_path)) # str() necessário para YOLO
            print(f"Modelo YOLO carregado com sucesso de: {self.model_path}")
            
            # Configurações do modelo
            self.model.conf = 0.5  # Limiar de confiança
            self.model.iou = 0.45 # Limiar de IOU para Non-Maximum Suppression

        except Exception as e:
            print(f"Erro ao carregar o modelo YOLO: {e}")
            raise # Levante a exceção para que o app saiba que algo deu errado

        self.class_names = self.load_class_names()
        
    def load_class_names(self):
        if self.model and hasattr(self.model.names, 'values'):
            return list(self.model.names.values())
        return ['produto_desconhecido'] # Fallback
        
    def detect_products(self, frame):
        results = self.model(frame)
        detections = []
        
        for result in results:
            if result.boxes:
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                cls_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                for box, conf, cls_id in zip(boxes, confs, cls_ids):
                    class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f'classe_{cls_id}'
                    detections.append({
                        'class': class_name,
                        'confidence': float(conf),
                        'bbox': box.tolist()
                    })
            
            frame_with_detections = result.plot()
                
        return detections, frame_with_detections