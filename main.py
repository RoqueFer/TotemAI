import cv2
from vision.product_detector import ProductDetector
from database.connector import init_db
from ui.interface import AITotemApp
import threading

def run_vision_system():
    detector = ProductDetector()
    cap = cv2.VideoCapture(0)  # Usar câmera padrão
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        detections = detector.detect_products(frame)
        # Aqui você pode processar as detecções e atualizar a interface
        
        cv2.imshow('AI-Totem', frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
            
    cap.release()
    cv2.destroyAllWindows()

def main():
    # Inicializar banco de dados
    init_db()
    
    # Iniciar sistema de visão em thread separada
    vision_thread = threading.Thread(target=run_vision_system)
    vision_thread.daemon = True
    vision_thread.start()
    
    # Iniciar interface do usuário
    AITotemApp().run()

if __name__ == '__main__':
    main()