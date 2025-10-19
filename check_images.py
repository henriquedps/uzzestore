import sqlite3

conn = sqlite3.connect('data/app.db')
produtos = conn.execute('SELECT id, nome, imagem FROM produtos ORDER BY id DESC LIMIT 10').fetchall()

print("=== PRODUTOS NO BANCO ===")
for p in produtos:
    print(f'ID: {p[0]}')
    print(f'Nome: {p[1]}')
    print(f'URL: {p[2] if p[2] else "VAZIO"}')
    print('---')

conn.close()