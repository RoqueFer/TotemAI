import torch
import cv2
from pathlib import Path
from ultralytics import YOLO 

PROJECT_ROOT = Path("C:/AI_Totem/AI-Totem")


MODEL_PATH = PROJECT_ROOT / "runs" / "detect" / "fruits_yolo3" / "weights" / "best.pt"


try:
    modelo = YOLO(MODEL_PATH)
    print(f"Modelo carregado com sucesso de: {MODEL_PATH}")
except Exception as e:
    print(f"Erro ao carregar o modelo de {MODEL_PATH}: {e}")
    exit() 


modelo.conf = 0.25 
modelo.iou = 0.7   

# 3. Função para testar com uma imagem
def testar_imagem(caminho_imagem):
    
    caminho_imagem_path = Path(caminho_imagem)

    
    img = cv2.imread(str(caminho_imagem_path)) 

    if img is None:
        print(f"Erro: Não foi possível carregar a imagem em {caminho_imagem_path}")
        return

    print(f"\n✅ Imagem carregada: {caminho_imagem_path}")

   
    resultados = modelo.predict(source=img, save=False, conf=modelo.conf, iou=modelo.iou) 

    
    for r in resultados:
        
        if r.boxes:
            detecções_df = r.boxes.data.cpu().numpy() 
            print("\n📊 Detecções (xmin, ymin, xmax, ymax, confidence, class_id):")
           
            print(detecções_df) 

            )
            im_com_bboxes = r.plot()

           
            cv2.imshow("Detecções YOLOv8", im_com_bboxes)
            cv2.waitKey(0) 
            cv2.destroyAllWindows() 

            
            output_dir = PROJECT_ROOT / "teste_output"
            output_dir.mkdir(parents=True, exist_ok=True) 
            output_path = output_dir / f"deteccao_{caminho_imagem_path.name}"
            cv2.imwrite(str(output_path), im_com_bboxes)
            print(f"🖼️ Imagem com detecções salva em: {output_path}")

        else:
            print("❌ Nenhuma detecção encontrada para esta imagem.")
            
            cv2.imshow("Detecções YOLOv8", img)
            cv2.waitKey(0)
            cv2.destroyAllWindows()



if __name__ == "__main__":
    
    imagem_teste = PROJECT_ROOT / "tests" / "fotostestes" / "uva.jpg"
    
    testar_imagem(imagem_teste)