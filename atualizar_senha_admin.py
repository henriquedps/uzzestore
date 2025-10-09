import sqlite3
from werkzeug.security import generate_password_hash

db_path = 'loja.db'  # Se estiver na Render, pode ser '/tmp/loja.db'
nova_senha = generate_password_hash("admin123")  # Troque para a senha desejada

conn = sqlite3.connect(db_path)
conn.execute("UPDATE usuarios SET senha = ? WHERE email = ?", (nova_senha, "admin@uzzerstore.com"))
conn.commit()
conn.close()

print("Senha do admin atualizada para: admin123")