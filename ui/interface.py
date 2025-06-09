from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock

class ShoppingCart(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Layout principal vertical
        main_layout = BoxLayout(orientation='vertical')
        #Layout horizontal separado
        content_layout = BoxLayout(orientation='horizontal', size_hint_y=0.8)
        
        # Parte esquerda - Visualização da câmera (50% da largura)
        self.camera_view = Camera(resolution=(640, 480), size_hint_x=0.6) 
        self.camera_view.play = True
        content_layout.add_widget(self.camera_view)
        
        # Parte direita - Lista de produtos (50% da largura)
        self.product_list = Label(text='Produtos identificados aparecerão aqui\n',
                                size_hint_x=0.4)
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
    
    def checkout(self, instance):
        self.manager.current = 'checkout'

class CheckOut(Screen):
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
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical')
        
        # Título
        title = Label(text='Pagamento via PIX', size_hint_y=0.2, font_size='20sp')
        layout.add_widget(title)
        
        # QR Code (simulado)
        self.qr_code = Image(source='', size_hint_y=0.5)  # Você pode substituir por um QR code real
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