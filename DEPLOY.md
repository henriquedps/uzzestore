# Deploy no Render - UzzerStore

## ✅ Checklist de Pré-Deploy

Todos os arquivos necessários estão prontos:

- [x] `app.py` - Aplicação Flask principal
- [x] `requirements.txt` - Dependências Python
- [x] `Procfile` - Comando de inicialização (gunicorn)
- [x] `runtime.txt` - Versão do Python (3.11.9)
- [x] `render.yaml` - Configuração do Render
- [x] `config.py` - Configurações da aplicação
- [x] `.gitignore` - Arquivos ignorados pelo Git
- [x] `.env.example` - Exemplo de variáveis de ambiente

## 🚀 Passos para Deploy no Render

### 1. Preparar o Repositório Git

```bash
cd uzzerstore
git init
git add .
git commit -m "Initial commit - Ready for Render deploy"
```

### 2. Criar Repositório no GitHub

1. Acesse https://github.com/new
2. Crie um repositório chamado `uzzerstore`
3. Não inicialize com README, .gitignore ou license
4. Execute os comandos fornecidos:

```bash
git remote add origin https://github.com/SEU-USUARIO/uzzerstore.git
git branch -M main
git push -u origin main
```

### 3. Deploy no Render

1. Acesse https://render.com e faça login
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub
4. Configure:
   - **Name**: uzzerstore
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
   - **Instance Type**: Free (ou escolha conforme necessidade)

### 4. Configurar Variáveis de Ambiente

No painel do Render, vá em "Environment" e adicione:

- `SECRET_KEY`: (clique em "Generate" para criar uma chave segura)
- `FLASK_ENV`: production
- `WHATSAPP_NUMERO`: 551166997164602 (ou seu número)
- `DB_PATH`: /opt/render/project/data/app.db

### 5. Deploy Automático

O Render irá:
1. Clonar seu repositório
2. Instalar as dependências do `requirements.txt`
3. Executar o comando do `Procfile`
4. Disponibilizar sua aplicação em uma URL pública

## 📝 Notas Importantes

### Banco de Dados
- O SQLite será criado automaticamente no primeiro acesso
- Para persistência de dados em produção, considere usar PostgreSQL (Render oferece gratuitamente)
- Para migrar para PostgreSQL:
  ```bash
  pip install psycopg2-binary
  # Adicionar ao requirements.txt: psycopg2-binary==2.9.9
  ```

### Imagens e Arquivos Estáticos
- As imagens na pasta `static/` serão servidas automaticamente
- Para upload de imagens de produtos, considere usar um serviço como:
  - Cloudinary (gratuito até 25GB)
  - AWS S3
  - Render Disk (persistente, pago)

### Monitoramento
- Acesse os logs em tempo real no dashboard do Render
- Configure alertas para erros críticos
- Use o comando: `render logs -f` (via Render CLI)

### Domínio Personalizado
- No Render, vá em "Settings" → "Custom Domain"
- Adicione seu domínio (ex: www.uzzerstore.com.br)
- Configure os registros DNS conforme instruções do Render

## 🔧 Comandos Úteis

### Testar localmente antes do deploy:
```bash
# Instalar dependências
pip install -r requirements.txt

# Executar com Gunicorn (como em produção)
gunicorn app:app

# Executar em modo desenvolvimento
python app.py
```

### Atualizar o site após mudanças:
```bash
git add .
git commit -m "Descrição das mudanças"
git push origin main
# O Render fará deploy automático
```

## 🐛 Troubleshooting

### Erro: "Application failed to start"
- Verifique os logs no dashboard do Render
- Confirme que todas as dependências estão no `requirements.txt`
- Verifique se o `Procfile` está correto

### Erro: "No module named 'app'"
- Certifique-se de que `app.py` está na raiz do repositório
- Verifique se o `Procfile` tem: `web: gunicorn app:app`

### Banco de dados não persiste
- O SQLite em disco temporário do Render não persiste entre deploys
- Solução: Migre para PostgreSQL (recomendado para produção)

## 📚 Recursos Adicionais

- [Documentação do Render](https://render.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)

## 🎉 Pronto!

Após o deploy, seu site estará disponível em:
`https://uzzerstore.onrender.com` (ou o nome que você escolheu)

**Primeira coisa a fazer após o deploy:**
1. Acesse `/admin/login`
2. Crie sua conta de administrador
3. Adicione produtos pela área admin
4. Teste o carrinho e checkout

**Boa sorte com sua loja! 🛍️**
