# import cv2 # Não é mais necessário importar cv2 aqui
# from vision.product_detector import ProductDetector # Não é mais necessário instanciar aqui
from database.connector import init_db
from ui.interface import AITotemApp
# import threading # Não é mais necessário importar threading aqui

# A lógica de run_vision_system será movida para interface.py
# def run_vision_system():
#     detector = ProductDetector()
#     cap = cv2.VideoCapture(0)  # Usar câmera padrão
    
#     while True:
#         ret, frame = cap.read()
#         if not ret:
#             break
            
#         detections = detector.detect_products(frame)
#         # Aqui você pode processar as detecções e atualizar a interface
        
#         cv2.imshow('AI-Totem', frame)
#         if cv2.waitKey(1) & 0xFF == ord('q'):
#             break
            
#     cap.release()
#     cv2.destroyAllWindows()

def main():
    # Inicializar banco de dados
    init_db()
    
    # A thread do sistema de visão será iniciada dentro da classe ShoppingCart
    # quando a tela for ativada (on_enter).
    # vision_thread = threading.Thread(target=run_vision_system)
    # vision_thread.daemon = True
    # vision_thread.start()
    
    # Iniciar interface do usuário
    AITotemApp().run()

if __name__ == '__main__':
    main()