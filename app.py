import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from decimal import Decimal
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import json
from datetime import datetime
import uuid
import click
import urllib.parse
from dotenv import load_dotenv

try:
    load_dotenv()
except Exception:
    pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB = os.path.join(BASE_DIR, 'data', 'app.db')
DB_PATH = os.getenv('DB_PATH', DEFAULT_DB)
if not os.path.isabs(DB_PATH):
    DB_PATH = os.path.join(BASE_DIR, DB_PATH)
db_dir = os.path.dirname(DB_PATH)
if db_dir:
    os.makedirs(db_dir, exist_ok=True)

# Configurações do WhatsApp da loja
WHATSAPP_LOJA = "551166997164602"  # Número padrão - altere aqui ou use variável de ambiente
WHATSAPP_NUMERO = os.getenv('WHATSAPP_NUMERO', WHATSAPP_LOJA)

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

def ensure_tamanhos_column(conn):
    """Garante que a coluna tamanhos existe na tabela produtos"""
    cols = [r['name'] for r in conn.execute("PRAGMA table_info(produtos)").fetchall()]
    if 'tamanhos' not in cols:
        conn.execute("ALTER TABLE produtos ADD COLUMN tamanhos TEXT")
        conn.commit()
        print("✅ Coluna 'tamanhos' adicionada à tabela produtos")

def ensure_estoque_column(conn):
    """Garante que a coluna estoque existe na tabela produtos"""
    cols = [r['name'] for r in conn.execute("PRAGMA table_info(produtos)").fetchall()]
    if 'estoque' not in cols:
        conn.execute("ALTER TABLE produtos ADD COLUMN estoque INTEGER DEFAULT 0")
        conn.commit()
        print("✅ Coluna 'estoque' adicionada à tabela produtos")

def ensure_imagens_adicionais_column(conn):
    """Garante que a coluna imagens_adicionais existe na tabela produtos"""
    cols = [r['name'] for r in conn.execute("PRAGMA table_info(produtos)").fetchall()]
    if 'imagens_adicionais' not in cols:
        conn.execute("ALTER TABLE produtos ADD COLUMN imagens_adicionais TEXT")
        conn.commit()
        print("✅ Coluna 'imagens_adicionais' adicionada à tabela produtos")

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'uzzer-store-secret-key-2024')

# Filtro personalizado para converter JSON no template
@app.template_filter('fromjson')
def fromjson_filter(value):
    try:
        return json.loads(value) if value else []
    except:
        return []

# Disponibilizar configurações globalmente para todos os templates
@app.context_processor
def inject_config():
    """Injeta as configurações em todos os templates"""
    try:
        config = carregar_configuracoes()
        return dict(global_config=config)
    except:
        return dict(global_config={})

# 🧹 Middleware para FORÇAR limpeza de cache
@app.after_request
def add_no_cache_headers(response):
    """Força o navegador a não fazer cache das páginas"""
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    response.headers['Last-Modified'] = datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT')
    response.headers['ETag'] = str(uuid.uuid4())
    return response

# Configurações para produção
if os.environ.get('VERCEL'):
    app.config['DATABASE_PATH'] = '/tmp/loja.db'
else:
    app.config['DATABASE_PATH'] = 'loja.db'

# Configuração do WhatsApp
app.config['WHATSAPP_NUMBER'] = os.environ.get('WHATSAPP_NUMBER', '551166997164602')
app.config['WHATSAPP_STORE_NAME'] = os.environ.get('WHATSAPP_STORE_NAME', 'CAMILA DE PAULA.')

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

def gerar_mensagem_whatsapp(pedido, itens):
    """Gera mensagem formatada para WhatsApp com dados do pedido"""
    try:
        # Cabeçalho da mensagem
        mensagem = f"🛒 *NOVO PEDIDO - UZZER STORE*\n\n"
        mensagem += f"📋 *Pedido:* #{pedido['id']}\n"
        mensagem += f"📅 *Data:* {pedido['created_at']}\n\n"
        
        # Dados do cliente
        mensagem += f"👤 *DADOS DO CLIENTE*\n"
        mensagem += f"Nome: {pedido['nome_cliente']}\n"
        mensagem += f"Email: {pedido['email_cliente']}\n"
        if pedido['telefone']:
            mensagem += f"Telefone: {pedido['telefone']}\n"
        mensagem += "\n"
        
        # Endereço de entrega
        mensagem += f"📍 *ENDEREÇO DE ENTREGA*\n"
        mensagem += f"{pedido['endereco']}, {pedido['numero']}\n"
        if pedido['complemento']:
            mensagem += f"Complemento: {pedido['complemento']}\n"
        mensagem += f"{pedido['bairro']}, {pedido['cidade']} - {pedido['estado']}\n"
        mensagem += f"CEP: {pedido['cep']}\n\n"
        
        # Itens do pedido
        mensagem += f"🛍️ *ITENS DO PEDIDO*\n"
        for item in itens:
            mensagem += f"• {item['nome']}\n"
            mensagem += f"  Qtd: {item['quantidade']} | "
            if item.get('tamanho'):
                mensagem += f"Tamanho: {item['tamanho']} | "
            if item.get('cor'):
                mensagem += f"Cor: {item['cor']}\n"
            mensagem += f"  Valor: {currency_filter(item['preco'])} cada\n"
            mensagem += f"  Subtotal: {currency_filter(item['subtotal'])}\n\n"
        
        # Pagamento e total
        mensagem += f"💳 *PAGAMENTO*\n"
        mensagem += f"Método: {pedido['metodo_pagamento']}\n"
        mensagem += f"*Total: {currency_filter(pedido['total'])}*\n\n"
        
        mensagem += f"✅ Pedido confirmado e aguardando processamento!"
        
        return mensagem
    except Exception as e:
        print(f"Erro ao gerar mensagem WhatsApp: {e}")
        return f"Novo pedido #{pedido.get('id', '?')} - {pedido.get('nome_cliente', 'Cliente')} - Total: {currency_filter(pedido.get('total', 0))}"

