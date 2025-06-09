import sqlite3
import json 
from datetime import datetime 

DB_NAME = 'ai_totem.db'

def init_db():
    """
    Inicializa o banco de dados e cria a tabela 'purchases' se ela não existir.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
       
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS purchases (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                products_json TEXT NOT NULL,
                total_value REAL NOT NULL,
                payment_method TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"Banco de dados '{DB_NAME}' inicializado com sucesso.")
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados: {e}")

def save_purchase(cart_items, total_price, payment_method):
    """
    Salva uma nova compra no banco de dados.

    :param cart_items: Dicionário com os itens do carrinho. Ex: {'Apple': 2}
    :param total_price: O preço final da compra.
    :param payment_method: String com o método de pagamento. Ex: 'Credit Card'
    :return: O ID da compra recém-criada ou None em caso de erro.
    """
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
       
        products_as_json = json.dumps(cart_items)
        
       
        current_timestamp = datetime.now()
        
        
        cursor.execute('''
            INSERT INTO purchases (products_json, total_value, payment_method, timestamp)
            VALUES (?, ?, ?, ?)
        ''', (products_as_json, total_price, payment_method, current_timestamp))
        
        purchase_id = cursor.lastrowid 
        
        conn.commit()
        conn.close()
        
        print(f"Compra #{purchase_id} salva com sucesso!")
        return purchase_id
    except Exception as e:
        print(f"Erro ao salvar a compra: {e}")
        return None