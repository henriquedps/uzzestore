import sqlite3
import os
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB = os.path.join(BASE_DIR, 'data', 'app.db')
print('Using DB:', DB)
if not os.path.exists(DB):
    print('DB file not found')
    raise SystemExit(1)
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
cur = conn.cursor()
try:
    total = cur.execute('SELECT COUNT(*) as c FROM produtos').fetchone()['c']
except Exception as e:
    print('Error reading produtos table:', e)
    conn.close()
    raise
print('Total produtos =', total)
rows = cur.execute('SELECT id, nome, imagem, categoria FROM produtos ORDER BY id DESC LIMIT 10').fetchall()
for r in rows:
    print(dict(r))
conn.close()