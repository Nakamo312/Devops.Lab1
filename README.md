# DevOps Demo Website

Простой пример того, как Git становится источником правды для всей системы.

## Структура проекта

```
demo-website/
├── index.html      # Основная страница сайта с ракеткой 🚀
├── nginx.conf      # Конфигурация веб-сервера
├── deploy.sh       # Скрипт автоматического развертывания
├── test.sh         # Тестирование ракетки на сайте
├── install-nginx.sh # Скрипт установки nginx
└── README.md       # Документация проекта
```

## Быстрый запуск

1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/prafdin/devops-demo-website.git
   cd devops-demo-website
   ```

2. Установите nginx:
   ```bash
   sudo ./install-nginx.sh
   ```

3. Проверьте что сайт готов к запуску:
   ```bash
   ./test.sh
   ```

4. Запустите развертывание:
   ```bash
   ./deploy.sh
   ```

5. Откройте в браузере: http://localhost:8181