def gerar_url_whatsapp(numero_whatsapp, mensagem):
    """Gera URL do WhatsApp com mensagem pré-formatada"""
    try:
        # Remove caracteres especiais do número
        numero = ''.join(filter(str.isdigit, numero_whatsapp))
        
        # Adiciona código do país se não tiver
        if not numero.startswith('55'):
            numero = '55' + numero
        
        # Codifica a mensagem para URL
        mensagem_codificada = urllib.parse.quote(mensagem)
        
        # Gera URL do WhatsApp
        url = f"https://wa.me/{numero}?text={mensagem_codificada}"
        
        return url
    except Exception as e:
        print(f"Erro ao gerar URL WhatsApp: {e}")
        return None

@app.template_filter('from_json')
def from_json_filter(value):
    try:
        import json
        if isinstance(value, str):
            return json.loads(value)
        return value or []
    except (json.JSONDecodeError, TypeError):
        return []

@app.context_processor
def inject_admin_status():
    """Injeta o status de admin em todos os templates"""
    return {
        'is_admin': is_admin
    }

def safe_parse_json(value, default=None):
    """Função helper para parsing seguro de JSON"""
    try:
        if isinstance(value, str) and value.strip():
            return json.loads(value)
        return default or []
    except (json.JSONDecodeError, TypeError, AttributeError):
        return default or []

def get_imagens_adicionais(produto):
    """Extrai imagens adicionais de um produto de forma segura"""
    if not produto:
        return []
    
    # Converter sqlite3.Row para dict para acesso seguro
    produto_dict = dict(produto) if hasattr(produto, 'keys') else produto
    imagens_adicionais = produto_dict.get('imagens_adicionais', '') if isinstance(produto_dict, dict) else getattr(produto, 'imagens_adicionais', '')
    
    if not imagens_adicionais:
        return []
    
    return safe_parse_json(imagens_adicionais)

def validate_form_field(form, field_name, max_length=255, required=True):
    """Valida campo de formulário de forma segura"""
    try:
        value = form.get(field_name, '').strip()
        if required and not value:
            raise ValueError(f'Campo {field_name} é obrigatório')
        if len(value) > max_length:
            raise ValueError(f'Campo {field_name} muito longo (máximo {max_length} caracteres)')
        return value
    except Exception:
        if required:
            raise ValueError(f'Campo {field_name} inválido')
        return ''

def validate_numeric_field(form, field_name, min_val=0, max_val=None, required=True):
    """Valida campo numérico de forma segura"""
    try:
        value_str = form.get(field_name, '').strip()
        if not value_str and not required:
            return 0
        value = float(value_str)
        if value < min_val:
            raise ValueError(f'Campo {field_name} deve ser maior que {min_val}')
        if max_val is not None and value > max_val:
            raise ValueError(f'Campo {field_name} deve ser menor que {max_val}')
        return value
    except (ValueError, TypeError):
        if required:
            raise ValueError(f'Campo {field_name} deve ser um número válido')
        return 0

def init_db():
    """Inicializar banco de dados"""
    try:
        conn = get_db_connection()
        
        # Verificar se já foi inicializado (tabela produtos existe e tem dados)
        try:
            result = conn.execute('SELECT COUNT(*) FROM produtos').fetchone()
            if result and result[0] > 0:
                conn.close()
                return  # Já inicializado
        except:
            pass  # Tabela não existe, continuar inicialização

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

        # Tabela de pedidos
        conn.execute('''
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                nome_cliente TEXT NOT NULL,
                email_cliente TEXT NOT NULL,
                telefone TEXT,
                cep TEXT NOT NULL,
                endereco TEXT NOT NULL,
                numero TEXT NOT NULL,
                complemento TEXT,
                bairro TEXT NOT NULL,
                cidade TEXT NOT NULL,
                estado TEXT NOT NULL,
                metodo_pagamento TEXT NOT NULL,
                total REAL NOT NULL,
                status TEXT DEFAULT 'Pendente',
                itens TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (usuario_id) REFERENCES usuarios (id)
            )
        ''')

        # Garante coluna is_admin (se faltar, cria)
        ensure_is_admin_column(conn)
        
        # Garante coluna tamanhos (se faltar, cria)
        ensure_tamanhos_column(conn)
        
        # Garante coluna estoque (se faltar, cria)
        ensure_estoque_column(conn)

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
        # Se o banco estiver vazio de produtos, tentar popular com imagens em static/produtos
        try:
            # Abrir conexão separada para seed (evita lock com a anterior)
            conn2 = get_db_connection()
            cur = conn2.execute("SELECT COUNT(*) as c FROM produtos")
            total = cur.fetchone()['c']
            if total == 0:
                try:
                    seed_count = seed_products_from_static(conn2)
                    if seed_count:
                        print(f"✅ Seed automático: inseridos {seed_count} produtos a partir de static/produtos")
                except Exception as se:
                    print(f"Aviso: falha ao popular produtos automaticamente: {se}")
            conn2.close()
        except Exception:
            pass
    except Exception as e:
        print(f"❌ Erro ao inicializar banco: {e}")


