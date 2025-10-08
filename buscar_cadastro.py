import os
import glob

def buscar_cadastro_nos_arquivos():
    # Buscar em todos os arquivos .html e .py
    arquivos = glob.glob('**/*.html', recursive=True) + glob.glob('**/*.py', recursive=True)
    
    encontrados = []
    
    for arquivo in arquivos:
        try:
            with open(arquivo, 'r', encoding='utf-8') as f:
                conteudo = f.read()
                linhas = conteudo.split('\n')
                
                for i, linha in enumerate(linhas, 1):
                    if 'cadastro' in linha.lower() and ('url_for' in linha or 'redirect' in linha):
                        encontrados.append({
                            'arquivo': arquivo,
                            'linha': i,
                            'conteudo': linha.strip()
                        })
        except Exception as e:
            print(f"Erro ao ler {arquivo}: {e}")
    
    return encontrados

if __name__ == '__main__':
    print("🔍 Buscando referências a 'cadastro'...")
    resultados = buscar_cadastro_nos_arquivos()
    
    if resultados:
        print(f"\n❌ Encontradas {len(resultados)} referências:")
        for resultado in resultados:
            print(f"\n📁 {resultado['arquivo']}")
            print(f"📍 Linha {resultado['linha']}: {resultado['conteudo']}")
    else:
        print("\n✅ Nenhuma referência a 'cadastro' encontrada!")