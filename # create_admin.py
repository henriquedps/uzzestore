# create_admin.py
import sqlite3
from werkzeug.security import generate_password_hash
import secrets
import string

def generate_secure_password():
    """Gera uma senha segura aleatória"""
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    password = ''.join(secrets.choice(alphabet) for _ in range(12))
    return password

def create_admin_user():
    conn = sqlite3.connect('loja.db')
    
    # Verificar se já existe o usuário admin
    existing = conn.execute('SELECT * FROM usuarios WHERE email = ?', ('admin@uzzerstore.com',)).fetchone()
    
    if not existing:
        # Gerar senha segura
        admin_password = generate_secure_password()
        
        conn.execute('''
            INSERT INTO usuarios (nome, email, senha) 
            VALUES (?, ?, ?)
        ''', (
            'Administrador',
            'admin@uzzerstore.com',
            generate_password_hash(admin_password)
        ))
        conn.commit()
        print("✅ Usuário admin criado com sucesso!")
        print("📧 Email: admin@uzzerstore.com")
        print(f"🔑 Senha: {admin_password}")
        print("⚠️  IMPORTANTE: Anote esta senha, ela não será exibida novamente!")
        
        # Salvar em arquivo seguro
        with open('admin_credentials.txt', 'w') as f:
            f.write(f"Admin UzzerStore\n")
            f.write(f"Email: admin@uzzerstore.com\n")
            f.write(f"Senha: {admin_password}\n")
            f.write(f"Criado em: {__import__('datetime').datetime.now()}\n")
        
        print("💾 Credenciais salvas em 'admin_credentials.txt'")
        
    else:
        print("ℹ️ Usuário admin já existe!")
        print("📧 Email: admin@uzzerstore.com")
        print("🔑 Senha: admin123")
    
    conn.close()

if __name__ == '__main__':
    create_admin_user()