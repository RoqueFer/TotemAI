import cv2
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.image import Image as KivyImage
from kivy.graphics.texture import Texture
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
from kivy.properties import DictProperty, NumericProperty, StringProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.metrics import dp

# <<< MUDANÇA AQUI >>> Importa a função do banco de dados
from database.connector import save_purchase 
import numpy as np
import threading
from queue import Queue, Empty
import time

# Importar o ProductDetector
from vision.product_detector import ProductDetector

# Variável global para armazenar o detector e a fila de comunicação
product_detector = None
frame_queue = Queue(maxsize=1)
detection_queue = Queue(maxsize=1)

# --- Definição dos Preços dos Produtos ---
PRODUCT_PRICES = {
    "Banana": 5.99,
    "Orange": 3.50,
    "Apple": 7.00,
    "Pineapple": 12.00,
    "Grapes": 7.00,
    "Kiwi": 5.35,
    "Mango": 3.82,
    "Sugerapple": 2.50,
    "Watermelon": 3.0,
}
UNKNOWN_PRODUCT_PRICE = 0.00

class ShoppingCart(Screen):
    cart_items = DictProperty({})
    total_price = NumericProperty(0.0)
    current_detection_info = StringProperty("Nenhuma fruta detectada.")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        main_layout = BoxLayout(orientation='vertical')
        content_layout = BoxLayout(orientation='horizontal', size_hint_y=0.8)
        
        self.camera_display = KivyImage(size_hint_x=0.6, allow_stretch=True, keep_ratio=False)
        content_layout.add_widget(self.camera_display)
        
        cart_layout = BoxLayout(orientation='vertical', size_hint_x=0.4, padding=dp(10), spacing=dp(5))
        cart_layout.add_widget(Label(text='🛒 Shopping Cart:', font_size='22sp', size_hint_y=None, height=dp(30), halign='left', text_size=(cart_layout.width, None)))
        
        self.product_list_scrollview = ScrollView(size_hint_y=0.8)
        self.cart_grid_layout = GridLayout(cols=1, size_hint_y=None, row_default_height=dp(30), row_force_default=True)
        self.cart_grid_layout.bind(minimum_height=self.cart_grid_layout.setter('height'))
        self.product_list_scrollview.add_widget(self.cart_grid_layout)
        cart_layout.add_widget(self.product_list_scrollview)

        self.detection_info_label = Label(text=self.current_detection_info, font_size='16sp', size_hint_y=None, height=dp(30), halign='left', text_size=(cart_layout.width, None))
        cart_layout.add_widget(self.detection_info_label)

        self.total_label = Label(text=f'Total: R$ {self.total_price:.2f}', font_size='24sp', bold=True, size_hint_y=None, height=dp(50), color=(0.2, 0.8, 0.2, 1))
        cart_layout.add_widget(self.total_label)
        content_layout.add_widget(cart_layout)
        
        main_layout.add_widget(content_layout)
        
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        self.checkout_btn = Button(text='Checkout')
        self.checkout_btn.bind(on_press=self.checkout)
        btn_layout.add_widget(self.checkout_btn)
        main_layout.add_widget(btn_layout)
        
        self.add_widget(main_layout)

        self.capture = None
        self.detector = None
        self.camera_event = None
        self.list_update_event = None
        self.detected_products_history = {}
        self.HISTORY_TIMEOUT = 1.0

        self.bind(cart_items=self.update_cart_display)
        self.bind(total_price=self.update_total_label_text)
        self.bind(current_detection_info=self.detection_info_label.setter('text'))

    def update_total_label_text(self, instance, value):
        self.total_label.text = f'Total: R$ {value:.2f}'

    def on_enter(self, *args):
        global product_detector
        if product_detector is None:
            try:
                product_detector = ProductDetector()
            except Exception as e:
                print(f"Failed to initialize ProductDetector: {e}")
                self.current_detection_info = f"Error: {e}\nFailed to start detection."
                return

        self.detector = product_detector
        self.capture = cv2.VideoCapture(0)
        if not self.capture.isOpened():
            print("Error opening camera!")
            self.current_detection_info = "Error: Could not access camera."
            return

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

        # <<< MUDANÇA AQUI >>> Reduzindo FPS para melhorar performance
        self.camera_event = Clock.schedule_interval(self.update_camera_frame, 1.0 / 20.0)
        
        self.vision_thread = threading.Thread(target=self.run_vision_processing, daemon=True)
        self.vision_thread.start()
        
        self.list_update_event = Clock.schedule_interval(self.process_detection_results, 0.1) 

    def on_leave(self, *args):
        if self.camera_event:
            self.camera_event.cancel()
        if self.list_update_event:
            self.list_update_event.cancel()
        if self.capture:
            self.capture.release()

    def update_camera_frame(self, dt):
        ret, frame = self.capture.read()
        if ret:
            try:
                frame_queue.put_nowait(frame) 
            except Exception:
                pass 

            buf = cv2.flip(frame, 0).tobytes()
            image_texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera_display.texture = image_texture
        else:
            print("Could not read frame from camera.")

    def run_vision_processing(self):
        while True:
            try:
                frame = frame_queue.get(timeout=0.5) 
                if self.detector:
                    detections, frame_with_detections = self.detector.detect_products(frame)
                    try:
                        detection_queue.put_nowait((detections, frame_with_detections))
                    except Exception:
                        pass
                frame_queue.task_done()
            except Empty:
                continue
            except Exception as e:
                print(f"Error in vision thread: {e}")
                break

    def process_detection_results(self, dt):
        try:
            detections, frame_with_detections = detection_queue.get_nowait()
            
            buf = cv2.flip(frame_with_detections, 0).tobytes()
            image_texture = Texture.create(size=(frame_with_detections.shape[1], frame_with_detections.shape[0]), colorfmt='bgr')
            image_texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
            self.camera_display.texture = image_texture

            self.update_cart_from_detections(detections)
        except Empty: 
            self.update_cart_from_detections([]) 
        except Exception as e:
            print(f"Error processing detections for UI: {e}")

    def update_cart_from_detections(self, detections):
        current_time = time.time()
        
        detected_in_current_frame = set()
        for d in detections:
            product_name = d['class']
            self.detected_products_history[product_name] = current_time
            detected_in_current_frame.add(product_name)

        if detections:
            best_detection = max(detections, key=lambda x: x['confidence'])
            self.current_detection_info = f"Detected: {best_detection['class'].capitalize()} ({best_detection['confidence']:.2f})"
        else:
            if self.detected_products_history:
                most_recent_product = max(self.detected_products_history.items(), key=lambda item: item[1])[0]
                self.current_detection_info = f"Waiting... (Last: {most_recent_product.capitalize()})"
            else:
                self.current_detection_info = "No fruit detected."
        
        products_to_remove = [product for product, timestamp in list(self.detected_products_history.items()) if current_time - timestamp > self.HISTORY_TIMEOUT]
        for product in products_to_remove:
            del self.detected_products_history[product]

        new_cart_items = {}
        new_total_price = 0.0
        
        for product_name in self.detected_products_history.keys():
            count_in_current_frame = sum(1 for p in detections if p['class'] == product_name)
            quantity = count_in_current_frame if count_in_current_frame > 0 else 1 
            new_cart_items[product_name] = quantity
            price_per_unit = PRODUCT_PRICES.get(product_name, UNKNOWN_PRODUCT_PRICE)
            new_total_price += quantity * price_per_unit

        self.cart_items = new_cart_items
        self.total_price = new_total_price

    def update_cart_display(self, instance, value):
        self.cart_grid_layout.clear_widgets()
        if not value:
            self.cart_grid_layout.add_widget(Label(text='No products detected.', font_size='18sp', color=(1, 1, 1, 0.7)))
        else:
            for item_name, quantity in value.items():
                price_per_unit = PRODUCT_PRICES.get(item_name, UNKNOWN_PRODUCT_PRICE)
                item_total = quantity * price_per_unit
                item_label = Label(
                    text=f'{item_name.capitalize()}: {quantity} unit(s) - R$ {item_total:.2f}',
                    font_size='18sp', color=(1, 1, 1, 1), halign='left',
                    text_size=(self.cart_grid_layout.width - dp(20), None)
                )
                self.cart_grid_layout.add_widget(item_label)

    def checkout(self, instance):
        checkout_screen = self.manager.get_screen('checkout')
        checkout_screen.set_cart_details(self.cart_items, self.total_price)
        self.manager.current = 'checkout'

