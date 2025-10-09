# limpar_usuarios.py
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('loja.db')

# Apagar todos os usuários
conn.execute("DELETE FROM usuarios")
conn.commit()

# Criar admin padrão
admin_email = "admin@uzzerstore.com"
admin_senha = generate_password_hash("admin123")
conn.execute(
    "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
    ("Administrador", admin_email, admin_senha)
)
conn.commit()
conn.close()

print("Todos os usuários foram removidos e o admin foi recriado com a senha: admin123")