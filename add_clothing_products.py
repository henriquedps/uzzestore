#!/usr/bin/env python3
"""
Script para adicionar produtos de roupas à loja UzzeStore
"""

import sqlite3
import os

def add_clothing_products():
    """Adiciona produtos de roupas à base de dados"""
    
    # Conectar ao banco de dados
    db_path = os.path.join('data', 'app.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Produtos de roupas para adicionar
    produtos = [
        # FEMININO
        {
            'nome': 'Vestido Floral Primavera',
            'preco': 189.90,
            'categoria': 'Feminino',
            'descricao': 'Vestido midi com estampa floral delicada, perfeito para ocasiões especiais e dias ensolarados.',
            'imagem': 'https://images.unsplash.com/photo-1515372039744-b8f02a3ae446?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'PP,P,M,G,GG',
            'estoque': 25
        },
        {
            'nome': 'Blusa Básica Algodão',
            'preco': 49.90,
            'categoria': 'Feminino',
            'descricao': 'Blusa básica de algodão, confortável e versátil para o dia a dia.',
            'imagem': 'https://images.unsplash.com/photo-1551803091-e20673f15770?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'PP,P,M,G,GG',
            'estoque': 30
        },
        {
            'nome': 'Calça Jeans Skinny Feminina',
            'preco': 129.90,
            'categoria': 'Feminino',
            'descricao': 'Calça jeans skinny com lavação moderna, modelagem que valoriza o corpo feminino.',
            'imagem': 'https://images.unsplash.com/photo-1541099649105-f69ad21f3246?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'PP,P,M,G,GG',
            'estoque': 20
        },
        {
            'nome': 'Saia Midi Plissada',
            'preco': 89.90,
            'categoria': 'Feminino',
            'descricao': 'Saia midi plissada elegante, ideal para compor looks femininos e sofisticados.',
            'imagem': 'https://images.unsplash.com/photo-1583496661160-fb5886a13d27?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'PP,P,M,G,GG',
            'estoque': 15
        },
        
        # MASCULINO
        {
            'nome': 'Camisa Social Slim Branca',
            'preco': 159.90,
            'categoria': 'Masculino',
            'descricao': 'Camisa social slim fit branca, tecido de alta qualidade, perfeita para trabalho e eventos.',
            'imagem': 'https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG,XG',
            'estoque': 18
        },
        {
            'nome': 'Camiseta Básica Preta',
            'preco': 39.90,
            'categoria': 'Masculino',
            'descricao': 'Camiseta básica preta de algodão, corte moderno e confortável.',
            'imagem': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG,XG',
            'estoque': 35
        },
        {
            'nome': 'Calça Chino Azul Marinho',
            'preco': 119.90,
            'categoria': 'Masculino',
            'descricao': 'Calça chino azul marinho, estilo casual elegante, versátil para diversas ocasiões.',
            'imagem': 'https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG,XG',
            'estoque': 22
        },
        {
            'nome': 'Polo Listrada Verão',
            'preco': 79.90,
            'categoria': 'Masculino',
            'descricao': 'Polo listrada casual, ideal para o verão e atividades de lazer.',
            'imagem': 'https://images.unsplash.com/photo-1618354691373-d851c5c3a990?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG,XG',
            'estoque': 28
        },
        
        # CAMISETAS
        {
            'nome': 'Camiseta Oversized Tie Dye',
            'preco': 59.90,
            'categoria': 'Camisetas',
            'descricao': 'Camiseta oversized com estampa tie dye moderna, tendência da moda jovem.',
            'imagem': 'https://images.unsplash.com/photo-1576566588028-4147f3842f27?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG',
            'estoque': 30
        },
        {
            'nome': 'Camiseta Estampada Vintage',
            'preco': 49.90,
            'categoria': 'Camisetas',
            'descricao': 'Camiseta com estampa vintage retrô, estilo descolado para looks casuais.',
            'imagem': 'https://images.unsplash.com/photo-1562157873-818bc0726f68?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG,XG',
            'estoque': 25
        },
        
        # CALÇAS
        {
            'nome': 'Calça Cargo Militar',
            'preco': 149.90,
            'categoria': 'Calças',
            'descricao': 'Calça cargo estilo militar com múltiplos bolsos, tendência urbana e funcional.',
            'imagem': 'https://images.unsplash.com/photo-1594633312681-425c7b97ccd1?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG,XG',
            'estoque': 15
        },
        {
            'nome': 'Legging Fitness Preta',
            'preco': 69.90,
            'categoria': 'Calças',
            'descricao': 'Legging fitness de alta compressão, ideal para treinos e atividades físicas.',
            'imagem': 'https://images.unsplash.com/photo-1506629905607-45cf4b3283f2?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'PP,P,M,G,GG',
            'estoque': 40
        },
        
        # VESTIDOS
        {
            'nome': 'Vestido Longo Boho',
            'preco': 259.90,
            'categoria': 'Vestidos',
            'descricao': 'Vestido longo estilo boho chic com detalhes em renda, perfeito para festivais e eventos.',
            'imagem': 'https://images.unsplash.com/photo-1566479179817-c0a96efe9011?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'PP,P,M,G,GG',
            'estoque': 12
        },
        {
            'nome': 'Vestido Curto Festa',
            'preco': 199.90,
            'categoria': 'Vestidos',
            'descricao': 'Vestido curto elegante para festas e ocasiões especiais, corte moderno e feminino.',
            'imagem': 'https://images.unsplash.com/photo-1620331313351-fa95dec6a8e0?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'PP,P,M,G,GG',
            'estoque': 8
        },
        
        # CALÇADOS
        {
            'nome': 'Tênis Branco Couro',
            'preco': 299.90,
            'categoria': 'Calçados',
            'descricao': 'Tênis branco de couro genuíno, design minimalista e versátil para diversos looks.',
            'imagem': 'https://images.unsplash.com/photo-1549298916-b41d501d3772?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': '35,36,37,38,39,40,41,42,43,44',
            'estoque': 20
        },
        {
            'nome': 'Bota Feminina Cano Alto',
            'preco': 249.90,
            'categoria': 'Calçados',
            'descricao': 'Bota feminina de cano alto em couro sintético, estilo moderno e confortável.',
            'imagem': 'https://images.unsplash.com/photo-1544966503-7cc5ac882d5e?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': '35,36,37,38,39,40',
            'estoque': 15
        },
        
        # ACESSÓRIOS
        {
            'nome': 'Bolsa Feminina Transversal',
            'preco': 89.90,
            'categoria': 'Acessórios',
            'descricao': 'Bolsa transversal pequena e elegante, perfeita para o dia a dia da mulher moderna.',
            'imagem': 'https://images.unsplash.com/photo-1553062407-98eeb64c6a62?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'Único',
            'estoque': 25
        },
        {
            'nome': 'Óculos de Sol Aviador',
            'preco': 129.90,
            'categoria': 'Acessórios',
            'descricao': 'Óculos de sol estilo aviador clássico, proteção UV400 e design atemporal.',
            'imagem': 'https://images.unsplash.com/photo-1511499767150-a48a237f0083?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'Único',
            'estoque': 30
        },
        {
            'nome': 'Relógio Masculino Digital',
            'preco': 179.90,
            'categoria': 'Acessórios',
            'descricao': 'Relógio masculino digital esportivo, à prova d\'água e multifuncional.',
            'imagem': 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'Único',
            'estoque': 18
        },
        
        # PROMOÇÃO
        {
            'nome': 'Kit 3 Camisetas Básicas',
            'preco': 89.90,
            'categoria': 'Promoção',
            'descricao': 'Kit promocional com 3 camisetas básicas nas cores branca, preta e cinza.',
            'imagem': 'https://images.unsplash.com/photo-1571945153237-4929e783af4a?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG',
            'estoque': 50
        },
        {
            'nome': 'Conjunto Moletom Promoção',
            'preco': 119.90,
            'categoria': 'Promoção',
            'descricao': 'Conjunto moletom (blusa + calça) em promoção especial, conforto e estilo.',
            'imagem': 'https://images.unsplash.com/photo-1586790170083-2f9ceadc732d?ixlib=rb-4.0.3&auto=format&fit=crop&w=400&q=80',
            'tamanhos': 'P,M,G,GG',
            'estoque': 20
        }
    ]
    
    # Verificar se a tabela produtos existe e tem as colunas necessárias
    cursor.execute("PRAGMA table_info(produtos)")
    columns = [column[1] for column in cursor.fetchall()]
    
    # Garantir que as colunas necessárias existem
    if 'tamanhos' not in columns:
        cursor.execute("ALTER TABLE produtos ADD COLUMN tamanhos TEXT")
        print("✅ Coluna 'tamanhos' adicionada")
    
    if 'estoque' not in columns:
        cursor.execute("ALTER TABLE produtos ADD COLUMN estoque INTEGER DEFAULT 0")
        print("✅ Coluna 'estoque' adicionada")
    
    if 'imagens_adicionais' not in columns:
        cursor.execute("ALTER TABLE produtos ADD COLUMN imagens_adicionais TEXT")
        print("✅ Coluna 'imagens_adicionais' adicionada")
    
    # Limpar produtos existentes (opcional - remova este bloco se quiser manter produtos existentes)
    print("🗑️ Removendo produtos existentes...")
    cursor.execute("DELETE FROM produtos")
    
    # Inserir novos produtos
    print("📦 Adicionando produtos de roupas...")
    
    for produto in produtos:
        cursor.execute("""
            INSERT INTO produtos (nome, preco, categoria, descricao, imagem, tamanhos, estoque)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            produto['nome'],
            produto['preco'],
            produto['categoria'],
            produto['descricao'],
            produto['imagem'],
            produto['tamanhos'],
            produto['estoque']
        ))
        
        print(f"✅ Adicionado: {produto['nome']} - {produto['categoria']} - R$ {produto['preco']}")
    
    # Confirmar mudanças
    conn.commit()
    
    # Mostrar estatísticas
    cursor.execute("SELECT COUNT(*) FROM produtos")
    total_produtos = cursor.fetchone()[0]
    
    cursor.execute("SELECT categoria, COUNT(*) FROM produtos GROUP BY categoria")
    categorias = cursor.fetchall()
    
    print(f"\n📊 RESUMO:")
    print(f"Total de produtos: {total_produtos}")
    print(f"Categorias:")
    for categoria, count in categorias:
        print(f"  • {categoria}: {count} produtos")
    
    conn.close()
    print(f"\n🎉 Produtos de roupas adicionados com sucesso à UzzeStore!")

if __name__ == "__main__":
    add_clothing_products()