class CheckOut(Screen):
    total_checkout_price = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        main_layout = BoxLayout(orientation='vertical')
        self.payment_label = Label(text='Select payment method:', size_hint_y=0.2, font_size='20sp')
        main_layout.add_widget(self.payment_label)
        self.checkout_total_display = Label(text=f'Total Purchase: R$ {self.total_checkout_price:.2f}',
                                          font_size='25sp', bold=True, color=(0.2, 0.8, 0.2, 1),
                                          size_hint_y=0.1)
        main_layout.add_widget(self.checkout_total_display)
        payment_layout = BoxLayout(orientation='horizontal', size_hint_y=0.5)
        self.pix_btn = Button(text='PIX', font_size='20sp')
        self.pix_btn.bind(on_press=lambda x: self.process_payment('PIX'))
        payment_layout.add_widget(self.pix_btn)
        self.credit_btn = Button(text='Credit Card', font_size='20sp')
        self.credit_btn.bind(on_press=lambda x: self.process_payment('Credit Card'))
        payment_layout.add_widget(self.credit_btn)
        self.debit_btn = Button(text='Debit Card', font_size='20sp')
        self.debit_btn.bind(on_press=lambda x: self.process_payment('Debit Card'))
        payment_layout.add_widget(self.debit_btn)
        main_layout.add_widget(payment_layout)
        back_btn = Button(text='Back', size_hint_y=0.2, font_size='20sp')
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        self.add_widget(main_layout)
        self.bind(total_checkout_price=self.update_checkout_total_display_text)

    def update_checkout_total_display_text(self, instance, value):
        self.checkout_total_display.text = f'Total Purchase: R$ {value:.2f}'

    def set_cart_details(self, cart_items, total_price):
        self.cart_items_for_checkout = cart_items
        self.total_checkout_price = total_price

    # <<< MUDANÇA AQUI >>> Lógica de pagamento totalmente refeita
    def process_payment(self, method):
        if method == 'PIX':
            pix_screen = self.manager.get_screen('pix_payment')
            pix_screen.set_details(
                cart_items=self.cart_items_for_checkout,
                total=self.total_checkout_price
            )
            self.manager.current = 'pix_payment'
        else: # Credit or Debit Card
            card_screen = self.manager.get_screen('card_waiting')
            card_screen.set_details(
                cart_items=self.cart_items_for_checkout,
                total=self.total_checkout_price,
                method=method
            )
            self.manager.current = 'card_waiting'
            
    def go_back(self, instance):
        self.manager.current = 'shopping'