def seed_products_from_static(conn=None):
    """Popula a tabela produtos a partir dos arquivos em static/produtos se não houver entradas.
    Retorna o número de produtos inseridos.
    Se uma conexão for passada, usa-a; caso contrário abre uma conexão temporária.
    """
    import os
    from datetime import datetime

    close_conn = False
    if conn is None:
        conn = get_db_connection()
        close_conn = True

    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    produtos_dir = os.path.join(BASE_DIR, 'static', 'produtos')
    if not os.path.isdir(produtos_dir):
        if close_conn:
            conn.close()
        return 0

    files = [f for f in os.listdir(produtos_dir) if os.path.isfile(os.path.join(produtos_dir, f))]
    if not files:
        if close_conn:
            conn.close()
        return 0

    # Ler imagens já referenciadas
    cur = conn.execute("SELECT imagem FROM produtos WHERE imagem IS NOT NULL")
    existing = set([r['imagem'] for r in cur.fetchall() if r['imagem']])

    def infer_category(filename):
        s = filename.lower()
        if 'bermuda' in s:
            return 'Bermudas'
        if 'calça' in s or 'calca' in s:
            return 'Calças'
        if 'camisa' in s or 'polo' in s:
            return 'Camisetas'
        if 'camiseta' in s:
            return 'Camisetas'
        if 'bolsa' in s:
            return 'Acessórios'
        if 'boné' in s or 'bone' in s:
            return 'Acessórios'
        if 'cueca' in s:
            return 'Moda Intima'
        return 'Sem categoria'

    inserted = 0
    for fn in files:
        imagem_field = f'produtos/{fn}'
        if imagem_field in existing:
            continue
        nome = os.path.splitext(fn)[0].replace('_', ' ').replace('-', ' ').title()
        preco = 49.90
        categoria = infer_category(fn)
        descricao = ''
        tamanhos = 'P,M,G'
        estoque = 10

        try:
            conn.execute('''
                INSERT INTO produtos (nome, preco, imagem, categoria, descricao, tamanhos, estoque, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome, preco, imagem_field, categoria, descricao, tamanhos, estoque, datetime.utcnow().isoformat()))
            inserted += 1
        except Exception:
            # ignora erros de inserção individuais
            continue

    if inserted > 0:
        conn.commit()

    if close_conn:
        conn.close()

    return inserted

def is_admin():
    """Verifica se usuário atual é administrador (otimizado)"""
    if 'user_id' not in session:
        return False
    
    # Cache na sessão para evitar consultas repetidas
    if 'is_admin_cached' in session:
        return session['is_admin_cached']
    
    try:
        conn = get_db_connection()
        user = conn.execute('SELECT id, email, is_admin FROM usuarios WHERE id = ?', 
                           (session['user_id'],)).fetchone()
        conn.close()

        if not user:
            session['is_admin_cached'] = False
            return False

        # Converter sqlite3.Row para dict para acesso seguro
        user_dict = dict(user)
        
        # Verificação unificada de admin
        is_admin_user = (
            bool(user_dict.get('is_admin', False)) or  # Coluna is_admin
            user_dict['id'] == 1 or  # Primeiro usuário
            user_dict['email'] in ['admin@uzzerstore.com', 'administrador@uzzerstore.com']  # Emails admin
        )
        
        # Cache o resultado na sessão
        session['is_admin_cached'] = is_admin_user
        session.permanent = True
        
        return is_admin_user
        
    except Exception as e:
        print(f"Erro ao verificar admin: {e}")
        return False



# ROTAS DO CARRINHO
@app.route('/carrinho')
def carrinho():
    # Permite ver carrinho sem login - usar sessão temporária
    
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
                    'tamanho': item.get('tamanho', 'M'),
                    'cor': item.get('cor', 'Padrão'),
                    'subtotal': item_total
                })
                total += item_total
        
        conn.close()
        
        print(f"Debug - Itens detalhados: {len(itens_detalhados)}")  # Debug
        return render_template('carrinho.html', itens=itens_detalhados, total=total)
    except Exception as e:
        print(f"Erro no carrinho: {e}")
        return render_template('carrinho.html', itens=[], total=0)

# 🧹 Rota para limpeza forçada de cache
@app.route('/limpar-cache')
def limpar_cache():
    """Força limpeza completa de cache"""
    from flask import jsonify
    return jsonify({
        'status': 'success',
        'message': 'Cache limpo com sucesso!',
        'timestamp': datetime.now().isoformat(),
        'cache_headers': {
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0'
        }
    })

# 📱 API para configurações do WhatsApp
@app.route('/api/whatsapp-config')
def whatsapp_config():
    """Retorna configurações do WhatsApp da loja"""
    from flask import jsonify
    return jsonify({
        'numero': app.config.get('WHATSAPP_NUMBER', '551166997164602'),
        'loja_nome': app.config.get('WHATSAPP_STORE_NAME', 'CAMILA DE PAULA.')
    })

# API para sacola lateral
@app.route('/api/carrinho')
def api_carrinho():
    """API endpoint para carregar itens da sacola lateral"""
    from flask import jsonify
    
    carrinho_itens = session.get('carrinho', [])
    
    if not carrinho_itens:
        return jsonify({'items': [], 'total': 0})
    
    try:
        conn = get_db_connection()
        itens_api = []
        total = 0
        
        for item in carrinho_itens:
            produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (item['produto_id'],)).fetchone()
            if produto:
                item_total = float(produto['preco']) * item['quantidade']
                itens_api.append({
                    'produto_id': produto['id'],
                    'nome': produto['nome'],
                    'preco': float(produto['preco']),
                    'imagem': produto['imagem'],
                    'quantidade': item['quantidade'],
                    'tamanho': item.get('tamanho', 'M'),
                    'cor': item.get('cor', 'Padrão'),
                    'subtotal': item_total
                })
                total += item_total
        
        conn.close()
        return jsonify({'items': itens_api, 'total': total})
    
    except Exception as e:
        print(f"Erro na API do carrinho: {e}")
        return jsonify({'items': [], 'total': 0, 'error': str(e)})

@app.route('/carrinho/adicionar/<int:produto_id>')
def carrinho_adicionar(produto_id):
    # Permite adicionar ao carrinho sem login - usar sessão temporária
    
    # NOVO: quantidade via querystring ?q= (padrão 1, máx. 99)
    try:
        q = int(request.args.get('q', 1))
    except ValueError:
        q = 1
    quantidade = max(1, min(q, 99))
    
    # Capturar tamanho e cor dos parâmetros
    tamanho = request.args.get('tamanho', 'M')
    cor = request.args.get('cor', 'Padrão')
    
    try:
        conn = get_db_connection()
        produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
        conn.close()

        if not produto:
            if request.headers.get('Content-Type') == 'application/json' or request.args.get('ajax'):
                return jsonify({'success': False, 'message': 'Produto não encontrado!'})
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('index'))

        if 'carrinho' not in session:
            session['carrinho'] = []

        carrinho = session['carrinho']
        # Verificar se o produto já está no carrinho (considerando tamanho e cor)
        item_encontrado = False
        for item in carrinho:
            if (item['produto_id'] == produto_id and 
                item.get('tamanho') == tamanho and 
                item.get('cor') == cor):
                item['quantidade'] += quantidade
                item_encontrado = True
                break
        
        if not item_encontrado:
            carrinho.append({
                'produto_id': produto_id, 
                'quantidade': quantidade,
                'tamanho': tamanho,
                'cor': cor
            })

        session['carrinho'] = carrinho
        session.permanent = True
        session.modified = True

        # Se for requisição AJAX, retornar JSON
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('ajax'):
            from flask import jsonify
            return jsonify({
                'success': True, 
                'message': f'"{produto["nome"]}" adicionado ao carrinho!',
                'produto': {
                    'id': produto['id'],
                    'nome': produto['nome'],
                    'preco': float(produto['preco']),
                    'imagem': produto['imagem'],
                    'tamanho': tamanho,
                    'cor': cor,
                    'quantidade': quantidade
                }
            })

        flash(f'✅ "{produto["nome"]}" x{quantidade} adicionado ao carrinho!', 'success')
        return redirect(request.referrer or url_for('index'))

    except Exception as e:
        print(f"Erro ao adicionar ao carrinho: {e}")
        
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('ajax'):
            from flask import jsonify
            return jsonify({'success': False, 'message': 'Erro ao adicionar produto ao carrinho!'})
            
        flash('Erro ao adicionar produto ao carrinho!', 'error')
        return redirect(url_for('index'))

@app.route('/carrinho/remover/<int:produto_id>')
def carrinho_remover(produto_id):
    # Capturar tamanho e cor dos parâmetros para remoção específica
    tamanho = request.args.get('tamanho')
    cor = request.args.get('cor')
    
    if 'carrinho' in session:
        carrinho = session['carrinho']
        
        if tamanho and cor:
            # Remover item específico considerando tamanho e cor
            session['carrinho'] = [
                item for item in carrinho 
                if not (item['produto_id'] == produto_id and 
                       item.get('tamanho') == tamanho and 
                       item.get('cor') == cor)
            ]
        else:
            # Remover todos os itens deste produto
            session['carrinho'] = [item for item in carrinho if item['produto_id'] != produto_id]
        
        session.permanent = True
        session.modified = True
        
        # Se for requisição AJAX, retornar JSON
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('ajax'):
            from flask import jsonify
            return jsonify({
                'success': True, 
                'message': 'Item removido do carrinho!',
                'carrinho_count': len(session['carrinho'])
            })
        
        flash('Item removido do carrinho!', 'info')
    
    return redirect(url_for('carrinho'))

@app.route('/carrinho/alterar-quantidade/<int:produto_id>')
def carrinho_alterar_quantidade(produto_id):
    """Altera a quantidade de um item específico no carrinho"""
    tamanho = request.args.get('tamanho')
    cor = request.args.get('cor')
    
    # Validação segura do delta
    try:
        delta = int(request.args.get('delta', 0))
        # Limitar delta a valores seguros
        delta = max(-10, min(10, delta))
    except (ValueError, TypeError):
        delta = 0
    
    if 'carrinho' in session and delta != 0:
        carrinho = session['carrinho']
        
        for item in carrinho:
            if (item['produto_id'] == produto_id and 
                item.get('tamanho') == tamanho and 
                item.get('cor') == cor):
                
                nova_quantidade = item['quantidade'] + delta
                
                if nova_quantidade <= 0:
                    # Remove o item se quantidade for 0 ou menor
                    session['carrinho'] = [
                        i for i in carrinho 
                        if not (i['produto_id'] == produto_id and 
                               i.get('tamanho') == tamanho and 
                               i.get('cor') == cor)
                    ]
                else:
                    # Atualiza a quantidade (máximo 99)
                    item['quantidade'] = min(nova_quantidade, 99)
                
                session.permanent = True
                session.modified = True
                break
        
        # Se for requisição AJAX, retornar JSON
        if request.headers.get('Content-Type') == 'application/json' or request.args.get('ajax'):
            from flask import jsonify
            return jsonify({
                'success': True, 
                'message': 'Quantidade atualizada!',
                'carrinho_count': len(session['carrinho'])
            })
    
    return redirect(url_for('carrinho'))

@app.route('/carrinho/limpar')
def carrinho_limpar():
    if 'carrinho' in session:
        session['carrinho'] = []
        session.permanent = True
        flash('Carrinho limpo!', 'info')
    
    return redirect(url_for('carrinho'))

# ROTAS DE CHECKOUT
@app.route('/checkout')
def checkout():
    # Verificar se há itens no carrinho
    carrinho_itens = session.get('carrinho', [])
    
    if not carrinho_itens:
        flash('Seu carrinho está vazio! Adicione produtos antes de finalizar a compra.', 'warning')
        return redirect(url_for('index'))
    
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
                    'tamanho': item.get('tamanho', 'M'),
                    'cor': item.get('cor', 'Padrão'),
                    'subtotal': item_total
                })
                total += item_total
        
        conn.close()
        
        # Dados do usuário logado (se houver)
        user_data = {}
        if 'user_id' in session:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM usuarios WHERE id = ?', (session['user_id'],)).fetchone()
            if user:
                user_data = {
                    'nome': user['nome'],
                    'email': user['email']
                }
            conn.close()
        
        return render_template('checkout.html', 
                             itens=itens_detalhados, 
                             total=total,
                             user_data=user_data)
    except Exception as e:
        print(f"Erro no checkout: {e}")
        flash('Erro ao carregar página de checkout!', 'error')
        return redirect(url_for('carrinho'))

@app.route('/processar-pedido', methods=['POST'])
def processar_pedido():
    try:
        # Verificar se há itens no carrinho
        carrinho_itens = session.get('carrinho', [])
        
        if not carrinho_itens:
            flash('Seu carrinho está vazio!', 'error')
            return redirect(url_for('index'))
        
        # Validação segura dos dados do formulário
        try:
            nome_cliente = validate_form_field(request.form, 'nome', max_length=100)
            email_cliente = validate_form_field(request.form, 'email', max_length=100)
            telefone = validate_form_field(request.form, 'telefone', max_length=20, required=False)
            cep = validate_form_field(request.form, 'cep', max_length=10)
            endereco = validate_form_field(request.form, 'endereco', max_length=200)
            numero = validate_form_field(request.form, 'numero', max_length=10)
            complemento = validate_form_field(request.form, 'complemento', max_length=100, required=False)
            bairro = validate_form_field(request.form, 'bairro', max_length=100)
            cidade = validate_form_field(request.form, 'cidade', max_length=100)
            estado = validate_form_field(request.form, 'estado', max_length=2)
            metodo_pagamento = validate_form_field(request.form, 'metodo_pagamento', max_length=50)
            
            # Validação de email básica
            if '@' not in email_cliente or '.' not in email_cliente:
                raise ValueError('Email inválido')
                
        except ValueError as e:
            flash(f'Erro nos dados: {str(e)}', 'error')
            return redirect(url_for('checkout'))
        
        # Calcular total e preparar itens
        conn = get_db_connection()
        itens_pedido = []
        total = 0
        
        for item in carrinho_itens:
            produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (item['produto_id'],)).fetchone()
            if produto:
                item_total = float(produto['preco']) * item['quantidade']
                itens_pedido.append({
                    'produto_id': produto['id'],
                    'nome': produto['nome'],
                    'preco': float(produto['preco']),
                    'quantidade': item['quantidade'],
                    'tamanho': item.get('tamanho', 'M'),
                    'cor': item.get('cor', 'Padrão'),
                    'subtotal': item_total
                })
                total += item_total
        
        # Salvar pedido no banco
        usuario_id = session.get('user_id')
        itens_json = json.dumps(itens_pedido)
        
        cursor = conn.execute('''
            INSERT INTO pedidos (
                usuario_id, nome_cliente, email_cliente, telefone,
                cep, endereco, numero, complemento, bairro, cidade, estado,
                metodo_pagamento, total, itens
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            usuario_id, nome_cliente, email_cliente, telefone,
            cep, endereco, numero, complemento, bairro, cidade, estado,
            metodo_pagamento, total, itens_json
        ))
        
        pedido_id = cursor.lastrowid
        conn.commit()
        
        # Buscar o pedido criado para gerar mensagem WhatsApp
        pedido = conn.execute('SELECT * FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
        conn.close()
        
        # Limpar carrinho
        session['carrinho'] = []
        session.permanent = True
        
        # Gerar mensagem e URL do WhatsApp
        mensagem_whatsapp = gerar_mensagem_whatsapp(pedido, itens_pedido)
        url_whatsapp = gerar_url_whatsapp(WHATSAPP_NUMERO, mensagem_whatsapp)
        
        # Salvar URL do WhatsApp na sessão para usar na página de sucesso
        session['whatsapp_url'] = url_whatsapp
        session['pedido_mensagem'] = mensagem_whatsapp
        
        flash('Pedido realizado com sucesso!', 'success')
        return redirect(url_for('pedido_sucesso', pedido_id=pedido_id))
    
    except Exception as e:
        print(f"Erro ao processar pedido: {e}")
        flash('Erro ao processar pedido. Tente novamente.', 'error')
        return redirect(url_for('checkout'))

@app.route('/pedido-sucesso/<int:pedido_id>')
def pedido_sucesso(pedido_id):
    try:
        conn = get_db_connection()
        pedido = conn.execute('SELECT * FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
        conn.close()
        
        if not pedido:
            flash('Pedido não encontrado!', 'error')
            return redirect(url_for('index'))
        
        # Parse dos itens do pedido
        itens = json.loads(pedido['itens'])
        
        # Obter dados do WhatsApp da sessão
        whatsapp_url = session.get('whatsapp_url')
        pedido_mensagem = session.get('pedido_mensagem')
        
        # Limpar dados da sessão após usar
        session.pop('whatsapp_url', None)
        session.pop('pedido_mensagem', None)
        
        return render_template('pedido_sucesso.html', 
                             pedido=pedido, 
                             itens_pedido=itens,
                             whatsapp_url=whatsapp_url,
                             pedido_mensagem=pedido_mensagem)
    
    except Exception as e:
        print(f"Erro ao carregar pedido: {e}")
        flash('Erro ao carregar detalhes do pedido!', 'error')
        return redirect(url_for('index'))

@app.route('/meus-pedidos')
def meus_pedidos():
    if 'user_id' not in session:
        flash('Faça login para ver seus pedidos!', 'warning')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        pedidos = conn.execute(
            'SELECT * FROM pedidos WHERE usuario_id = ? ORDER BY created_at DESC',
            (session['user_id'],)
        ).fetchall()
        conn.close()
        
        # Parse dos itens de cada pedido
        pedidos_com_itens = []
        for pedido in pedidos:
            pedido_dict = dict(pedido)
            pedido_dict['itens'] = json.loads(pedido['itens'])
            pedidos_com_itens.append(pedido_dict)
        
        return render_template('pedidos_usuario.html', pedidos=pedidos_com_itens)
    
    except Exception as e:
        print(f"Erro ao carregar pedidos: {e}")
        flash('Erro ao carregar seus pedidos!', 'error')
        return redirect(url_for('index'))

# ROTA PRINCIPAL
@app.route('/')
def index():
    try:
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

# ROTA PRODUTO INDIVIDUAL
@app.route('/produto/<int:produto_id>')
def produto_individual(produto_id):
    try:
        conn = get_db_connection()
        produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
        
        if not produto:
            conn.close()
            flash('Produto não encontrado!', 'error')
            return redirect(url_for('index'))
        
        # Processar imagens adicionais
        imagens_adicionais = get_imagens_adicionais(produto)
        
        # Buscar produtos relacionados da mesma categoria
        # Converter sqlite3.Row para dict para acesso seguro
        produto_dict = dict(produto)
        categoria = produto_dict.get('categoria', '')
        
        produtos_relacionados = conn.execute(
            'SELECT * FROM produtos WHERE categoria = ? AND id != ? ORDER BY RANDOM() LIMIT 4',
            (categoria, produto_id)
        ).fetchall()
        
        conn.close()
        
        return render_template('produto_individual.html', 
                             produto=produto,
                             imagens_adicionais=imagens_adicionais,
                             produtos_relacionados=produtos_relacionados)
    except Exception as e:
        print(f"Erro ao carregar produto: {e}")
        flash('Erro ao carregar produto!', 'error')
        return redirect(url_for('index'))

# ROTA COMPRAR AGORA
@app.route('/comprar-agora')
def comprar_agora():
    """Página para finalizar compra direta de um produto"""
    try:
        # Verificar se há produto selecionado via parâmetros
        produto_id = request.args.get('produto')
        tamanho = request.args.get('tamanho')
        quantidade = request.args.get('quantidade', 1, type=int)
        
        produto = None
        
        if produto_id:
            conn = get_db_connection()
            produto = conn.execute('SELECT * FROM produtos WHERE id = ?', (produto_id,)).fetchone()
            conn.close()
            
            if not produto:
                flash('Produto não encontrado!', 'error')
                return redirect(url_for('index'))
        
        return render_template('comprar_agora.html', 
                             produto=produto,
                             tamanho=tamanho,
                             quantidade=quantidade)
    except Exception as e:
        print(f"Erro ao carregar página de compra: {e}")
        flash('Erro ao carregar página!', 'error')
        return redirect(url_for('index'))

@app.route('/processar-compra', methods=['POST'])
def processar_compra():
    """Processar dados da compra e criar pedido"""
    try:
        data = request.get_json()
        
        # Validar dados recebidos
        if not data or 'cliente' not in data or 'produto' not in data:
            return {'success': False, 'message': 'Dados incompletos'}, 400
        
        conn = get_db_connection()
        
        # Calcular total
        produto = data['produto']
        subtotal = produto['preco'] * produto['quantidade']
        frete = 15.00  # Frete fixo por enquanto
        total = subtotal + frete
        
        # Inserir pedido na base de dados
        itens_json = json.dumps([{
            'produto_id': produto['id'],
            'nome': produto['nome'],
            'preco': produto['preco'],
            'quantidade': produto['quantidade'],
            'tamanho': produto.get('tamanho', ''),
            'imagem': produto.get('imagem', '')
        }])
        
        cursor = conn.execute('''
            INSERT INTO pedidos (
                nome_cliente, email_cliente, telefone, 
                cep, endereco, numero, complemento, bairro, cidade, estado,
                metodo_pagamento, total, itens, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['cliente']['nome'],
            data['cliente']['email'], 
            data['cliente']['telefone'],
            data['endereco']['cep'],
            data['endereco']['endereco'],
            data['endereco']['numero'],
            data['endereco'].get('complemento', ''),
            data['endereco']['bairro'],
            data['endereco']['cidade'],
            data['endereco']['estado'],
            data['pagamento'],
            total,
            itens_json,
            'Pendente'
        ))
        
        pedido_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Se for pagamento PIX, redirecionar para página específica
        if data['pagamento'] == 'pix':
            return {
                'success': True, 
                'pedido_id': pedido_id,
                'redirect_pix': True,
                'message': 'Pedido criado! Redirecionando para pagamento PIX...'
            }
        
        return {
            'success': True, 
            'pedido_id': pedido_id,
            'message': 'Pedido criado com sucesso!'
        }
        
    except Exception as e:
        print(f"Erro ao processar compra: {e}")
        return {'success': False, 'message': 'Erro interno do servidor'}, 500

@app.route('/pagamento-pix/<int:pedido_id>')
def pagamento_pix(pedido_id):
    """Página de pagamento PIX"""
    try:
        conn = get_db_connection()
        pedido = conn.execute('SELECT * FROM pedidos WHERE id = ?', (pedido_id,)).fetchone()
        conn.close()
        
        if not pedido:
            flash('Pedido não encontrado!', 'error')
            return redirect(url_for('index'))
        
        # Gerar código PIX simulado (em produção, usar uma API real)
        codigo_pix = gerar_codigo_pix(pedido['total'], pedido_id)
        
        return render_template('pagamento_pix.html', 
                             pedido=pedido, 
                             codigo_pix=codigo_pix)
    
    except Exception as e:
        print(f"Erro ao carregar pagamento PIX: {e}")
        flash('Erro ao carregar página de pagamento!', 'error')
        return redirect(url_for('index'))

@app.route('/verificar-pagamento-pix', methods=['POST'])
def verificar_pagamento_pix():
    """Verificar status do pagamento PIX"""
    try:
        data = request.get_json()
        pedido_id = data.get('pedido_id')
        
        # Simular verificação (em produção, consultar API do banco/gateway)
        # Por enquanto, simular que 30% dos pagamentos são aprovados
        import random
        pago = random.random() < 0.3  # 30% de chance de estar pago
        
        if pago:
            # Atualizar status do pedido
            conn = get_db_connection()
            conn.execute('UPDATE pedidos SET status = ? WHERE id = ?', 
                        ('Pago', pedido_id))
            conn.commit()
            conn.close()
        
        return jsonify({
            'pago': pago,
            'message': 'Pagamento confirmado!' if pago else 'Pagamento pendente'
        })
    
    except Exception as e:
        print(f"Erro ao verificar pagamento: {e}")
        return jsonify({'pago': False, 'message': 'Erro na verificação'})

def gerar_codigo_pix(valor, pedido_id):
    """Gerar código PIX usando configurações salvas"""
    # Carregar configurações PIX
    config = carregar_configuracoes()
    
    # Valores padrão caso não estejam configurados
    chave_pix = config.get('chavePix', 'contato@uzzerstore.com')
    nome_beneficiario = config.get('nomeBeneficiarioPix', 'UZZERSTORE LTDA')
    cidade_beneficiario = config.get('cidadeBeneficiario', 'SAO PAULO')
    
    # Em produção, usar biblioteca real para PIX (como pypix ou similar)
    # Este é apenas um código simulado para demonstração
    
    # Formato básico do código PIX
    base_code = f"PIX{pedido_id:06d}{int(valor*100):08d}"
    
    # Montar código PIX simplificado (formato real é mais complexo)
    codigo_completo = (
        f"00020126"  # Payload Format Indicator
        f"{len(chave_pix)+4:02d}0014{chave_pix}"  # Merchant Account Information
        f"5303986"  # Transaction Currency (986 = BRL)
        f"54{len(f'{valor:.2f}'):02d}{valor:.2f}"  # Transaction Amount
        f"5802BR"  # Country Code
        f"59{len(nome_beneficiario):02d}{nome_beneficiario}"  # Merchant Name
        f"60{len(cidade_beneficiario):02d}{cidade_beneficiario}"  # Merchant City
        f"62{len(str(pedido_id))+4:02d}05{len(str(pedido_id)):02d}{pedido_id}"  # Additional Data
        f"6304"  # CRC16
    )
    
    # Simular checksum (em produção, calcular CRC16 real)
    checksum = str(abs(hash(codigo_completo)) % 10000).zfill(4)
    
    return codigo_completo + checksum

# ROTA MOBILE
@app.route('/mobile')
def mobile_index():
    try:
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
                             categoria_selecionada=categoria_selecionada,
                             mobile_view=True)
    except Exception as e:
        print(f"Erro na rota mobile: {e}")
        return f"""
        <h1>🏪 UzzerStore Mobile</h1>
        <p>Loja em inicialização...</p>
        <p>Erro: {e}</p>
        <style>
            body {{ font-family: Arial; padding: 20px; text-align: center; }}
            h1 {{ color: #00d4aa; }}
        </style>
        """

# PWA Routes
@app.route('/sw.js')
def service_worker():
    response = app.send_static_file('sw.js')
    response.headers['Content-Type'] = 'application/javascript'
    response.headers['Service-Worker-Allowed'] = '/'
    return response

@app.route('/manifest.json')
def manifest():
    response = app.send_static_file('manifest.json')
    response.headers['Content-Type'] = 'application/manifest+json'
    return response

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

                # Migrar carrinho da sessão para o usuário logado (se houver)
                if 'carrinho' in session and session['carrinho']:
                    # Aqui você pode implementar a migração para banco de dados se quiser
                    # Por agora, mantemos o carrinho na sessão
                    pass

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

@app.route('/admin/configuracoes')
def admin_configuracoes():
    """Página de configurações do admin"""
    if not is_admin():
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        
        # Obter estatísticas para a página de backup
        stats = {
            'total_usuarios': conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0],
            'total_produtos': conn.execute('SELECT COUNT(*) FROM produtos').fetchone()[0],
            'total_pedidos': conn.execute('SELECT COUNT(*) FROM pedidos').fetchone()[0] if conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='pedidos'").fetchone() else 0,
        }
        
        conn.close()
        
        # Carregar configurações salvas
        config = carregar_configuracoes()
        
        return render_template('admin_configuracoes.html', stats=stats, config=config)
    except Exception as e:
        print(f"Erro nas configurações: {e}")
        return f"Erro: {e}"

@app.route('/admin/configuracoes/salvar', methods=['POST'])
def salvar_configuracoes():
    """Salvar configurações do admin"""
    if not is_admin():
        return {'success': False, 'message': 'Acesso negado'}, 403
    
    try:
        data = request.get_json()
        
        # Salvar configurações em arquivo JSON
        config_file = os.path.join(BASE_DIR, 'data', 'config.json')
        
        # Criar diretório se não existir
        os.makedirs(os.path.dirname(config_file), exist_ok=True)
        
        # Carregar configurações existentes ou criar novo
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
        else:
            config = {}
        
        # Atualizar com novas configurações
        config.update(data)
        config['ultima_atualizacao'] = datetime.now().isoformat()
        
        # Salvar arquivo
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        
        print(f"Configurações salvas: {data}")
        
        return {'success': True, 'message': 'Configurações salvas com sucesso!'}
        
    except Exception as e:
        print(f"Erro ao salvar configurações: {e}")
        return {'success': False, 'message': f'Erro interno do servidor: {str(e)}'}, 500

def carregar_configuracoes():
    """Carregar configurações salvas"""
    try:
        config_file = os.path.join(BASE_DIR, 'data', 'config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}
    except Exception as e:
        print(f"Erro ao carregar configurações: {e}")
        return {}

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
        # Imagem principal: pode ser upload via form file 'imagem_file' ou URL no campo 'imagem'
        imagem = None
        imagem_file = request.files.get('imagem_file')
        if imagem_file and imagem_file.filename:
            filename = secure_filename(imagem_file.filename)
            base, ext = os.path.splitext(filename)
            timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
            filename = f"{base}-{timestamp}{ext}"
            upload_dir = os.path.join(BASE_DIR, 'static', 'produtos')
            os.makedirs(upload_dir, exist_ok=True)
            upload_path = os.path.join(upload_dir, filename)
            imagem_file.save(upload_path)
            imagem = f'produtos/{filename}'
        else:
            imagem = request.form.get('imagem', '').strip()  # fallback para URL
        estoque = int(request.form.get('estoque', 0))
        
        # Processar tamanhos selecionados
        tamanhos_selecionados = request.form.getlist('tamanhos[]')
        tamanhos_str = ','.join(tamanhos_selecionados) if tamanhos_selecionados else ''
        
        # Processar imagens adicionais (aceita upload file ou URL)
        imagens_adicionais = []
        for i in range(1, 10):  # Imagens adicionais de 1 a 9 (total 10 com a principal)
            # Checar upload primeiro
            file_field = request.files.get(f'imagem_adicional_file_{i}')
            if file_field and file_field.filename:
                filename = secure_filename(file_field.filename)
                base, ext = os.path.splitext(filename)
                timestamp = datetime.utcnow().strftime('%Y%m%d%H%M%S%f')
                filename = f"{base}-{timestamp}{ext}"
                upload_dir = os.path.join(BASE_DIR, 'static', 'produtos')
                os.makedirs(upload_dir, exist_ok=True)
                upload_path = os.path.join(upload_dir, filename)
                file_field.save(upload_path)
                imagens_adicionais.append(f'produtos/{filename}')
                continue
            # fallback para campo URL
            imagem_adicional = request.form.get(f'imagem_adicional_{i}')
            if imagem_adicional and imagem_adicional.strip():
                imagens_adicionais.append(imagem_adicional.strip())
        
        imagens_adicionais_str = ','.join(imagens_adicionais) if imagens_adicionais else ''
        
        try:
            conn = get_db_connection()
            # Garantir que as colunas existem
            ensure_tamanhos_column(conn)
            ensure_estoque_column(conn)
            ensure_imagens_adicionais_column(conn)
            
            conn.execute('''
                INSERT INTO produtos (nome, preco, categoria, descricao, imagem, imagens_adicionais, tamanhos, estoque)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (nome, preco, categoria, descricao, imagem, imagens_adicionais_str, tamanhos_str, estoque))
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
        imagem = request.form['imagem']  # Imagem principal
        estoque = int(request.form.get('estoque', 0))
        
        # Processar tamanhos selecionados
        tamanhos_selecionados = request.form.getlist('tamanhos[]')
        tamanhos_str = ','.join(tamanhos_selecionados) if tamanhos_selecionados else ''
        
        # Processar imagens adicionais
        imagens_adicionais = []
        for i in range(1, 10):  # Imagens adicionais de 1 a 9 (total 10 com a principal)
            imagem_adicional = request.form.get(f'imagem_adicional_{i}')
            if imagem_adicional and imagem_adicional.strip():
                imagens_adicionais.append(imagem_adicional.strip())
        
        imagens_adicionais_str = ','.join(imagens_adicionais) if imagens_adicionais else ''
        
        try:
            # Garantir que as colunas existem
            ensure_tamanhos_column(conn)
            ensure_estoque_column(conn)
            ensure_imagens_adicionais_column(conn)
            
            conn.execute('''
                UPDATE produtos 
                SET nome = ?, preco = ?, categoria = ?, descricao = ?, imagem = ?, imagens_adicionais = ?, tamanhos = ?, estoque = ?
                WHERE id = ?
            ''', (nome, preco, categoria, descricao, imagem, imagens_adicionais_str, tamanhos_str, estoque, produto_id))
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

@app.route('/admin/produtos/remover-todos', methods=['POST'])
def admin_remover_todos_produtos():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado!'}), 403
    
    try:
        conn = get_db_connection()
        
        # Contar quantos produtos serão removidos
        count = conn.execute('SELECT COUNT(*) as total FROM produtos').fetchone()
        total_produtos = count['total'] if count else 0
        
        if total_produtos == 0:
            conn.close()
            return jsonify({'success': False, 'message': 'Não há produtos para remover!'}), 400
        
        # Remover todos os produtos
        conn.execute('DELETE FROM produtos')
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True, 
            'message': 'Todos os produtos foram removidos com sucesso!',
            'removidos': total_produtos
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'Erro ao remover produtos: {str(e)}'}), 500

