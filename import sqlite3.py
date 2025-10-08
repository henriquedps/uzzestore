import sqlite3

def atualizar_banco():
    conn = sqlite3.connect('loja.db')
    
    # Adicionar colunas na tabela pedidos
    try:
        conn.execute('ALTER TABLE pedidos ADD COLUMN endereco TEXT')
        print("✅ Coluna endereco adicionada")
    except:
        print("⚠️ Coluna endereco já existe")
    
    try:
        conn.execute('ALTER TABLE pedidos ADD COLUMN status TEXT DEFAULT "aguardando_pagamento"')
        print("✅ Coluna status adicionada")
    except:
        print("⚠️ Coluna status já existe")
    
    try:
        conn.execute('ALTER TABLE pedidos ADD COLUMN forma_pagamento TEXT')
        print("✅ Coluna forma_pagamento adicionada")
    except:
        print("⚠️ Coluna forma_pagamento já existe")
    
    try:
        conn.execute('ALTER TABLE pedidos ADD COLUMN transacao_id TEXT')
        print("✅ Coluna transacao_id adicionada")
    except:
        print("⚠️ Coluna transacao_id já existe")
    
    try:
        conn.execute('ALTER TABLE pedidos ADD COLUMN data_pedido TEXT')
        print("✅ Coluna data_pedido adicionada")
    except:
        print("⚠️ Coluna data_pedido já existe")
    
    try:
        conn.execute('ALTER TABLE pedidos ADD COLUMN data_pagamento TEXT')
        print("✅ Coluna data_pagamento adicionada")
    except:
        print("⚠️ Coluna data_pagamento já existe")
    
    conn.commit()
    conn.close()
    print("🎉 Banco atualizado!")

if __name__ == '__main__':
    atualizar_banco()