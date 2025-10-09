# criar_novo_admin.py
import sqlite3
from werkzeug.security import generate_password_hash

db_path = 'loja.db'  # Altere para '/tmp/loja.db' se estiver na Render

novo_nome = "Novo Admin"
novo_email = "henrique99429151@gmail.com"
nova_senha = generate_password_hash("admin123")  # Troque para a senha desejada

conn = sqlite3.connect(db_path)

# Verifica se já existe
existe = conn.execute("SELECT id FROM usuarios WHERE email = ?", (novo_email,)).fetchone()
if not existe:
    conn.execute(
        "INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)",
        (novo_nome, novo_email, nova_senha)
    )
    conn.commit()
    print(f"Usuário admin '{novo_email}' criado com sucesso!")
else:
    print("Este email já está cadastrado!")

conn.close()