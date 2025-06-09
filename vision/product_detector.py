import cv2
from ultralytics import YOLO
import numpy as np
from pathlib import Path

class ProductDetector:
    def __init__(self):
        try:
            project_root = Path(__file__).resolve().parents[1] 
           
            self.model_path = project_root / "runs" / "detect" / "fruits_yolo_retrain" / "weights" / "best.pt"
            
            if not self.model_path.exists():
                self.model_path = project_root / "runs" / "detect" / "fruits_yolo3" / "weights" / "best.pt"
                if not self.model_path.exists():
                    raise FileNotFoundError(f"Modelo não encontrado em: {project_root / 'runs' / 'detect' / 'fruits_yolo_retrain' / 'weights' / 'best.pt'} ou {project_root / 'runs' / 'detect' / 'fruits_yolo3' / 'weights' / 'best.pt'}")


            self.model = YOLO(str(self.model_path))
            print(f"Modelo YOLO carregado com sucesso de: {self.model_path}")
            
            
            # limiar de confiança: reduzi para ser menos restritivo.
            self.model.conf = 0.70 

        
            self.model.iou = 0.25 

        except Exception as e:
            print(f"Erro ao carregar o modelo YOLO: {e}")
            raise # relança a exceção para que o Kivy saiba que houve um erro na inicialização

        # as classes são carregadas do próprio modelo YOLO
        self.class_names = self.model.names if hasattr(self.model, 'names') else ['produto_desconhecido']
        # converte os valores do dicionário para uma lista de strings
        if isinstance(self.class_names, dict):
            self.class_names = list(self.class_names.values())
        
    def detect_products(self, frame):
        results = self.model(frame) 
        detections = []
        
        # iterar sobre os resultados (pode haver mais de um se batch for maior que 1)
        for result in results:
            if result.boxes: # verifica se há caixas detectadas
                boxes = result.boxes.xyxy.cpu().numpy()
                confs = result.boxes.conf.cpu().numpy()
                cls_ids = result.boxes.cls.cpu().numpy().astype(int)
                
                for box, conf, cls_id in zip(boxes, confs, cls_ids):
                    class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f'classe_{cls_id}'
                    detections.append({
                        'class': class_name,
                        'confidence': float(conf),
                        'bbox': box.tolist() # coordenadas [x1, y1, x2, y2]
                    })
            
            # o método .plot() desenha as caixas e labels no frame
            frame_with_detections = result.plot()
                
        return detections, frame_with_detections