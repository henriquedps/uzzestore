from flask import Flask, render_template, request, redirect, url_for, session, flash
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
import json
from datetime import datetime
import uuid
import click
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(BASE_DIR, 'data', 'app.db')
DB_PATH = os.getenv('DB_PATH', DEFAULT_DB)

# NOVO: tornar absoluto se for relativo
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(BASE_DIR, DB_PATH)

DB_DIR = os.path.dirname(DB_PATH)
# NOVO: só cria se houver diretório definido
if DB_DIR:
    os.makedirs(DB_DIR, exist_ok=True)

def _conn_rw():
    # usa sua função existente
    return get_db_connection()

def ensure_is_admin_column(conn):
    cols = [r['name'] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
    if 'is_admin' not in cols:
        conn.execute("ALTER TABLE usuarios ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0")
        conn.commit()

def ensure_password_column(conn):
    cols = [r['name'] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
    # Preferimos senha_hash; se não existir, cria
    if 'senha_hash' in cols:
        return 'senha_hash'
    if 'senha' in cols:
        return 'senha'
    conn.execute("ALTER TABLE usuarios ADD COLUMN senha_hash TEXT")
    conn.commit()
    return 'senha_hash'

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'uzzer-store-secret-key-2024')

# Configurações para produção
if os.environ.get('VERCEL'):
    app.config['DATABASE_PATH'] = '/tmp/loja.db'
else:
    app.config['DATABASE_PATH'] = 'loja.db'

# Filtros de template
@app.template_filter('currency')
def currency_filter(value):
    try:
        v = float(value)
        s = f"{v:,.2f}"
        s = s.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f"R$ {s}"
    except:
        return value

@app.template_filter('from_json')
def from_json_filter(value):
    try:
        import json
        if isinstance(value, str):
            return json.loads(value)
        return value or []
    except (json.JSONDecodeError, TypeError):
        return []

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializar banco de dados"""
    try:
        conn = get_db_connection()

        # Tabelas
        conn.execute('''
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                senha TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.execute('''
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                preco REAL NOT NULL,
                imagem TEXT,
                categoria TEXT,
                descricao TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Garante coluna is_admin (se faltar, cria)
        ensure_is_admin_column(conn)

        # Admin padrão (com is_admin=1)
        admin_exists = conn.execute('SELECT COUNT(*) FROM usuarios WHERE email = ?', ('admin@uzzerstore.com',)).fetchone()[0]
        if admin_exists == 0:
            conn.execute('''
                INSERT INTO usuarios (nome, email, senha, is_admin) 
                VALUES (?, ?, ?, 1)
            ''', (
                'Administrador',
                'admin@uzzerstore.com',
                generate_password_hash('Admin@2024!')
            ))

        conn.commit()
        conn.close()
        print("✅ Banco de dados inicializado com sucesso!")
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")

def is_admin():
    if 'user_id' not in session:
        return False
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()

        # verifica se a coluna existe
        cols = [r['name'] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
        conn.close()

        db_admin = False
        if user:
            if 'is_admin' in cols:
                try:
                    db_admin = bool(user['is_admin'])
                except Exception:
                    db_admin = False

            # Fallbacks antigos
            is_first_user = user['id'] == 1
            is_admin_email = user['email'] in ['admin@uzzerstore.com', 'administrador@uzzerstore.com']
            is_session_admin = session.get('is_admin', False)

            return db_admin or is_first_user or is_admin_email or is_session_admin
    except Exception as e:
        print(f"Erro ao verificar admin: {e}")
    return False

# ROTAS DO CARRINHO
@app.route('/carrinho')
def carrinho():
    if 'user_id' not in session:
        flash('Você precisa estar logado para ver o carrinho!', 'error')
        return redirect(url_for('login'))
    
    carrinho_itens = session.get('carrinho', [])
    print(f"Debug - Itens no carrinho: {carrinho_itens}")  # Debug
    
    if not carrinho_itens:
        return render_template('carrinho.html', itens=[], total=0)
    
    try:
        conn = get_db_connection()
        itens_detalhados = []
        total = 0
        
        for item in carrinho_itens:
            produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (item['produto_id'],)).fetchone()
            if produto:
                item_total = float(produto['preco']) * item['quantidade']
                itens_detalhados.append({
                    'produto': produto,
                    'quantidade': item['quantidade'],
                    'subtotal': item_total
                })
                total += item_total
        
        conn.close()
        
        print(f"Debug - Itens detalhados: {len(itens_detalhados)}")  # Debug
        return render_template('carrinho.html', itens=itens_detalhados, total=total)
    except Exception as e:
        print(f"Erro no carrinho: {e}")
        return render_template('carrinho.html', itens=[], total=0)

@app.route('/carrinho/adicionar/<int:produto_id>')
def carrinho_adicionar(produto_id):
    if 'user_id' not in session:
        flash('Você precisa estar logado para adicionar ao carrinho!', 'error')
        return redirect(url_for('login'))

    # NOVO: quantidade via querystring ?q= (padrão 1, máx. 99)
    try:
        q = int(request.args.get('q', 1))
    except ValueError:
        q = 1
    quantidade = max(1, min(q, 99))
    
    try:
        conn = get_db_connection()
        produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
        conn.close()

        if not produto:
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('index'))

        if 'carrinho' not in session:
            session['carrinho'] = []

        carrinho = session['carrinho']
        for item in carrinho:
            if item['produto_id'] == produto_id:
                item['quantidade'] += quantidade
                break
        else:
            carrinho.append({'produto_id': produto_id, 'quantidade': quantidade})

        session['carrinho'] = carrinho
        session.permanent = True
        session.modified = True

        flash(f'✅ "{produto["nome"]}" x{quantidade} adicionado ao carrinho!', 'success')
        return redirect(request.referrer or url_for('index'))

    except Exception as e:
        print(f"Erro ao adicionar ao carrinho: {e}")
        flash('Erro ao adicionar produto ao carrinho!', 'error')
        return redirect(url_for('index'))

@app.route('/carrinho/remover/<int:produto_id>')
def carrinho_remover(produto_id):
    if 'carrinho' in session:
        carrinho = session['carrinho']
        session['carrinho'] = [item for item in carrinho if item['produto_id'] != produto_id]
        session.permanent = True
        flash('Item removido do carrinho!', 'info')
    
    return redirect(url_for('carrinho'))

@app.route('/carrinho/limpar')
def carrinho_limpar():
    if 'carrinho' in session:
        session['carrinho'] = []
        session.permanent = True
        flash('Carrinho limpo!', 'info')
    
    return redirect(url_for('carrinho'))

# ROTA PRINCIPAL
@app.route('/')
def index():
    try:
        init_db()  # Garantir que o DB existe
        
        categoria_selecionada = request.args.get('categoria')
        
        conn = get_db_connection()
        
        if categoria_selecionada:
            produtos = conn.execute(
                'SELECT * FROM produtos WHERE categoria = ? ORDER BY id DESC',
                (categoria_selecionada,)
            ).fetchall()
        else:
            produtos = conn.execute('SELECT * FROM produtos ORDER BY id DESC').fetchall()
        
        categorias = conn.execute('SELECT DISTINCT categoria FROM produtos WHERE categoria IS NOT NULL ORDER BY categoria').fetchall()
        
        conn.close()
        
        return render_template('index.html', 
                             produtos=produtos, 
                             categorias=categorias,
                             categoria_selecionada=categoria_selecionada)
    except Exception as e:
        print(f"Erro na rota index: {e}")
        return f"""
        <h1>🏪 UzzerStore</h1>
        <p>Loja em inicialização...</p>
        <p>Erro: {e}</p>
        <style>
            body {{ font-family: Arial; padding: 20px; text-align: center; }}
            h1 {{ color: #00d4aa; }}
        </style>
        """

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        nome = request.form['nome']
        email = request.form['email']
        senha = request.form['senha']
        
        try:
            conn = get_db_connection()
            
            user_exists = conn.execute('SELECT id FROM usuarios WHERE email = ?', (email,)).fetchone()
            
            if user_exists:
                flash('Este email já está cadastrado!', 'error')
                conn.close()
                return render_template('cadastro.html')
            
            hashed_password = generate_password_hash(senha)
            
            cursor = conn.execute(
                'INSERT INTO usuarios (nome, email, senha) VALUES (?, ?, ?)',
                (nome, email, hashed_password)
            )
            user_id = cursor.lastrowid
            conn.commit()
            
            session['user_id'] = user_id
            session['user_nome'] = nome
            
            if user_id == 1:
                session['is_admin'] = True
                flash(f'Conta criada com sucesso! Bem-vindo(a) Admin, {nome}! 🔧', 'success')
            else:
                flash(f'Conta criada com sucesso! Bem-vindo(a), {nome}!', 'success')
            
            conn.close()
            return redirect(url_for('index'))
            
        except Exception as e:
            flash(f'Erro ao criar conta: {e}', 'error')
    
    return render_template('cadastro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        senha = request.form['senha']
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()

            # checa colunas
            cols = [r['name'] for r in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
            conn.close()

            if user and check_password_hash(user['senha'], senha):
                session['user_id'] = user['id']
                session['user_nome'] = user['nome']

                db_admin = False
                if 'is_admin' in cols:
                    try:
                        db_admin = bool(user['is_admin'])
                    except Exception:
                        db_admin = False

                # Fallbacks
                is_first_user = user['id'] == 1
                is_admin_email = user['email'] in ['admin@uzzerstore.com', 'administrador@uzzerstore.com']

                session['is_admin'] = bool(db_admin or is_first_user or is_admin_email)

                if session['is_admin']:
                    flash(f'Bem-vindo(a) Admin, {user["nome"]}! 🔧', 'success')
                else:
                    flash(f'Bem-vindo(a), {user["nome"]}!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Email ou senha incorretos!', 'error')
        except Exception as e:
            flash(f'Erro no login: {e}', 'error')
    return render_template('login.html')

@app.route('/logout')
def logout():
    nome = session.get('user_nome', 'Usuário')
    session.clear()
    flash(f'Até logo, {nome}!', 'info')
    return redirect(url_for('index'))

# ROTAS DE ADMIN
@app.route('/admin')
def admin_dashboard():
    if not is_admin():
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        
        stats = {
            'total_usuarios': conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0],
            'total_produtos': conn.execute('SELECT COUNT(*) FROM produtos').fetchone()[0],
            'carrinho_ativos': 0,  # Removido contador de pedidos
            'vendas_total': 0,     # Removido vendas
        }
        
        conn.close()
        
        return render_template('admin_dashboard.html', stats=stats)
    except Exception as e:
        return f"Erro no admin: {e}"

@app.route('/admin/produtos')
def admin_produtos():
    if not is_admin():
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        produtos = conn.execute('SELECT * FROM produtos ORDER BY id DESC').fetchall()
        conn.close()
        
        return render_template('admin_produtos.html', produtos=produtos)
    except Exception as e:
        return f"Erro: {e}"

@app.route('/admin/produtos/novo', methods=['GET', 'POST'])
def admin_novo_produto():
    if not is_admin():
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        categoria = request.form['categoria']
        descricao = request.form['descricao']
        imagem = request.form['imagem']
        
        try:
            conn = get_db_connection()
            conn.execute('''
                INSERT INTO produtos (nome, preco, categoria, descricao, imagem)
                VALUES (?, ?, ?, ?, ?)
            ''', (nome, preco, categoria, descricao, imagem))
            conn.commit()
            conn.close()
            
            flash(f'Produto "{nome}" adicionado com sucesso!', 'success')
            return redirect(url_for('admin_produtos'))
        except Exception as e:
            flash(f'Erro ao adicionar produto: {e}', 'error')
    
    return render_template('admin_novo_produto.html')

@app.route('/admin/produtos/editar/<int:produto_id>', methods=['GET', 'POST'])
def admin_editar_produto(produto_id):
    if not is_admin():
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
    
    if not produto:
        flash('Produto não encontrado!', 'error')
        return redirect(url_for('admin_produtos'))
    
    if request.method == 'POST':
        nome = request.form['nome']
        preco = float(request.form['preco'])
        categoria = request.form['categoria']
        descricao = request.form['descricao']
        imagem = request.form['imagem']
        
        try:
            conn.execute('''
                UPDATE produtos 
                SET nome = ?, preco = ?, categoria = ?, descricao = ?, imagem = ?
                WHERE id = ?
            ''', (nome, preco, categoria, descricao, imagem, produto_id))
            conn.commit()
            conn.close()
            
            flash(f'Produto "{nome}" atualizado com sucesso!', 'success')
            return redirect(url_for('admin_produtos'))
        except Exception as e:
            flash(f'Erro ao atualizar produto: {e}', 'error')
    
    conn.close()
    return render_template('admin_editar_produto.html', produto=produto)

@app.route('/admin/produtos/deletar/<int:produto_id>')
def admin_deletar_produto(produto_id):
    if not is_admin():
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        produto = conn.execute('SELECT nome FROM produtos WHERE id = ?', (produto_id,)).fetchone()
        
        if produto:
            conn.execute('DELETE FROM produtos WHERE id = ?', (produto_id,))
            conn.commit()
            flash(f'Produto "{produto["nome"]}" removido com sucesso!', 'success')
        else:
            flash('Produto não encontrado!', 'error')
        
        conn.close()
    except Exception as e:
        flash(f'Erro ao remover produto: {e}', 'error')
    
    return redirect(url_for('admin_produtos'))

@app.route('/debug/produtos')
def debug_produtos():
    if not is_admin():
        return "Acesso negado"
    
    try:
        conn = get_db_connection()
        produtos = conn.execute('SELECT * FROM produtos ORDER BY id DESC').fetchall()
        conn.close()
        
        html = "<h1>Debug - Produtos</h1><br>"
        for produto in produtos:
            html += f"""
            <div style="border: 1px solid #ccc; padding: 10px; margin: 10px 0;">
                <h3>ID: {produto['id']} - {produto['nome']}</h3>
                <p><strong>Preço:</strong> R$ {produto['preco']}</p>
                <p><strong>Categoria:</strong> {produto['categoria']}</p>
                <p><strong>URL da Imagem:</strong> {produto['imagem'] or 'Não informado'}</p>
                {f'<img src="{produto["imagem"]}" style="max-width: 200px; height: auto;" onerror="this.src=\'data:image/svg+xml,<svg xmlns=&quot;http://www.w3.org/2000/svg&quot; width=&quot;200&quot; height=&quot;200&quot;><rect width=&quot;200&quot; height=&quot;200&quot; fill=&quot;%23f0f0f0&quot;/><text x=&quot;50%25&quot; y=&quot;50%25&quot; text-anchor=&quot;middle&quot; dy=&quot;.3em&quot; fill=&quot;%23666&quot;>Erro</text></svg>\'">' if produto['imagem'] else '<p style="color: #999;">Sem imagem</p>'}
                <hr>
            </div>
            """
        
        return html
    except Exception as e:
        return f"Erro: {e}"

@app.cli.command("db-info")
def db_info():
    """Mostra o arquivo de banco em uso e as colunas de usuarios."""
    conn = get_db_connection()
    try:
        dblist = [dict(r) for r in conn.execute("PRAGMA database_list").fetchall()]
        print("SQLite em uso:", dblist)
        cols = [dict(c) for c in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
        print("Tabela usuarios:", cols or 'não encontrada')
    finally:
        conn.close()

@app.cli.command("create-admin")
@click.option('--nome', prompt=True)
@click.option('--email', prompt=True)
@click.option('--senha', prompt=True, hide_input=True, confirmation_prompt=True)
def create_admin(nome, email, senha):
    """Cria (ou promove) um usuário para administrador."""
    conn = _conn_rw()
    try:
        ensure_is_admin_column(conn)
        pass_col = ensure_password_column(conn)
        senha_val = generate_password_hash(senha) if pass_col == 'senha_hash' else senha

        u = conn.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
        if u:
            conn.execute(f"UPDATE usuarios SET nome = ?, {pass_col} = ?, is_admin = 1 WHERE id = ?",
                         (nome, senha_val, u['id']))
            msg = f'Usuário atualizado e promovido a admin: {email}'
        else:
            conn.execute(f"INSERT INTO usuarios (nome, email, {pass_col}, is_admin) VALUES (?, ?, ?, 1)",
                         (nome, email, senha_val))
            msg = f'Admin criado: {email}'
        conn.commit()
        print("OK:", msg)
    except Exception as e:
        conn.rollback()
        print("Erro:", e)
    finally:
        conn.close()

@app.cli.command("init-db")
@click.option('--schema', default=os.path.join(BASE_DIR, 'sql', 'schema.sql'))
def init_db_cli(schema):  # RENOMEADO para não sobrescrever init_db()
    """Cria as tabelas no DB atual a partir de um schema.sql."""
    if not os.path.exists(schema):
        print("Schema não encontrado:", schema)
        return
    conn = get_db_connection()
    try:
        with open(schema, 'r', encoding='utf-8') as f:
            conn.executescript(f.read())
        conn.commit()
        print("OK: schema aplicado em", DB_PATH)
    finally:
        conn.close()

@app.cli.command("upgrade-db")
def upgrade_db():
    """Garante estrutura mínima (tabelas + coluna is_admin)."""
    # garante tabelas
    init_db()
    conn = get_db_connection()
    try:
        # garante coluna is_admin
        ensure_is_admin_column(conn)
        # garante coluna de senha compatível (senha ou senha_hash)
        ensure_password_column(conn)
        conn.commit()
        print("OK: Migração mínima aplicada em", DB_PATH)
        # Mostra colunas para conferência
        cols = [dict(c) for c in conn.execute("PRAGMA table_info(usuarios)").fetchall()]
        print("usuarios =>", cols)
    except Exception as e:
        conn.rollback()
        print("Erro no upgrade-db:", e)
    finally:
        conn.close()

# Para o Vercel, não usar if __name__ == '__main__'
# O app será executado automaticamente
print("🚀 UzzerStore inicializado para produção!")

# Inicializar DB na primeira execução
init_db()