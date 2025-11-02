# 👗 UzzeStore - Loja de Roupas Online

Uma moderna loja de roupas online desenvolvida com Flask, apresentando uma experiência de compra elegante e responsiva.

## ✨ Características Principais

### 🛍️ Catálogo de Produtos
- **Moda Feminina**: Vestidos, blusas, calças, saias e mais
- **Moda Masculina**: Camisas sociais, camisetas, calças chino, polos
- **Camisetas**: Variados estilos para todos os gostos
- **Calças**: Jeans, leggings, cargo e mais opções
- **Vestidos**: Do casual ao elegante para ocasiões especiais
- **Calçados**: Tênis, botas e sapatos para completar o look
- **Acessórios**: Bolsas, óculos, relógios e complementos
- **Promoções**: Ofertas especiais e kits promocionais

### 🎨 Interface Moderna
- Design responsivo e elegante
- Banners rotativos com categorias em destaque
- Sistema de filtros avançado por categoria, preço e tamanho
- Cards de produtos com hover effects e animações
- Cores e tipografia cuidadosamente selecionadas

### 🛒 Funcionalidades de E-commerce
- Sistema de carrinho de compras
- Sacola lateral (sidebar cart) com atualizações em tempo real
- Checkout simplificado com dados de entrega
- Integração com WhatsApp para finalização de pedidos
- Gestão de estoque e tamanhos
- Sistema de usuários e autenticação

### 🔧 Painel Administrativo
- Dashboard com estatísticas
- Gestão completa de produtos
- Adicionar, editar e remover produtos
- Upload de múltiplas imagens por produto
- Controle de estoque e tamanhos disponíveis
- Visualização de pedidos

## 🚀 Tecnologias Utilizadas

- **Backend**: Python Flask
- **Banco de Dados**: SQLite
- **Frontend**: HTML5, CSS3, JavaScript
- **Estilização**: CSS moderno com variáveis CSS e gradientes
- **Responsividade**: Design mobile-first
- **Segurança**: Hash de senhas, validação de dados
- **API**: Endpoints para carrinho e filtros

## 📱 Recursos Responsivos

- Layout adaptativo para mobile, tablet e desktop
- Navegação otimizada para telas menores
- Cards de produtos redimensionáveis
- Banners responsivos com textos adaptativos
- Menu hamburger para dispositivos móveis

## 🎯 Categorias de Produtos

### Feminino
- Vestidos (midi, longos, curtos)
- Blusas e camisetas
- Calças (jeans, leggings, sociais)
- Saias e shorts
- Lingerie e moda íntima

### Masculino
- Camisas sociais e casuais
- Camisetas e polos
- Calças (jeans, chino, social)
- Bermudas e shorts
- Underwear

### Calçados
- Tênis esportivos e casuais
- Sapatos sociais
- Botas e botinas
- Sandálias e chinelos
- Sapatos femininos

### Acessórios
- Bolsas e carteiras
- Óculos de sol
- Relógios
- Cintos
- Bijuterias e joias

## 🛠️ Como Executar

1. **Clone o repositório**:
   ```bash
   git clone [url-do-repositorio]
   cd uzzerstore
   ```

2. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure o banco de dados**:
   ```bash
   python -c "from app import init_db; init_db()"
   ```

4. **Adicione produtos de exemplo**:
   ```bash
   python add_clothing_products.py
   ```

5. **Execute a aplicação**:
   ```bash
   python app.py
   ```

6. **Acesse no navegador**:
   ```
   http://localhost:5000
   ```

## 👤 Contas de Teste

### Administrador
- **Email**: admin@uzzerstore.com
- **Senha**: Admin@2024!

### Cliente
Crie uma conta através da página de cadastro.

## 📁 Estrutura do Projeto

```
uzzerstore/
├── app.py                 # Aplicação principal Flask
├── config.py             # Configurações
├── add_clothing_products.py  # Script para adicionar produtos
├── data/
│   └── app.db            # Banco de dados SQLite
├── static/
│   ├── css/              # Estilos CSS
│   ├── js/               # JavaScript
│   └── imagens/          # Imagens estáticas
├── templates/
│   ├── base.html         # Template base
│   ├── index.html        # Página inicial
│   ├── produto_individual.html
│   ├── carrinho.html
│   ├── checkout.html
│   └── admin/            # Templates administrativos
└── requirements.txt      # Dependências Python
```

## 🎨 Destaques Visuais

- **Paleta de Cores**: Tons elegantes com destaques em laranja e dourado
- **Tipografia**: Inter para textos e Playfair Display para títulos
- **Animações**: Transições suaves e efeitos hover
- **Cards Futuristas**: Bordas com gradiente e efeitos de luz
- **Banners Dinâmicos**: Slides com textos coloridos letra por letra

## 🔮 Funcionalidades Futuras

- [ ] Sistema de avaliações e comentários
- [ ] Wishlist/Lista de desejos
- [ ] Cupons de desconto
- [ ] Programa de fidelidade
- [ ] Notificações push
- [ ] Chat de atendimento
- [ ] Comparador de produtos
- [ ] Recomendações personalizadas

## 🤝 Contribuição

Contribuições são bem-vindas! Por favor:

1. Faça um fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Contato

Para dúvidas ou sugestões, entre em contato através do WhatsApp integrado na aplicação ou crie uma issue no repositório.

---

**UzzeStore** - Onde a moda encontra a tecnologia! 👗✨