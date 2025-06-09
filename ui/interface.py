from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.camera import Camera
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle
from kivy.clock import Clock
import os

# Create dummy image files for demonstration if they don't exist
if not os.path.exists('qr_placeholder.png'):
    try:
        from PIL import Image as PILImage
        from PIL import ImageDraw

        # Create a simple white image with black text for QR code placeholder
        img = PILImage.new('RGB', (200, 200), color = 'white')
        d = ImageDraw.Draw(img)
        d.text((10,10), "Simulated QR Code", fill=(0,0,0))
        img.save("qr_placeholder.png")
        print("Generated dummy qr_placeholder.png")
    except ImportError:
        print("Pillow library not found. Please install it (`pip install Pillow`) or manually create 'qr_placeholder.png' for QR code simulation.")
        print("Using a blank image placeholder for QR code screen.")
        # Fallback if Pillow is not installed, the Image widget will simply be blank.

if not os.path.exists('card_placeholder.png'):
    try:
        from PIL import Image as PILImage
        from PIL import ImageDraw
        # Create a simple card outline for the card placeholder image
        img = PILImage.new('RGB', (200, 200), color = 'white')
        d = ImageDraw.Draw(img)
        d.rectangle([50, 70, 150, 130], outline="black", width=5) # Card body
        d.rectangle([60, 80, 140, 90], fill="black") # Magnetic stripe simulation
        img.save("card_placeholder.png")
        print("Generated dummy card_placeholder.png")
    except ImportError:
        print("Pillow library not found. Please install it (`pip install Pillow`) or manually create 'card_placeholder.png'.")

if not os.path.exists('checkmark_placeholder.png'):
    try:
        from PIL import Image as PILImage
        from PIL import ImageDraw
        # Create a simple green checkmark for the success placeholder image
        img = PILImage.new('RGB', (200, 200), color = 'white')
        d = ImageDraw.Draw(img)
        d.line([(50, 100), (90, 140), (150, 60)], fill="green", width=10) # Checkmark shape
        img.save("checkmark_placeholder.png")
        print("Generated dummy checkmark_placeholder.png")
    except ImportError:
        print("Pillow library not found. Please install it (`pip install Pillow`) or manually create 'checkmark_placeholder.png'.")


class ShoppingCart(Screen):
    """
    Tela principal do carrinho de compras, com visualização da câmera e lista de produtos.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Layout principal vertical
        main_layout = BoxLayout(orientation='vertical')
        
        # Layout horizontal para a visualização da câmera e a lista de produtos
        content_layout = BoxLayout(orientation='horizontal', size_hint_y=0.8)
        
        # Parte esquerda - Visualização da câmera (60% da largura)
        # resolution=(640, 480) define a resolução da câmera.
        self.camera_view = Camera(resolution=(640, 480), size_hint_x=0.6) 
        self.camera_view.play = True # Inicia a câmera
        content_layout.add_widget(self.camera_view)
        
        # Parte direita - Lista de produtos (40% da largura)
        self.product_list = Label(text='Produtos identificados aparecerão aqui\n',
                                  size_hint_x=0.4,
                                  valign='top', # Alinha o texto ao topo
                                  halign='left', # Alinha o texto à esquerda
                                  padding=[10, 10]) # Adiciona preenchimento
        content_layout.add_widget(self.product_list)
        
        # Adiciona a área bipartida ao layout principal
        main_layout.add_widget(content_layout)
        
        # Área de botões (20% da altura da tela)
        btn_layout = BoxLayout(orientation='horizontal', size_hint_y=0.2)
        self.checkout_btn = Button(text='Finalizar Compra', font_size='20sp')
        self.checkout_btn.bind(on_press=self.checkout)
        btn_layout.add_widget(self.checkout_btn)
        
        # Adiciona o rodapé ao layout principal
        main_layout.add_widget(btn_layout)
        
        self.add_widget(main_layout)
    
    def checkout(self, instance):
        """
        Função para navegar para a tela de checkout.
        """
        self.manager.current = 'checkout'

class CheckOut(Screen):
    """
    Tela de checkout para seleção do método de pagamento.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Layout principal vertical
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Label de instrução
        self.payment_label = Label(text='Selecione o método de pagamento:', 
                                   size_hint_y=0.2,
                                   font_size='22sp',
                                   halign='center',
                                   valign='middle')
        main_layout.add_widget(self.payment_label)
        
        # Layout de botões de pagamento (60% da altura da tela)
        payment_layout = BoxLayout(orientation='horizontal', size_hint_y=0.6, spacing=10)
        
        self.pix_btn = Button(text='PIX', font_size='24sp')
        self.pix_btn.bind(on_press=lambda x: self.process_payment('PIX'))
        payment_layout.add_widget(self.pix_btn)
        
        self.credit_btn = Button(text='Cartão de Crédito', font_size='24sp')
        self.credit_btn.bind(on_press=lambda x: self.process_payment('Cartão de Crédito'))
        payment_layout.add_widget(self.credit_btn)
        
        self.debit_btn = Button(text='Cartão de Débito', font_size='24sp')
        self.debit_btn.bind(on_press=lambda x: self.process_payment('Cartão de Débito'))
        payment_layout.add_widget(self.debit_btn)
        
        main_layout.add_widget(payment_layout)
        
        # Botão voltar (20% da altura da tela)
        back_btn = Button(text='Voltar', size_hint_y=0.2, font_size='20sp')
        back_btn.bind(on_press=self.go_back)
        main_layout.add_widget(back_btn)
        
        self.add_widget(main_layout)
    
    def process_payment(self, method):
        """
        Processa a seleção do método de pagamento e navega para a tela apropriada.
        """
        if method == 'PIX':
            self.manager.current = 'pix_payment'
        else:
            self.manager.current = 'card_waiting'
            # Configura o texto com o método de pagamento selecionado na tela de espera do cartão
            card_screen = self.manager.get_screen('card_waiting')
            card_screen.update_payment_method(method)
    
    def go_back(self, instance):
        """
        Função para voltar à tela do carrinho de compras.
        """
        self.manager.current = 'shopping'

