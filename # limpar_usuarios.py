# limpar_usuarios.py
import sqlite3
from werkzeug.security import generate_password_hash

conn = sqlite3.connect('loja.db')

# Apagar todos os usuários
conn.execute("DELETE FROM usuarios")
conn.commit()

# Criar admin padrão

conn.commit()
conn.close()
print("Todos os usuários foram apagados ")