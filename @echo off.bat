@echo off
echo 🚀 Iniciando deploy das alterações...

REM Verificar se está na pasta correta
if not exist "app.py" (
    echo ❌ Erro: Execute este script na pasta do projeto (onde está o app.py)
    pause
    exit /b 1
)

REM Adicionar todas as alterações
echo 📦 Adicionando arquivos...
git add .

REM Verificar se há alterações
git diff --cached --quiet
if %errorlevel% == 0 (
    echo ℹ️ Nenhuma alteração encontrada para commit.
    pause
    exit /b 0
)

REM Pedir mensagem do commit
set /p "mensagem=💬 Digite a mensagem do commit (ou pressione Enter para padrão): "
if "%mensagem%"=="" set "mensagem=Atualizações do UzzerStore - %date% %time%"

REM Fazer commit
echo 💾 Fazendo commit...
git commit -m "%mensagem%"
if %errorlevel% neq 0 (
    echo ❌ Erro no commit!
    pause
    exit /b 1
)

REM Fazer push
echo 🌐 Enviando para GitHub...
git push
if %errorlevel% == 0 (
    echo ✅ Deploy realizado com sucesso!
    echo 🔗 Suas alterações foram enviadas para o GitHub
    echo ⏳ O Render fará o deploy automaticamente em alguns minutos
) else (
    echo ❌ Erro no push!
    pause
    exit /b 1
)

REM Opcional: Abrir o site
set /p "abrirSite=🌍 Deseja abrir o site? (s/n): "
if /i "%abrirSite%"=="s" start https://uzzerstore.onrender.com

echo 🎉 Deploy concluído!
pause