class PixPaymentScreen(Screen):
    total_display_pix = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cart_items = {} # <<< MUDANÇA AQUI >>> Adicionado para guardar o carrinho
        layout = BoxLayout(orientation='vertical')
        title = Label(text='PIX Payment', size_hint_y=0.2, font_size='25sp', bold=True)
        layout.add_widget(title)
        self.qr_code = KivyImage(source='fgbOcu.png', size_hint_y=0.4, allow_stretch=True, keep_ratio=True) 
        layout.add_widget(self.qr_code)
        instructions = Label(text='Scan the QR Code to pay', size_hint_y=0.1, font_size='18sp', halign='center')
        layout.add_widget(instructions)
        self.total_label = Label(text=f'Total: R$ {self.total_display_pix:.2f}', size_hint_y=0.1, font_size='25sp', bold=True, color=(0.2, 0.8, 0.2, 1))
        layout.add_widget(self.total_label)

        # <<< MUDANÇA AQUI >>> Adicionado botão de confirmação
        btn_layout = BoxLayout(size_hint_y=0.2, padding=dp(10), spacing=dp(10))
        confirm_btn = Button(text='Confirm Payment', font_size='20sp')
        confirm_btn.bind(on_press=self.confirm_pix_payment)
        btn_layout.add_widget(confirm_btn)
        back_btn = Button(text='Back', font_size='20sp')
        back_btn.bind(on_press=self.go_back)
        btn_layout.add_widget(back_btn)
        layout.add_widget(btn_layout)
        
        self.add_widget(layout)
        self.bind(total_display_pix=self.update_pix_total_label_text)

    def update_pix_total_label_text(self, instance, value):
        self.total_label.text = f'Total: R$ {value:.2f}'
    
    # <<< MUDANÇA AQUI >>> Novo método para receber detalhes
    def set_details(self, cart_items, total):
        self.cart_items = cart_items
        self.total_display_pix = total

    # <<< MUDANÇA AQUI >>> Novo método para confirmar e salvar
    def confirm_pix_payment(self, instance):
        purchase_id = save_purchase(
            cart_items=self.cart_items,
            total_price=self.total_display_pix,
            payment_method='PIX'
        )
        if purchase_id:
            thank_you_screen = self.manager.get_screen('thank_you')
            thank_you_screen.show_confirmation(purchase_id)
            self.manager.current = 'thank_you'

    def go_back(self, instance):
        self.manager.current = 'checkout'

