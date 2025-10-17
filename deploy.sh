#!/bin/bash
echo "🚀 Запуск деплоя Catty Reminders App"

echo "⏹️  Остановка службы..."
sudo systemctl stop catty-reminders

echo "📦 Установка зависимостей..."
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
fi

pip3 install -r requirements.txt

echo "▶️  Запуск службы..."
sudo systemctl start catty-reminders

sleep 2
sudo systemctl status catty-reminders --no-pager

echo "✅ Деплой завершен"
