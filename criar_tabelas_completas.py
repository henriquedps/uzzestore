import sqlite3
import os

def criar_todas_tabelas():
    # Verificar se o banco existe
    db_path = 'loja.db'
    print(f"📍 Verificando banco em: {os.path.abspath(db_path)}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Criar tabela de usuários (se não existir)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Tabela usuarios verificada/criada")
        
        # 2. Criar tabela de produtos (se não existir)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                descricao TEXT,
                preco REAL NOT NULL,
                categoria TEXT,
                imagem TEXT,
                estoque INTEGER DEFAULT 0,
                data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Tabela produtos verificada/criada")
        
        # 3. Criar tabela de pedidos (se não existir)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER NOT NULL,
                itens TEXT NOT NULL,
                total REAL NOT NULL,
                endereco TEXT,
                status TEXT DEFAULT 'aguardando_pagamento',
                forma_pagamento TEXT,
                transacao_id TEXT,
                data_pedido TEXT DEFAULT CURRENT_TIMESTAMP,
                data_pagamento TEXT,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')
        print("✅ Tabela pedidos verificada/criada")
        
        # 4. Criar tabela de contas de recebimento
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contas_recebimento (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_titular TEXT NOT NULL,
                cpf_cnpj TEXT NOT NULL,
                banco TEXT NOT NULL,
                agencia TEXT NOT NULL,
                conta TEXT NOT NULL,
                tipo_conta TEXT NOT NULL,
                chave_pix TEXT,
                tipo_chave_pix TEXT,
                ativa INTEGER DEFAULT 1,
                data_criacao TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        print("✅ Tabela contas_recebimento criada!")
        
        # 5. Verificar se já existe uma conta padrão
        conta_existente = cursor.execute('SELECT COUNT(*) FROM contas_recebimento').fetchone()[0]
        
        if conta_existente == 0:
            # Inserir conta padrão
            cursor.execute('''
                INSERT INTO contas_recebimento 
                (nome_titular, cpf_cnpj, banco, agencia, conta, tipo_conta, chave_pix, tipo_chave_pix, ativa)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                'UzzerStore LTDA',
                '12.345.678/0001-90',
                'Banco do Brasil',
                '1234-5',
                '98765-4',
                'Conta Corrente',
                '12345678000190',
                'CNPJ',
                1
            ))
            print("✅ Conta padrão criada!")
        else:
            print("ℹ️ Já existem contas configuradas")
        
        # 6. Verificar estrutura das tabelas
        print("\n📋 Verificando estrutura das tabelas:")
        
        tables = ['usuarios', 'produtos', 'pedidos', 'contas_recebimento']
        for table in tables:
            cursor.execute(f"PRAGMA table_info({table})")
            columns = cursor.fetchall()
            print(f"\n🔹 Tabela {table}:")
            for col in columns:
                print(f"   - {col[1]} ({col[2]})")
        
        # Commit das alterações
        conn.commit()
        print(f"\n🎉 Todas as tabelas foram criadas/verificadas com sucesso!")
        
        # Mostrar estatísticas
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        users_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM produtos")
        products_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM pedidos")
        orders_count = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM contas_recebimento")
        accounts_count = cursor.fetchone()[0]
        
        print(f"\n📊 Estatísticas:")
        print(f"   👥 Usuários: {users_count}")
        print(f"   📦 Produtos: {products_count}")
        print(f"   🛒 Pedidos: {orders_count}")
        print(f"   🏦 Contas: {accounts_count}")
        
    except Exception as e:
        print(f"❌ Erro ao criar tabelas: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == '__main__':
    criar_todas_tabelas()