class CardWaitingScreen(Screen):
    total_display_card = NumericProperty(0.0)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # <<< MUDANÇA AQUI >>> Adicionado para guardar detalhes da compra
        self.cart_items = {}
        self.payment_method_text = ''
        
        with self.canvas.before:
            Color(0.95, 0.95, 0.95, 1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(10))
        self.card_icon = Label(text='💳', font_size='80sp', size_hint_y=0.3)
        layout.add_widget(self.card_icon)
        self.instructions = Label(text='Please make the payment on the card machine',
                                  size_hint_y=0.3, font_size='20sp', halign='center')
        layout.add_widget(self.instructions)
        self.payment_method = Label(text='', size_hint_y=0.1, font_size='18sp')
        layout.add_widget(self.payment_method)
        self.total_label_card = Label(text=f'Total: R$ {self.total_display_card:.2f}', size_hint_y=0.1, font_size='25sp', bold=True, color=(0.2, 0.8, 0.2, 1))
        layout.add_widget(self.total_label_card)
        self.status_label = Label(text='Awaiting payment...', size_hint_y=0.2, font_size='20sp', color=(1,0.5,0,1))
        layout.add_widget(self.status_label)
        self.back_btn = Button(text='Back', size_hint_y=0.1, font_size='20sp')
        self.back_btn.bind(on_press=self.go_back_from_card_screen)
        layout.add_widget(self.back_btn)
        self.add_widget(layout)
        self.bind(total_display_card=self.update_card_total_label_text)
    
    def update_card_total_label_text(self, instance, value):
        self.total_label_card.text = f'Total: R$ {value:.2f}'

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos
    
    def update_payment_method(self, method):
        self.payment_method.text = f'Method: {method}'

    # <<< MUDANÇA AQUI >>> Novo método unificado para receber os detalhes
    def set_details(self, cart_items, total, method):
        self.cart_items = cart_items
        self.total_display_card = total
        self.payment_method_text = method
        self.update_payment_method(method)
    
    def on_enter(self):
        self.status_label.text = 'Awaiting payment...'
        self.status_label.color = (1,0.5,0,1)
        self.card_icon.text = '💳'
        Clock.schedule_once(self.simulate_payment, 5)

    # <<< MUDANÇA AQUI >>> Lógica de simulação refeita para salvar no DB e limpar carrinho
    def simulate_payment(self, dt):
        purchase_id = save_purchase(
            cart_items=self.cart_items,
            total_price=self.total_display_card,
            payment_method=self.payment_method_text
        )

        if purchase_id:
            # Navega para a tela de agradecimento
            thank_you_screen = self.manager.get_screen('thank_you')
            thank_you_screen.show_confirmation(purchase_id)
            self.manager.current = 'thank_you'
        else:
            self.status_label.text = 'Error saving purchase!'
            self.status_label.color = (1, 0, 0, 1)
            self.card_icon.text = '❌'
            # Volta para a tela de checkout em caso de erro
            Clock.schedule_once(lambda x: setattr(self.manager, 'current', 'checkout'), 3)

    def go_back_from_card_screen(self, instance):
        self.manager.current = 'checkout'

# <<< MUDANÇA AQUI >>> Nova tela de agradecimento
class ThankYouScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=dp(20), spacing=dp(20))
        self.icon_label = Label(text='✅', font_size='100sp', size_hint_y=0.4)
        self.message_label = Label(text='Thank you for your purchase!', font_size='30sp', size_hint_y=0.3, halign='center')
        self.purchase_id_label = Label(text='', font_size='20sp', size_hint_y=0.3, color=(0.8, 0.8, 0.8, 1))
        layout.add_widget(self.icon_label)
        layout.add_widget(self.message_label)
        layout.add_widget(self.purchase_id_label)
        self.add_widget(layout)

    def show_confirmation(self, purchase_id):
        self.purchase_id_label.text = f'Purchase ID: {purchase_id}'
    
    def on_enter(self):
        # Agenda o retorno para a tela de compras e limpa o carrinho
        Clock.schedule_once(self.go_to_shopping, 4) # Mostra a tela por 4 segundos

    def go_to_shopping(self, dt):
        shopping_screen = self.manager.get_screen('shopping')
        shopping_screen.cart_items = {} # Esvazia o carrinho
        shopping_screen.total_price = 0.0 # Zera o total
        shopping_screen.detected_products_history = {} # Limpa o histórico de detecção
        self.manager.current = 'shopping'

class AITotemApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ShoppingCart(name='shopping'))
        sm.add_widget(CheckOut(name='checkout'))
        sm.add_widget(PixPaymentScreen(name='pix_payment'))
        sm.add_widget(CardWaitingScreen(name='card_waiting'))
        # <<< MUDANÇA AQUI >>> Registra a nova tela
        sm.add_widget(ThankYouScreen(name='thank_you'))
        return sm