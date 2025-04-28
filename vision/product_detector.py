import cv2
from ultralytics import YOLO
import numpy as np

class ProductDetector:
    def __init__(self, model_path='models/yolov8n_custom.pt'):
        self.model = YOLO(model_path)
        self.class_names = self.load_class_names()
        
    def load_class_names(self):
        # Carregar nomes das classes do seu dataset
        return ['product1', 'product2', 'product3']  # Exemplo
        
    def detect_products(self, frame):
        results = self.model(frame)
        detections = []
        
        for result in results:
            boxes = result.boxes.xyxy.cpu().numpy()
            confs = result.boxes.conf.cpu().numpy()
            cls_ids = result.boxes.cls.cpu().numpy().astype(int)
            
            for box, conf, cls_id in zip(boxes, confs, cls_ids):
                detections.append({
                    'class': self.class_names[cls_id],
                    'confidence': float(conf),
                    'bbox': box.tolist()
                })
                
        return detections