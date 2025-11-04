#!/usr/bin/env python3
"""
Atualiza a coluna `tamanhos` na tabela produtos para usar tamanhos numéricos
para produtos das categorias Calças/Calcas e Bermudas.
- Para cada produto com categoria que contenha 'calç'/'calca'/'bermuda' tenta
  extrair números (ex: 36, 38) do nome ou do campo imagem.
- Se encontrar números, define tamanhos para a lista única encontrada.
- Caso contrário, define para uma lista padrão: '36,38,40,42,44'.
"""
import os
import re
import sqlite3

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, 'data', 'app.db')

NUMERIC_DEFAULT = '36,38,40,42,44'

def extract_numbers(s):
    if not s:
        return []
    # Encontrar números com 2 dígitos (ex: 36) ou 2-3 dígitos
    nums = re.findall(r"\b(\d{2,3})\b", s)
    # Remover zeros à esquerda e duplicatas mantendo ordem
    seen = []
    for n in nums:
        n2 = str(int(n))
        if n2 not in seen:
            seen.append(n2)
    return seen


def main():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # Selecionar produtos com categoria parecida
    cur.execute("SELECT id, nome, imagem, categoria, tamanhos FROM produtos")
    rows = cur.fetchall()

    updates = []
    for row in rows:
        pid, nome, imagem, categoria, tamanhos = row
        if not categoria:
            continue
        cat = categoria.lower()
        if 'calç' in cat or 'calca' in cat or 'calças' in cat or 'calcas' in cat or 'bermuda' in cat or 'bermudas' in cat:
            # tentar extrair numeros de nome e imagem
            numbers = extract_numbers(nome or '')
            if not numbers:
                numbers = extract_numbers(imagem or '')
            if numbers:
                new_tamanhos = ','.join(numbers)
            else:
                # se já tem tamanhos e parecem numéricos, manter
                existing_nums = extract_numbers(tamanhos or '')
                if existing_nums:
                    new_tamanhos = ','.join(existing_nums)
                else:
                    new_tamanhos = NUMERIC_DEFAULT
            if (tamanhos or '') != new_tamanhos:
                updates.append((new_tamanhos, pid, tamanhos))

    if not updates:
        print('Nenhuma atualização necessária para calças/bermudas.')
        conn.close()
        return

    print('Atualizações a aplicar:', len(updates))
    for new_tam, pid, old in updates:
        print('-> id=', pid, 'de', old, 'para', new_tam)
        cur.execute('UPDATE produtos SET tamanhos = ? WHERE id = ?', (new_tam, pid))

    conn.commit()
    conn.close()
    print('Atualização concluída:', len(updates), 'registros atualizados.')

if __name__ == '__main__':
    main()
