from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.camera import Camera



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
        self.pix_btn.bind(on_press=self.process_payment)
        payment_layout.add_widget(self.pix_btn)
        
        self.credit_btn = Button(text='Cartão de Crédito')
        self.credit_btn.bind(on_press=self.process_payment)
        payment_layout.add_widget(self.credit_btn)
        
        self.debit_btn = Button(text='Cartão de Débito')
        self.debit_btn.bind(on_press=self.process_payment)
        payment_layout.add_widget(self.debit_btn)
        
        main_layout.add_widget(payment_layout)
        
        # Botão voltar (20% da tela)
        back_btn = Button(text='Voltar', size_hint_y=0.2)
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
    
    def process_payment(self, instance):
        method = instance.text
        print(f"Processando pagamento via {method}")
    
    def go_back(self, instance):
        self.manager.current = 'shopping'

class AITotemApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(ShoppingCart(name='shopping'))
        sm.add_widget(CheckOut(name='checkout'))
        return sm

if __name__ == '__main__':
    AITotemApp().run()