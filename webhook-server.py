#!/usr/bin/env python3
import tempfile
import subprocess
import os
import json
import hashlib
import hmac
from datetime import datetime
from http.server import HTTPServer, BaseHTTPRequestHandler
import sys
import requests

PORT = 8080
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', '')  
APP_ID = os.getenv('ID', 'localhost')  # ← здесь
PROXY_DOMAIN = os.getenv('PROXY', 'local')  # ← здесь
TOKEN = os.getenv('TOKEN', 'local') 
class WebhookHandler(BaseHTTPRequestHandler):

    def do_POST(self):
        try:
            content_length = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_length)

            try:
                payload = json.loads(body.decode('utf-8'))
                self._process_webhook(payload)

                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "success"}')

            except json.JSONDecodeError:
                print("❌ Ошибка парсинга JSON")
                self.send_response(400)
                self.end_headers()
                
        except BrokenPipeError:
            print("   ℹ️  Клиент закрыл соединение до отправки ответа")
            self.send_response(200)
        except Exception as e:
            print(f"   ❌ Ошибка в обработке запроса: {e}")

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()

        html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>DevOps Webhook Demo</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; background-color: #f5f5f5; }}
                .container {{ background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                h1 {{ color: #4d90cd; text-align: center; }}
                .info {{ background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🚀 DevOps Webhook Demo Server</h1>
                <div class="info">
                    <p><strong>Статус:</strong> Сервер активен и ожидает webhook события от GitHub</p>
                    <p><strong>Время запуска:</strong> {time}</p>
                    <p><strong>Порт:</strong> {port}</p>
                    <p><strong>GitHub Status:</strong> {github_status}</p>
                </div>
                <p>Этот сервер демонстрирует как Git события могут автоматически запускать процессы.</p>
                <p>Каждый push, pull request или release будет логироваться в консоли сервера.</p>
            </div>
        </body>
        </html>
        """.format(
            time=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            port=PORT,
            github_status="✅ Включено" if GITHUB_TOKEN else "❌ Выключено (нет GITHUB_TOKEN)"
        )

        self.wfile.write(html.encode('utf-8'))

    def _process_webhook(self, payload):
        event_type = self.headers.get('X-GitHub-Event', 'unknown')
        repo_name = payload.get('repository', {}).get('full_name', 'unknown')
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\n🔔 Получено webhook событие:")
        print(f"   Время: {timestamp}")
        print(f"   Тип события: {event_type}")
        print(f"   Репозиторий: {repo_name}")

        if event_type == 'push':
            self._handle_push_event(payload)
        elif event_type == 'pull_request':
            self._handle_pr_event(payload)
        elif event_type == 'release':
            self._handle_release_event(payload)
        else:
            print(f"   ℹ️  Событие '{event_type}' - базовое логирование")

    def _update_github_status(self, payload, state, description, context="ci/catty-reminders"):
        """Обновляет статус коммита в GitHub"""
        if not GITHUB_TOKEN:
            return

        try:
            repo_full_name = payload.get('repository', {}).get('full_name')
            commit_sha = payload.get('after') or payload.get('pull_request', {}).get('head', {}).get('sha')
            
            if not repo_full_name or not commit_sha:
                return

            url = f"https://api.github.com/repos/{repo_full_name}/statuses/{commit_sha}"
            
            headers = {
                'Authorization': f'token {GITHUB_TOKEN}',
                'Accept': 'application/vnd.github.v3+json'
            }
            
            data = {
                "state": state,
                "target_url": f"http://app.{APP_ID}.{PROXY_DOMAIN}:8080",
                "description": description,
                "context": context
            }
            
            response = requests.post(url, headers=headers, json=data)
            if response.status_code == 201:
                print(f"   📊 GitHub Status: {state} - {description}")
            else:
                print(f"   ❌ Ошибка обновления статуса: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Ошибка отправки статуса в GitHub: {e}")

    def _handle_push_event(self, payload):
        commits = payload.get('commits', [])
        branch = payload.get('ref', '').replace('refs/heads/', '')
        pusher = payload.get('pusher', {}).get('name', 'unknown')
        clone_url = payload.get('repository', {}).get('clone_url', 'unknown')

        print(f"   📝 Push в ветку: {branch}")
        print(f"   👤 Автор: {pusher}")
        print(f"   📊 Коммитов: {len(commits)}")

        # Обновляем статус в GitHub - начали обработку
        self._update_github_status(payload, "pending", "Запуск автоматизации...")

        print(f"   🚀 ЗАПУСКАЕМ АВТОМАТИЗАЦИЮ:")
        
        working_dir = "/home/v1k70r/tmp/catty-reminders-app"
        
        try:
            if not os.path.exists(working_dir):
                print(f"      ❌ Рабочая директория не найдена: {working_dir}")
                self._update_github_status(payload, "error", "Рабочая директория не найдена")
                return

            print(f"      Рабочая директория: {working_dir}")

            print(f"      - Получение изменений из ветки {branch}...")
            pull_result = subprocess.run(
                ["git", "pull", "origin", branch],
                cwd=working_dir,
                capture_output=True,
                text=True
            )
            
            if pull_result.returncode == 0:
                print(f"      ✅ Изменения получены успешно!")
                if pull_result.stdout.strip():
                    print(f"         {pull_result.stdout.strip()}")
            else:
                print(f"      ❌ Ошибка при получении изменений!")
                print(f"         {pull_result.stderr if pull_result.stderr else pull_result.stdout}")
                self._update_github_status(payload, "error", "Ошибка при получении изменений")
                return

            # Обновляем статус - запускаем тесты
            self._update_github_status(payload, "pending", "Запуск тестов...")

            print(f"      - Запуск тестов на обновленном коде...")
            test_result = subprocess.run(
                ["./test.sh"],
                cwd=working_dir,
                capture_output=True,
                text=True
            )
            
            if test_result.returncode == 0:
                print(f"      ✅ Тесты прошли успешно!")
                if test_result.stdout.strip():
                    print(f"         {test_result.stdout.strip()}")
                
                # Обновляем статус - тесты прошли, запускаем деплой
                self._update_github_status(payload, "pending", "Запуск деплоя...")

                print(f"      - Запуск деплоя...")
                deploy_result = subprocess.run(
                    ["./deploy.sh"],
                    cwd=os.getcwd(),
                    capture_output=True,
                    text=True
                )
                
                if deploy_result.returncode == 0:
                    print(f"      ✅ Деплой завершен успешно!")
                    if deploy_result.stdout.strip():
                        print(f"         {deploy_result.stdout.strip()}")
                    
                    # Финальный успешный статус
                    self._update_github_status(payload, "success", "Автоматизация завершена успешно")
                    
                    print(f"   🎉 Автоматизация завершена!")
                    print(f"   🌐 Приложение доступно по: http://app.$ID.$PROXY:8181")
                    
                else:
                    print(f"      ❌ Ошибка деплоя!")
                    print(f"         {deploy_result.stderr if deploy_result.stderr else deploy_result.stdout}")
                    self._update_github_status(payload, "failure", "Ошибка деплоя")
                    return

            else:
                print(f"      ❌ Тесты упали! Деплой отменен.")
                print(f"         {test_result.stderr if test_result.stderr else test_result.stdout}")
                self._update_github_status(payload, "failure", "Тесты не прошли")
                print(f"   🚫 Pull отклонен из-за неудачных тестов")

        except Exception as e:
            print(f"      ❌ Неожиданная ошибка: {e}")
            self._update_github_status(payload, "error", f"Неожиданная ошибка: {e}")

    def _handle_pr_event(self, payload):
        action = payload.get('action', '')
        pr_number = payload.get('pull_request', {}).get('number', '')
        title = payload.get('pull_request', {}).get('title', '')

        print(f"   🔀 Pull Request #{pr_number}: {action}")
        print(f"   📋 Заголовок: {title}")

    def _handle_release_event(self, payload):
        action = payload.get('action', '')
        tag_name = payload.get('release', {}).get('tag_name', '')

        print(f"   🏷️  Release {tag_name}: {action}")

def main():
    print(f"🚀 Запуск DevOps Webhook Demo Server")
    print(f"📡 Порт: {PORT}")
    print(f"🌐 URL: http://0.0.0.0:{PORT}")
    print(f"🔧 Webhook URL: http://0.0.0.0:{PORT}/webhook")
    print(f"⏰ Время запуска: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if GITHUB_TOKEN:
        print(f"🔗 GitHub Status: ✅ Включено")
    else:
        print(f"🔗 GitHub Status: ❌ Выключено (установи GITHUB_TOKEN для обратной связи)")
    
    print(f"\n👀 Ожидание webhook событий от GitHub...")
    print(f"💡 Для остановки: Ctrl+C\n")

    try:
        server = HTTPServer(('0.0.0.0', PORT), WebhookHandler)
        server.serve_forever()
    except KeyboardInterrupt:
        print(f"\n🛑 Сервер остановлен")

if __name__ == '__main__':
    main()