@app.route('/admin/relatorios')
def admin_relatorios():
    if not is_admin():
        flash('Acesso negado!', 'error')
        return redirect(url_for('login'))
    
    try:
        conn = get_db_connection()
        
        # Estatísticas básicas
        stats = {}
        
        # Total de produtos
        stats['total_produtos'] = conn.execute('SELECT COUNT(*) as count FROM produtos').fetchone()['count']
        
        # Total de usuários
        stats['total_usuarios'] = conn.execute('SELECT COUNT(*) as count FROM usuarios').fetchone()['count']
        
        # Vendas totais (simular - você pode implementar uma tabela de vendas)
        stats['vendas_total'] = '15.750,80'
        
        # Total de pedidos (simular)
        stats['total_pedidos'] = 127
        
        conn.close()
        return render_template('admin_relatorios.html', stats=stats)
    
    except Exception as e:
        flash(f'Erro ao carregar relatórios: {e}', 'error')
        return redirect(url_for('admin_dashboard'))

@app.route('/admin/relatorios/dados', methods=['POST'])
def admin_relatorios_dados():
    if not is_admin():
        return jsonify({'success': False, 'message': 'Acesso negado'})
    
    try:
        filtros = request.get_json()
        
        # Aqui você implementaria a lógica real de filtragem
        # Por enquanto, retornando dados simulados
        dados = {
            'vendas': {
                'total': 15750.80,
                'periodo': [
                    {'data': '2025-10-01', 'valor': 1200.50},
                    {'data': '2025-10-02', 'valor': 890.00},
                    {'data': '2025-10-03', 'valor': 1450.30},
                    {'data': '2025-10-04', 'valor': 1120.75},
                    {'data': '2025-10-05', 'valor': 2100.20},
                ]
            },
            'pedidos': {
                'total': 127,
                'concluidos': 95,
                'pendentes': 22,
                'cancelados': 10
            },
            'produtos': [
                {'nome': 'Vestido Floral Primavera', 'vendas': 25, 'valor': 4747.50},
                {'nome': 'Calça Jeans Skinny', 'vendas': 18, 'valor': 2338.20},
                {'nome': 'Blusa Básica Algodão', 'vendas': 32, 'valor': 1596.80},
                {'nome': 'Tênis Casual Branco', 'vendas': 15, 'valor': 1847.25},
                {'nome': 'Saia Midi Estampada', 'vendas': 12, 'valor': 1176.00}
            ],
            'categorias': {
                'Feminino': 45,
                'Masculino': 30, 
                'Infantil': 15,
                'Acessórios': 10
            }
        }
        
        return jsonify({'success': True, 'dados': dados})
    
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

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
    conn = get_db_connection()
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

# Inicializar DB apenas uma vez (evita duplicação no debug mode)
import os
if not os.environ.get('WERKZEUG_RUN_MAIN'):
    init_db()

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)  
