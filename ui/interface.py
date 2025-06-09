import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.camera import Camera
from kivy.uix.image import Image as KivyImage # Renomeado para evitar conflito com Image do Pillow ou OpenCV
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
import numpy as np
import threading # Para rodar o processamento da câmera em uma thread separada
from queue import Queue # Para comunicação segura entre threads

# Importar o ProductDetector
from vision.product_detector import ProductDetector

# Variável global para armazenar o detector e a fila de comunicação
product_detector = None
frame_queue = Queue(maxsize=1) # Fila para passar frames da câmera para a thread de detecção
detection_queue = Queue(maxsize=1) # Fila para passar detecções da thread de detecção para a UI

class ShoppingCart(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Layout principal vertical
        main_layout = BoxLayout(orientation='vertical')
        # Layout horizontal separado
        content_layout = BoxLayout(orientation='horizontal', size_hint_y=0.8)
        
        # Parte esquerda - Visualização da câmera (50% da largura)
        # Substituímos Camera por Image para ter controle sobre a textura
        self.camera_display = KivyImage(size_hint_x=0.6, allow_stretch=True, keep_ratio=False)
        content_layout.add_widget(self.camera_display)
        
        # Parte direita - Lista de produtos (50% da largura)
        self.product_list = Label(text='Produtos identificados aparecerão aqui\n',
                                  size_hint_x=0.4,
                                  valign='top', # Alinha o texto no topo
                                  padding_x=10, # Adiciona padding horizontal
                                  text_size=(self.width * 0.4 - 20, None) # Limita a largura do texto
                                 )
        content_layout.add_widget(self.product_list)
        
        # Adiciona a área bipartida ao layout principal
        main_layout.add_widget(content_layout)
        
        # Área de botões (20% da tela)
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        self.checkout_btn = Button(text='Finalizar Compra')
        self.checkout_btn.bind(on_press=self.checkout)
        btn_layout.add_widget(self.checkout_btn)
        
        # Adiciona o rodapé ao layout principal
        main_layout.add_widget(btn_layout)
        
        self.add_widget(main_layout)

        # Inicializa a câmera OpenCV e agenda a captura
        self.capture = None
        self.detector = None
        self.event = None # Para agendar a atualização da câmera

    def on_enter(self, *args):
        """Chamado quando esta tela se torna ativa."""
        global product_detector
        # Inicializa o detector de produtos apenas uma vez
        if product_detector is None:
            try:
                product_detector = ProductDetector()
            except Exception as e:
                print(f"Não foi possível inicializar o ProductDetector: {e}")
                # Exibir uma mensagem de erro na UI
                self.product_list.text = f"Erro: {e}\nNão foi possível iniciar a detecção."
                return

        self.detector = product_detector
        self.capture = cv2.VideoCapture(0) # Inicia a captura de vídeo
        if not self.capture.isOpened():
            print("Erro ao abrir a câmera!")
            self.product_list.text = "Erro: Não foi possível acessar a câmera."
            return

        # Ajusta a resolução da captura (opcional, pode ser limitada pela câmera)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # Agenda a função de atualização da câmera
        self.event = Clock.schedule_interval(self.update_camera_frame, 1.0 / 30.0) # 30 FPS

        # Inicia a thread de processamento da visão
        self.vision_thread = threading.Thread(target=self.run_vision_processing, daemon=True)
        self.vision_thread.start()
        
        # Agenda a atualização da lista de produtos na UI
        Clock.schedule_interval(self.update_product_list, 1.0) # Atualiza a cada 1 segundo

    def on_leave(self, *args):
        """Chamado quando esta tela deixa de ser ativa."""
        if self.event:
            self.event.cancel() # Cancela o agendamento da câmera
        if self.capture:
            self.capture.release() # Libera a câmera do OpenCV
        # Não precisa parar a thread explicitamente se ela for daemon
        
    def update_camera_frame(self, dt):
        """Captura um frame da câmera e o exibe."""
        ret, frame = self.capture.read()
        if ret:
            # Coloca o frame na fila para ser processado pela thread de visão
            try:
                frame_queue.put_nowait(frame) # Tenta colocar sem bloquear
            except Exception:
                pass # Se a fila estiver cheia, ignora o frame (reduz o backlog)

            # Para exibir o frame na UI (mesmo sem detecções ainda)
            buf = cv2.flip(frame, 0).tobytes() # Inverte e converte para bytes
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera_display.texture = image_texture
        else:
            print("Não foi possível ler o frame da câmera.")

    def run_vision_processing(self):
        """Função que roda na thread separada para processar frames."""
        while True:
            try:
                frame = frame_queue.get(timeout=0.1) # Pega um frame da fila (com timeout)
                if self.detector:
                    detections, frame_with_detections = self.detector.detect_products(frame)
                    
                    # Coloca as detecções e o frame processado na fila para a UI
                    try:
                        detection_queue.put_nowait((detections, frame_with_detections))
                    except Exception:
                        pass # Se a fila estiver cheia, ignora (UI está lenta)
                frame_queue.task_done() # Marca a tarefa como concluída na fila
            except Exception as e:
                # print(f"Thread de visão esperando por frames ou erro: {e}")
                pass # A fila pode estar vazia ou a thread pode estar desligando

    def update_product_list(self, dt):
        """Atualiza a lista de produtos na UI com base nas detecções."""
        try:
            detections, frame_with_detections = detection_queue.get_nowait()
            
            # Atualiza o display da câmera com o frame que tem as detecções desenhadas
            # A imagem do YOLOv8 (frame_with_detections) já vem em BGR
            buf = cv2.flip(frame_with_detections, 0).tobytes()
            image_texture = Texture.create(size=(frame_with_detections.shape[1], frame_with_detections.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera_display.texture = image_texture

            # Processa as detecções e atualiza a lista de produtos
            product_counts = {}
            for d in detections:
                product_name = d['class']
                if product_name in product_counts:
                    product_counts[product_name] += 1
                else:
                    product_counts[product_name] = 1
            
            list_text = "🛒 Produtos Identificados:\n\n"
            if not product_counts:
                list_text += "Nenhum produto detectado."
            else:
                for product, count in product_counts.items():
                    list_text += f"- {product.capitalize()}: {count}\n"
            
            self.product_list.text = list_text
            
            detection_queue.task_done()
        except Exception:
            pass # Fila de detecções vazia ou erro ao processar

    def checkout(self, instance):
        self.manager.current = 'checkout'

# As outras classes (CheckOut, PixPaymentScreen, CardWaitingScreen) permanecem as mesmas
# ... (código existente para CheckOut, PixPaymentScreen, CardWaitingScreen) ...

class CheckOut(Screen):
    # ... (Seu código existente para CheckOut) ...
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Layout principal vertical
        main_layout = BoxLayout(orientation='vertical')
        
        # Label de instrução
        self.payment_label = Label(text='Selecione o método de pagamento:', 
                                   size_hint_y=0.2)
        main_layout.add_widget(self.payment_label)
        
        # Layout de botões de pagamento (60% da tela)
        payment_layout = BoxLayout(orientation='horizontal', size_hint_y=0.6)
        
        self.pix_btn = Button(text='PIX')
        self.pix_btn.bind(on_press=lambda x: self.process_payment('PIX'))
        payment_layout.add_widget(self.pix_btn)
        
        self.credit_btn = Button(text='Cartão de Crédito')
        self.credit_btn.bind(on_press=lambda x: self.process_payment('Cartão de Crédito'))
        payment_layout.add_widget(self.credit_btn)
        
        self.debit_btn = Button(text='Cartão de Débito')
        self.debit_btn.bind(on_press=lambda x: self.process_payment('Cartão de Débito'))
        payment_layout.add_widget(self.debit_btn)
        
        main_layout.add_widget(payment_layout)
        
        # Botão voltar (20% da tela)
        back_btn = Button(text='Voltar', size_hint_y=0.2)
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
    
    def process_payment(self, method):
        if method == 'PIX':
            self.manager.current = 'pix_payment'
        else:
            self.manager.current = 'card_waiting'
            # Configura o texto com o método de pagamento selecionado
            card_screen = self.manager.get_screen('card_waiting')
            card_screen.update_payment_method(method)
    
    def go_back(self, instance):
        self.manager.current = 'shopping'

class PixPaymentScreen(Screen):
    # ... (Seu código existente para PixPaymentScreen) ...
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical')
        
        # Título
        title = Label(text='Pagamento via PIX', size_hint_y=0.2, font_size='20sp')
        layout.add_widget(title)
        
        # QR Code (simulado)
        self.qr_code = KivyImage(source='', size_hint_y=0.5)  # Você pode substituir por um QR code real
        layout.add_widget(self.qr_code)
        
        # Instruções
        instructions = Label(text='Escaneie o QR Code acima usando seu aplicativo de pagamento\n'
                                  'Pagamento válido por 30 minutos',
                                  size_hint_y=0.2,
                                  halign='center')
        layout.add_widget(instructions)
        
        # Valor total
        self.total_label = Label(text='Total: R$ 0,00', size_hint_y=0.1)
        layout.add_widget(self.total_label)
        
        # Botão de voltar
        back_btn = Button(text='Voltar', size_hint_y=0.1)
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def on_enter(self):
        # Simula a geração de um QR Code (na prática, você usaria uma biblioteca para gerar o QR)
        self.qr_code.source = 'qr_placeholder.png'  # Substitua por um QR code real
        # Aqui você atualizaria o valor total também
        self.total_label.text = 'Total: R$ 99,99'  # Substitua pelo valor real
    
    def go_back(self, instance):
        self.manager.current = 'checkout'

class CardWaitingScreen(Screen):
    # ... (Seu código existente para CardWaitingScreen) ...
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # Cor de fundo cinza claro
            self.rect = Rectangle(size=self.size, pos=self.pos)
        
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        layout = BoxLayout(orientation='vertical')
        
        # Ícone de cartão (simulado)
        self.card_icon = Label(text='💳', font_size='50sp', size_hint_y=0.3)
        layout.add_widget(self.card_icon)
        
        # Instruções
        self.instructions = Label(text='Por favor, faça o pagamento na máquina de cartão ao lado',
                                  size_hint_y=0.3,
                                  halign='center',
                                  font_size='18sp')
        layout.add_widget(self.instructions)
        
        # Método de pagamento
        self.payment_method = Label(text='', size_hint_y=0.2, font_size='16sp')
        layout.add_widget(self.payment_method)
        
        # Status
        self.status_label = Label(text='Aguardando pagamento...', size_hint_y=0.2)
        layout.add_widget(self.status_label)
        
        self.add_widget(layout)
    
    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos
    
    def update_payment_method(self, method):
        self.payment_method.text = f'Método: {method}'
    
    def on_enter(self):
        # Simula o processamento do pagamento
        Clock.schedule_once(self.simulate_payment, 5)
    
    def simulate_payment(self, dt):
        # Esta função seria substituída pela verificação real do pagamento
        self.status_label.text = 'Pagamento aprovado!'
        self.card_icon.text = '✅'
        Clock.schedule_once(lambda x: self.manager.current == 'shopping', 2)

class AITotemApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ShoppingCart(name='shopping'))
        sm.add_widget(CheckOut(name='checkout'))
        sm.add_widget(PixPaymentScreen(name='pix_payment'))
        sm.add_widget(CardWaitingScreen(name='card_waiting'))
        return sm

if __name__ == '__main__':
    AITotemApp().run()