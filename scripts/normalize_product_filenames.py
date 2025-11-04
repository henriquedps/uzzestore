#!/usr/bin/env python3
"""
Renomeia arquivos em static/produtos para nomes URL-friendly (kebab-case) e atualiza
os campos `imagem` e `imagens_adicionais` na tabela produtos.
Gera um backup JSON em scripts/filename_map.json com o mapeamento {old: new}.

Riscos: renomeia arquivos no disco e atualiza o DB; cria backup do mapeamento.
"""
import os
import re
import json
import unicodedata
import sqlite3
from collections import defaultdict

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
PROD_DIR = os.path.join(BASE_DIR, 'static', 'produtos')
DB_PATH = os.path.join(BASE_DIR, 'data', 'app.db')
MAP_PATH = os.path.join(BASE_DIR, 'scripts', 'filename_map.json')

# keep extension
def normalize_filename(filename):
    name, ext = os.path.splitext(filename)
    # normalize unicode -> NFC
    name = unicodedata.normalize('NFC', name)
    # lowercase
    name = name.lower()
    # remove degree symbol º and similar
    name = name.replace('º', 'o')
    # replace non-alnum by hyphen
    name = re.sub(r"[^a-z0-9]+", '-', name)
    # remove leading/trailing hyphens
    name = name.strip('-')
    if not name:
        name = 'file'
    return f"{name}{ext}"


def main():
    if not os.path.isdir(PROD_DIR):
        print('Pasta não encontrada:', PROD_DIR)
        return

    files = [f for f in os.listdir(PROD_DIR) if os.path.isfile(os.path.join(PROD_DIR, f))]
    if not files:
        print('Nenhum arquivo em', PROD_DIR)
        return

    # build mapping old->new, avoiding collisions
    existing_names = set(files)
    target_names = set()
    mapping = {}
    collisions = defaultdict(list)

    for f in files:
        new = normalize_filename(f)
        # if new collides with another target, disambiguate
        base, ext = os.path.splitext(new)
        i = 1
        candidate = new
        while candidate in target_names:
            candidate = f"{base}-{i}{ext}"
            i += 1
        # if candidate exists as a different existing file on disk, we still allow (we will handle by renaming order)
        mapping[f] = candidate
        target_names.add(candidate)

    # Save a copy of original mapping before moving
    with open(MAP_PATH, 'w', encoding='utf-8') as mf:
        json.dump({'mapping': mapping, 'note': 'old -> new (relative filenames, not paths)'}, mf, ensure_ascii=False, indent=2)

    print('Mapping created. Will rename files now...')

    # To avoid overwriting, perform moves using a temp prefix for files that need to move to existing name
    temp_prefix = '__tmp_rename__'
    temp_created = []

    # First pass: for targets that already exist as original files but are different, move original to temp
    for old, new in mapping.items():
        if old == new:
            continue
        new_path = os.path.join(PROD_DIR, new)
        old_path = os.path.join(PROD_DIR, old)
        if os.path.exists(new_path) and new != old:
            # move the existing target to temp to free the name
            tmp = os.path.join(PROD_DIR, temp_prefix + new)
            print(f"Temporarily renaming existing target {new} -> {os.path.basename(tmp)}")
            os.rename(new_path, tmp)
            temp_created.append((tmp, new_path))

    # Second pass: rename old -> new
    renamed = {}
    for old, new in mapping.items():
        if old == new:
            renamed[old] = new
            continue
        old_path = os.path.join(PROD_DIR, old)
        new_path = os.path.join(PROD_DIR, new)
        if not os.path.exists(old_path):
            print('Aviso: arquivo esperado não encontrado, pulando:', old)
            continue
        print('Renomeando:', old, '->', new)
        os.rename(old_path, new_path)
        renamed[old] = new

    # Restore temp files (move temp -> desired new name for those that were moved)
    for tmp_path, desired_path in temp_created:
        if os.path.exists(tmp_path):
            # If desired_path already exists (due to rename), disambiguate
            if os.path.exists(desired_path):
                base, ext = os.path.splitext(desired_path)
                i = 1
                candidate = f"{base}-{i}{ext}"
                while os.path.exists(candidate):
                    i += 1
                    candidate = f"{base}-{i}{ext}"
                final_path = candidate
            else:
                final_path = desired_path
            print('Restaurando temp', os.path.basename(tmp_path), '->', os.path.basename(final_path))
            os.rename(tmp_path, final_path)

    # Update DB
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    # load products
    cur.execute('SELECT id, imagem, imagens_adicionais FROM produtos')
    rows = cur.fetchall()

    updates = []

    for pid, imagem, imagens_ad in rows:
        orig_imagem = imagem
        changed = False
        if imagem:
            # imagem stored might already be 'produtos/<name>' or a URL
            if imagem.startswith('produtos/'):
                filename = imagem.split('/', 1)[1]
                if filename in renamed and renamed[filename] != filename:
                    nova = 'produtos/' + renamed[filename]
                    imagem = nova
                    changed = True
        # imagens_adicionais is comma separated
        if imagens_ad:
            parts = [p.strip() for p in imagens_ad.split(',') if p.strip()]
            new_parts = []
            for p in parts:
                if p.startswith('produtos/'):
                    fname = p.split('/',1)[1]
                    if fname in renamed and renamed[fname] != fname:
                        new_parts.append('produtos/' + renamed[fname])
                        changed = True
                    else:
                        new_parts.append(p)
                else:
                    new_parts.append(p)
            imagens_ad = ','.join(new_parts)
        if changed:
            updates.append((imagem, imagens_ad, pid, orig_imagem))

    print('\nDB updates to apply:', len(updates))
    for imagem_new, imagens_ad_new, pid, orig in updates:
        print('-> id', pid, 'imagem:', orig, '->', imagem_new)
        cur.execute('UPDATE produtos SET imagem = ?, imagens_adicionais = ? WHERE id = ?', (imagem_new, imagens_ad_new, pid))

    conn.commit()
    conn.close()

    # write final mapping with renamed set
    with open(MAP_PATH, 'w', encoding='utf-8') as mf:
        json.dump({'mapping': renamed}, mf, ensure_ascii=False, indent=2)

    print('\nRenomeação concluída. Mapeamento salvo em', MAP_PATH)

if __name__ == '__main__':
    main()