class PixPaymentScreen(Screen):
    """
    Tela de pagamento PIX com QR Code simulado e instruções.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Título
        title = Label(text='Pagamento via PIX', size_hint_y=0.2, font_size='28sp', bold=True)
        layout.add_widget(title)
        
        # QR Code (simulado)
        # O source será definido em on_enter para garantir que a tela esteja visível.
        self.qr_code = Image(source='', size_hint=(0.7, 0.5), pos_hint={'center_x': 0.5}) 
        layout.add_widget(self.qr_code)
        
        # Instruções
        instructions = Label(text='Escaneie o QR Code acima usando seu aplicativo de pagamento\n'
                                  'Pagamento válido por 30 minutos',
                                  size_hint_y=0.2,
                                  halign='center',
                                  valign='middle',
                                  font_size='18sp')
        layout.add_widget(instructions)
        
        # Valor total
        self.total_label = Label(text='Total: R$ 0,00', size_hint_y=0.1, font_size='24sp', bold=True)
        layout.add_widget(self.total_label)
        
        # Botão de voltar
        back_btn = Button(text='Voltar', size_hint_y=0.1, font_size='20sp')
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)
        
        self.add_widget(layout)
    
    def on_enter(self):
        """
        Chamado quando a tela é exibida. Atualiza o QR Code e o valor total.
        """
        # Simula a geração de um QR Code. Na prática, você usaria uma biblioteca
        # (como `qrcode`) para gerar um QR code real a partir de dados de pagamento.
        self.qr_code.source = 'qr_placeholder.png'  # Caminho para uma imagem de QR code
        self.qr_code.reload() # Garante que a imagem seja recarregada
        
        # Aqui você atualizaria o valor total também, provavelmente obtido de um modelo de dados.
        self.total_label.text = 'Total: R$ 99,99'  # Substitua pelo valor real do carrinho
    
    def go_back(self, instance):
        """
        Função para voltar à tela de checkout.
        """
        self.manager.current = 'checkout'

class CardWaitingScreen(Screen):
    """
    Tela de espera de pagamento via cartão, com ícone e instruções.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Desenha um retângulo de fundo preto para combinar com o estilo geral
        with self.canvas.before:
            Color(0, 0, 0, 1)  
            self.rect = Rectangle(size=self.size, pos=self.pos)
        
        # Atualiza a posição e o tamanho do retângulo quando a tela muda
        self.bind(size=self._update_rect, pos=self._update_rect)
        
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        
        # Ícone de cartão (agora uma imagem placeholder)
        self.card_icon = Image(source='card_placeholder.png', size_hint=(0.4, 0.3), pos_hint={'center_x': 0.5}) 
        layout.add_widget(self.card_icon)
        
        # Instruções
        self.instructions = Label(text='Por favor, faça o pagamento na máquina de cartão ao lado',
                                  size_hint_y=0.3,
                                  halign='center',
                                  valign='middle',
                                  font_size='22sp',
                                  markup=True,
                                  color=(1,1,1,1)) # Cor branca para o texto
        layout.add_widget(self.instructions)
        
        # Método de pagamento
        self.payment_method = Label(text='', size_hint_y=0.2, font_size='20sp', halign='center', valign='middle', color=(1,1,1,1)) # Cor branca para o texto
        layout.add_widget(self.payment_method)
        
        # Status do pagamento
        self.status_label = Label(text='Aguardando pagamento...', size_hint_y=0.2, font_size='24sp', bold=True, color=(0.2, 0.5, 0.8, 1)) # Azul
        layout.add_widget(self.status_label)

        # Adiciona um botão para simular a aprovação (para fins de demonstração)
        self.simulate_btn = Button(text='Simular Aprovação', size_hint_y=0.1, font_size='18sp')
        self.simulate_btn.bind(on_press=lambda x: self.simulate_payment(0)) # Chama simulate_payment imediatamente
        layout.add_widget(self.simulate_btn)

        # Novo botão "Voltar"
        back_btn = Button(text='Voltar', size_hint_y=0.1, font_size='20sp')
        back_btn.bind(on_press=self.go_back)
        layout.add_widget(back_btn)

        self.add_widget(layout)
    
    def _update_rect(self, instance, value):
        """
        Atualiza o tamanho e a posição do retângulo de fundo.
        """
        self.rect.size = instance.size
        self.rect.pos = instance.pos
    
    def update_payment_method(self, method):
        """
        Atualiza o texto do método de pagamento exibido na tela.
        """
        self.payment_method.text = f'Método: {method}'
    
    def on_enter(self):
        """
        Chamado quando a tela é exibida. Redefine o status e agenda a simulação.
        """
        self.status_label.text = 'Aguardando pagamento...'
        self.card_icon.source = 'card_placeholder.png' # Define a imagem inicial do cartão
        self.card_icon.reload() # Recarrega a imagem para garantir que apareça
        self.status_label.color = (0.2, 0.5, 0.8, 1) # Azul novamente
        self.simulate_btn.opacity = 1 # Garante que o botão de simulação esteja visível
        self.simulate_btn.disabled = False # Habilita o botão de simulação
        # Remove qualquer agendamento anterior para evitar múltiplas chamadas
        Clock.unschedule(self.simulate_payment)
    
    def simulate_payment(self, dt):
        """
        Simula o resultado do pagamento (aprovado ou reprovado).
        Esta função seria substituída pela verificação real do status do pagamento
        com um terminal de cartão de crédito.
        """
        self.status_label.text = 'Pagamento aprovado!'
        self.card_icon.source = 'checkmark_placeholder.png' # Altera para a imagem de checkmark
        self.card_icon.reload() # Recarrega a imagem
        self.status_label.color = (0, 0.8, 0, 1) # Cor verde para aprovado
        self.simulate_btn.opacity = 0 # Esconde o botão após a simulação
        self.simulate_btn.disabled = True # Desabilita o botão
        # Volta para a tela de compras após um curto atraso
        Clock.schedule_once(lambda x: self.manager.current == 'shopping', 2)

    def go_back(self, instance):
        """
        Função para voltar à tela de seleção de formas de pagamento (checkout).
        """
        self.manager.current = 'checkout'

class AITotemApp(App):
    """
    A classe principal da aplicação Kivy.
    """
    def build(self):
        """
        Constrói o gerenciador de telas e adiciona todas as telas à aplicação.
        """
        sm = ScreenManager()
        sm.add_widget(ShoppingCart(name='shopping'))
        sm.add_widget(CheckOut(name='checkout'))
        sm.add_widget(PixPaymentScreen(name='pix_payment'))
        sm.add_widget(CardWaitingScreen(name='card_waiting'))
        return sm

if __name__ == '__main__':
    AITotemApp().run()
