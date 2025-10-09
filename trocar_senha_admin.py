import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('loja.db')
nova_senha = generate_password_hash("admin123")
conn.execute("UPDATE usuarios SET senha = ? WHERE email = ?", (nova_senha, "admin@uzzerstore.com"))
conn.commit()
conn.close()
print("Senha do admin atualizada!")