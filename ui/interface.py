from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label

class ShoppingCart(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        
        self.product_list = Label(text='Produtos identificados aparecerão aqui')
        self.add_widget(self.product_list)
        
        self.checkout_btn = Button(text='Finalizar Compra')
        self.checkout_btn.bind(on_press=self.checkout)
        self.add_widget(self.checkout_btn)
    
    def checkout(self, instance):
        print("Processando pagamento...")

class AITotemApp(App):
    def build(self):
        return ShoppingCart()

if __name__ == '__main__':
    AITotemApp().run()