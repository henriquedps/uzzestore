import sqlite3

def criar_tabela_contas():
    conn = sqlite3.connect('loja.db')
    
    # Criar tabela de contas para recebimento
    conn.execute('''
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
    
    # Inserir conta padrão da loja
    conta_padrao = conn.execute('SELECT * FROM contas_recebimento WHERE id = 1').fetchone()
    
    if not conta_padrao:
        conn.execute('''
            INSERT INTO contas_recebimento 
            (nome_titular, cpf_cnpj, banco, agencia, conta, tipo_conta, chave_pix, tipo_chave_pix, ativa)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            'UzzerStore LTDA',
            '12.345.678/0001-90',
            'Banco do Brasil',
            '1234-5',
            '12345-6',
            'Conta Corrente',
            '12345678000190',
            'CNPJ',
            1
        ))
        print("✅ Conta padrão criada!")
    
    conn.commit()
    conn.close()
    print("🎉 Tabela de contas criada com sucesso!")

if __name__ == '__main__':
    criar_tabela_contas()