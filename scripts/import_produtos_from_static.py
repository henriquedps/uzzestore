#!/usr/bin/env python3
"""
Importa arquivos de static/produtos para a tabela produtos do banco data/app.db.
- Para cada arquivo na pasta cria um produto se não existir uma linha com o mesmo valor em `imagem`.
- Coloca `imagem` como 'produtos/<filename>' (compatível com os templates que usam url_for('static', filename=...)).
- Define defaults razoáveis e tenta inferir categoria a partir do nome do arquivo.
"""
import os
import sqlite3
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'app.db')
PRODUTOS_DIR = os.path.join(BASE_DIR, 'static', 'produtos')

DEFAULT_PRICE = 49.90
DEFAULT_STOCK = 10
DEFAULT_SIZES = 'P,M,G'

def slug_to_title(name):
    name = os.path.splitext(name)[0]
    # remover múltiplos espaços
    name = name.replace('_', ' ').replace('-', ' ')
    name = ' '.join(name.split())
    # capitalizar cada palavra
    return name.title()

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


def main():
    if not os.path.isdir(PRODUTOS_DIR):
        print('Pasta static/produtos não encontrada:', PRODUTOS_DIR)
        return

    files = [f for f in os.listdir(PRODUTOS_DIR) if os.path.isfile(os.path.join(PRODUTOS_DIR, f))]
    if not files:
        print('Nenhum arquivo encontrado em', PRODUTOS_DIR)
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Obter colunas da tabela produtos
    cur.execute("PRAGMA table_info(produtos)")
    cols = [r[1] for r in cur.fetchall()]

    # Colunas que vamos preencher (exceto id)
    insertable = [c for c in cols if c != 'id']

    print('Colunas detectadas em produtos:', insertable)

    # Ler imagens já referenciadas
    cur.execute("SELECT imagem FROM produtos WHERE imagem IS NOT NULL")
    existing = set(r[0] for r in cur.fetchall() if r[0])

    to_insert = []
    for fn in files:
        imagem_field = f'produtos/{fn}'
        if imagem_field in existing:
            print('Pulando (já existe):', imagem_field)
            continue
        nome = slug_to_title(fn)
        preco = DEFAULT_PRICE
        categoria = infer_category(fn)
        descricao = ''
        tamanhos = DEFAULT_SIZES
        estoque = DEFAULT_STOCK
        imagens_adicionais = ''

        row = {
            'nome': nome,
            'preco': preco,
            'imagem': imagem_field,
            'categoria': categoria,
            'descricao': descricao,
            'tamanhos': tamanhos,
            'estoque': estoque,
            'imagens_adicionais': imagens_adicionais
        }
        to_insert.append(row)

    if not to_insert:
        print('Nenhum novo produto para inserir.')
        conn.close()
        return

    # Preparar INSERT dinâmico baseado nas colunas existentes
    cols_to_use = [c for c in insertable if c in ('nome','preco','imagem','categoria','descricao','tamanhos','estoque','imagens_adicionais','created_at')]

    placeholders = ','.join('?' for _ in cols_to_use)
    columns_sql = ','.join(cols_to_use)

    inserted_ids = []
    for r in to_insert:
        values = []
        for c in cols_to_use:
            if c == 'created_at':
                values.append(datetime.utcnow().isoformat())
            else:
                values.append(r.get(c))
        sql = f"INSERT INTO produtos ({columns_sql}) VALUES ({placeholders})"
        cur.execute(sql, values)
        inserted_ids.append(cur.lastrowid)
        print('Inserido:', r['nome'], 'id=', cur.lastrowid)

    conn.commit()
    conn.close()

    print('\nResumo:')
    print('Total arquivos avaliados:', len(files))
    print('Inseridos:', len(inserted_ids))
    if inserted_ids:
        print('IDs inseridos:', inserted_ids)

if __name__ == '__main__':
    main()
