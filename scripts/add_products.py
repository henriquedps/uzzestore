import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'app.db')
print('Usando DB:', DB_PATH)

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# Mostrar colunas da tabela produtos
cols = [r['name'] for r in cur.execute("PRAGMA table_info(produtos)").fetchall()]
print('Colunas em produtos:', cols)

products = [
    {
        'nome': 'Bermuda Dry fit GG',
        'descricao': 'Bermuda Dry fit tamanho GG, confortável e leve.',
        'preco': 45.00,
        'categoria': 'Bermudas',
        'imagem': 'produtos/bermuda vermelha.png',
        'tamanhos': '["GG"]',
        'estoque': 10
    },
    {
        'nome': 'Bermuda Dry fit G',
        'descricao': 'Bermuda Dry fit tamanho G, confortável e leve.',
        'preco': 45.00,
        'categoria': 'Bermudas',
        'imagem': 'produtos/bermuda1.png',
        'tamanhos': '["G"]',
        'estoque': 12
    },
    {
        'nome': 'Bermuda Dry fit P',
        'descricao': 'Bermuda Dry fit tamanho P, confortável e leve.',
        'preco': 45.00,
        'categoria': 'Bermudas',
        'imagem': 'produtos/bermuda.png',
        'tamanhos': '["P"]',
        'estoque': 8
    }
]

inserted = []
for p in products:
    # checar se já existe
    existing = cur.execute('SELECT id FROM produtos WHERE nome = ?', (p['nome'],)).fetchone()
    if existing:
        print(f"Produto já existe: {p['nome']} (id={existing['id']}) - pulando")
        continue
    # construir insert considerando colunas existentes
    fields = []
    placeholders = []
    values = []
    for key in ['nome','descricao','preco','categoria','imagem','tamanhos','estoque','imagens_adicionais']:
        if key in cols:
            fields.append(key)
            placeholders.append('?')
            values.append(p.get(key))
    sql = f"INSERT INTO produtos ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
    cur.execute(sql, values)
    inserted_id = cur.lastrowid
    conn.commit()
    print(f"Inserido: {p['nome']} id={inserted_id}")
    inserted.append(inserted_id)

print('Inseridos:', inserted)
conn.close()
