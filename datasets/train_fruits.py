from ultralytics import YOLO
import os

# 1. Carregar modelo base
model = YOLO('yolov8n.pt') 

# 2. Treinar com o dataset
results = model.train(
    data=os.path.join(r'C:\Users\User\Desktop\AI-Totem\datasets', r'C:\Users\User\Desktop\AI-Totem\datasets\fruits_yolo', r'C:\Users\User\Desktop\AI-Totem\datasets\fruits_yolo\data.yaml'),
    epochs=100,
    imgsz=640,
    batch=8,
    name='fruits_yolo',
    save=True,
    pretrained=True
)

# 3. Exportar modelo treinado
model.export(format='onnx')  # Opcional para melhor performance