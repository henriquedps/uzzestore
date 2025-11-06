"""Script simples para migrar dados da tabela `produtos` do SQLite local para o MySQL configurado via SQLAlchemy.

Uso:
- Defina a variável de ambiente MYSQL_URL com a URL de conexão MySQL (ex: mysql+pymysql://user:pass@host:3306/dbname)
- Certifique-se de que as dependências estão instaladas e que o banco MySQL está acessível
- Execute:
    $env:MYSQL_URL='mysql+pymysql://user:pass@host:3306/dbname'
    $env:FLASK_APP='app.py'
    C:/Users/henri/OneDrive/Desktop/loja-de-roupas-flask/uzzerstore/.venv/Scripts/python.exe scripts/migrate_sqlite_to_mysql.py

Observações:
- Este script migra somente a tabela `produtos`. Você pode estendê-lo para outras tabelas.
- Faça backup dos bancos antes de rodar em produção.
"""

import os
import sqlite3
from decimal import Decimal

# Ajuste o caminho do DB SQLite local
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SQLITE_PATH = os.path.join(BASE_DIR, 'data', 'app.db')

# Importar o app e os modelos SQLAlchemy
from app import app, db, Produto


def migrate_produtos():
    if not os.path.exists(SQLITE_PATH):
        print(f"Arquivo SQLite não encontrado em: {SQLITE_PATH}")
        return

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute('SELECT * FROM produtos')
    rows = cur.fetchall()
    print(f"{len(rows)} produtos encontrados no SQLite. Preparando para migrar...")

    migrated = 0
    with app.app_context():
        for r in rows:
            try:
                # Verifica se já existe produto similar (por id ou nome)
                exists = Produto.query.filter_by(nome=r['nome']).first()
                if exists:
                    print(f"Pulando produto já existente: {r['nome']}")
                    continue

                preco = Decimal(r['preco']) if r['preco'] not in (None, '') else Decimal('0.00')
                produto = Produto(
                    nome=r['nome'],
                    preco=preco,
                    categoria=r.get('categoria'),
                    descricao=r.get('descricao'),
                    imagem=r.get('imagem'),
                    estoque=int(r.get('estoque') or 0),
                    tamanhos=r.get('tamanhos') or '',
                    visivel=bool(int(r.get('visivel', 1)))
                )
                db.session.add(produto)
                migrated += 1
            except Exception as e:
                print(f"Erro ao migrar produto {r.get('nome')}: {e}")

        try:
            db.session.commit()
            print(f"Migração concluída. {migrated} produtos inseridos no MySQL.")
        except Exception as e:
            db.session.rollback()
            print(f"Erro ao commitar migração: {e}")

    conn.close()


if __name__ == '__main__':
    migrate_produtos()
