# init_production.py
import sqlite3
from werkzeug.security import generate_password_hash
import os

def setup_production():
    """Configurar ambiente de produção"""
    
    # Criar banco se não existir
    if not os.path.exists('loja.db'):
        print("🔧 Criando banco de dados...")
        
        conn = sqlite3.connect('loja.db')
        
        # Criar tabelas
        conn.execute('''
            CREATE TABLE usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                imagem TEXT,
                categoria TEXT,
                descricao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.execute('''
            CREATE TABLE pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                itens TEXT NOT NULL,
                total REAL NOT NULL,
                endereco TEXT,
                status TEXT DEFAULT 'pendente',
                data_pedido TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        
        # Criar usuário admin
        admin_password = "Admin@2024!"
        conn.execute('''
            INSERT INTO usuarios (nome, email, senha) 
            VALUES (?, ?, ?)
        ''', (
            'Administrador',
            'admin@uzzerstore.com',
            generate_password_hash(admin_password)
        ))
        
        # Adicionar produtos de exemplo
        produtos_exemplo = [
            ('Camiseta Básica Branca', 49.90, 'https://via.placeholder.com/300x400/FFFFFF/000000?text=Camiseta+Branca', 'Camisetas', 'Camiseta básica em algodão, confortável e versátil.'),
            ('Calça Jeans Skinny', 129.90, 'https://via.placeholder.com/300x400/4169E1/FFFFFF?text=Calça+Jeans', 'Calças', 'Calça jeans skinny com lavagem escura, perfeita para o dia a dia.'),
            ('Vestido Floral', 89.90, 'https://via.placeholder.com/300x400/FF69B4/FFFFFF?text=Vestido+Floral', 'Vestidos', 'Vestido floral feminino, ideal para ocasiões especiais.'),
            ('Tênis Casual', 159.90, 'https://via.placeholder.com/300x400/32CD32/FFFFFF?text=Tênis+Casual', 'Calçados', 'Tênis casual confortável para uso diário.'),
            ('Bolsa de Couro', 199.90, 'https://via.placeholder.com/300x400/8B4513/FFFFFF?text=Bolsa+Couro', 'Acessórios', 'Bolsa de couro genuíno, elegante e durável.')
        ]
        
        for produto in produtos_exemplo:
            conn.execute('''
                INSERT INTO produtos (nome, preco, imagem, categoria, descricao)
                VALUES (?, ?, ?, ?, ?)
            ''', produto)
        
        conn.commit()
        conn.close()
        
        print("✅ Banco de dados criado com sucesso!")
        print("👤 Admin criado: admin@uzzerstore.com")
        print(f"🔑 Senha: {admin_password}")
        print("📦 5 produtos de exemplo adicionados")
    else:
        print("ℹ️ Banco de dados já existe!")
    
    print("\n🚀 Sistema pronto para produção!")
    print("🌐 Para executar: python app.py")

if __name__ == '__main__':
    setup_production()