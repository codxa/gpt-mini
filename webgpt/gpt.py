from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
import datetime
import tiktoken
import time
import os

# .env dosyasını yükle
load_dotenv()

app = Flask(__name__)

# GPT modelini ayarla
model = ChatOpenAI(model="gpt-4")

# Konu listesi (yalnızca savunma / farkındalık odaklı içerikler)
topics = {
    "Nmap": {
        "explanation": (
            "Nmap, ağ keşfi ve güvenlik taraması için kullanılan popüler bir araçtır.\n"
            "Burada size Python'da Nmap taraması yapmayı sağlayan basit bir örnek vereceğim.\n"
            "Bu örnek, sadece izin verilen ağlarda kullanılmalı, yetkisiz taramalar yasa dışıdır."
        ),
        "code": '''\
# Python'da Nmap modülü ile basit tarama örneği
import nmap

nm = nmap.PortScanner()

# Belirtilen IP'yi tarar
nm.scan('127.0.0.1', '22-80')

for host in nm.all_hosts():
    print(f'Host : {host} ({nm[host].hostname()})')
    print(f'State : {nm[host].state()}')
    for proto in nm[host].all_protocols():
        print('----------')
        print(f'Protocol : {proto}')

        lport = nm[host][proto].keys()
        for port in lport:
            print(f'Port : {port}\tState : {nm[host][proto][port]["state"]}')
''',
        "warning": (
            "\nUYARI: Bu kod, sadece izin verilen sistemlerde kullanılmalıdır. "
            "Yetkisiz taramalar yasa dışıdır ve cezai sorumluluk doğurur."
        )
    },

    "OWASP": {
        "explanation": (
            "OWASP, web uygulama güvenliği için en önemli kaynaklardan biridir.\n"
            "Burada, OWASP top 10 güvenlik açıklarından biri olan SQL Injection'a karşı basit bir koruma örneği verilmektedir."
        ),
        "code": '''\
# Basit SQL Injection önleme örneği (Python + SQLite)
import sqlite3

conn = sqlite3.connect(':memory:')
c = conn.cursor()
c.execute('CREATE TABLE users (username TEXT, password TEXT)')

# Parametreli sorgu kullanarak SQL Injection önlenir
def get_user(username):
    c.execute('SELECT * FROM users WHERE username = ?', (username,))
    return c.fetchone()

# Kullanıcı ekleme
c.execute('INSERT INTO users VALUES (?, ?)', ('admin', 'sifre123'))
conn.commit()

print(get_user('admin'))
''',
        "warning": (
            "\nUYARI: Kod örnekleri eğitim amaçlıdır. Gerçek uygulamalarda gelişmiş güvenlik önlemleri alınmalıdır."
        )
    },

    "Phishing": {
        "explanation": (
            "Phishing (Oltalama) saldırıları, kullanıcıları kandırarak kişisel bilgilerini ele geçirmeye çalışır.\n"
            "Burada, şüpheli e-posta içeriklerini tespit etmek için basit bir Python örneği verilmektedir."
        ),
        "code": '''\
# Basit phishing e-posta tespit örneği
def detect_phishing(email_content):
    suspicious_keywords = ['password', 'verify', 'urgent', 'bank', 'login']
    email_content_lower = email_content.lower()
    for word in suspicious_keywords:
        if word in email_content_lower:
            return True
    return False

sample_email = "Please verify your bank account login immediately!"
print("Phishing detected!" if detect_phishing(sample_email) else "Email clean.")
''',
        "warning": (
            "\nUYARI: Bu basit örnek sadece eğitim amaçlıdır. Gerçek phishing tespiti çok daha karmaşıktır."
        )
    },

    "Malware Analysis": {
        "explanation": (
            "Malware analizi, zararlı yazılımları inceleyip etkilerini anlamayı sağlar.\n"
            "Burada, basit bir dosya hash hesaplama örneği verilmektedir."
        ),
        "code": '''\
import hashlib

def get_file_hash(filename):
    with open(filename, 'rb') as f:
        data = f.read()
        return hashlib.sha256(data).hexdigest()

# Örnek kullanım:
# print(get_file_hash('suspect_file.exe'))
''',
        "warning": (
            "\nUYARI: Malware analizi karmaşık ve riskli bir alandır. Bu örnek basit bir araçtır."
        )
    },

    "Wi-Fi Security": {
        "explanation": (
            "Wi-Fi güvenliği, kablosuz ağların korunmasını sağlar.\n"
            "Basit bir Wi-Fi sinyal gücü ölçme örneği (Windows için) verilmektedir."
        ),
        "code": '''\
# Windows ortamında Wi-Fi sinyal gücü ölçümü
import subprocess

def get_wifi_signal():
    result = subprocess.run(['netsh', 'wlan', 'show', 'interfaces'], capture_output=True, text=True)
    for line in result.stdout.split('\\n'):
        if 'Signal' in line:
            print(line.strip())

get_wifi_signal()
''',
        "warning": (
            "\nUYARI: Bu kod sadece Windows için geçerlidir."
        )
    },

    "Social Engineering": {
        "explanation": (
            "Sosyal mühendislik, insanları manipüle ederek bilgi sızdırma yöntemidir.\n"
            "Burada basit bir sosyal mühendislik senaryosu ve nasıl fark edilir anlatılmaktadır."
        ),
        "code": '''\
# Basit sosyal mühendislik senaryosu
def recognize_social_engineering(message):
    red_flags = ['password', 'urgent', 'help me', 'click link', 'confidential']
    message_lower = message.lower()
    for flag in red_flags:
        if flag in message_lower:
            return True
    return False

sample_msg = "Can you urgently send me your password?"
print("Possible social engineering attempt detected!" if recognize_social_engineering(sample_msg) else "Message seems safe.")
''',
        "warning": (
            "\nUYARI: Sosyal mühendislik tespiti zor ve karmaşıktır, bu örnek sadece başlangıçtır."
        )
    },

    "Encryption": {
        "explanation": (
            "Şifreleme, verilerin gizliliğini ve bütünlüğünü korur.\n"
            "Burada basit AES simetrik şifreleme/deşifreleme örneği verilmektedir."
        ),
        "code": '''\
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes

key = get_random_bytes(16)
data = b'Sifrelenmesi gereken veri'

cipher = AES.new(key, AES.MODE_CBC)
ct_bytes = cipher.encrypt(pad(data, AES.block_size))
iv = cipher.iv

print("Şifreli:", ct_bytes.hex())

cipher_dec = AES.new(key, AES.MODE_CBC, iv)
pt = unpad(cipher_dec.decrypt(ct_bytes), AES.block_size)
print("Çözülmüş:", pt.decode())
''',
        "warning": (
            "\nUYARI: Şifreleme karmaşık bir alandır, bu örnek temel bir uygulamadır."
        )
    },

    "Vulnerability Scanners": {
        "explanation": (
            "Zafiyet tarayıcıları sistemlerde bilinen güvenlik açıklarını bulur.\n"
            "Burada Nikto kullanımına dair örnek verilmiştir."
        ),
        "code": '''\
# Nikto basit komut satırı çağrısı (Python subprocess ile)
import subprocess

def run_nikto(target_url):
    result = subprocess.run(['nikto', '-h', target_url], capture_output=True, text=True)
    print(result.stdout)

# Örnek:
# run_nikto('http://example.com')
''',
        "warning": (
            "\nUYARI: Nikto gibi araçlar yalnızca izinli sistemlerde kullanılmalıdır."
        )
    },
}
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Chat geçmişi
history_messages = []

def count_tokens(text, model_name="gpt-4"):
    encoding = tiktoken.encoding_for_model(model_name)
    return len(encoding.encode(text))

def log_to_file_with_cost(user_input, gpt_reply, prompt_tokens, completion_tokens):
    cost = (prompt_tokens / 1000) * 0.03 + (completion_tokens / 1000) * 0.06
    with open("chat_log.txt", "a", encoding="utf-8") as f:
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        f.write(f"[{timestamp}] Kullanıcı: {user_input}\n")
        f.write(f"[{timestamp}] Yanıt: {gpt_reply}\n")
        f.write(f"[{timestamp}] Token: {prompt_tokens + completion_tokens} (Prompt: {prompt_tokens}, Cevap: {completion_tokens})\n")
        f.write(f"[{timestamp}] Ücret: ${cost:.4f}\n\n")

@app.route("/")
def index():
    return render_template("index.html", topics=list(topics.keys()))

@app.route("/send_message", methods=["POST"])
def send_message():
    data = request.get_json()
    user_input = data.get("message", "")
    system_prompt = "Sen yasal sınırlar içinde hareket eden, dobra ve teknik bir siber güvenlik eğitmenisin."

    chat_history = [SystemMessage(content=system_prompt), *history_messages, HumanMessage(content=user_input)]

    try:
        response = model.invoke(chat_history)
        reply = response.content

        # Token hesaplama
        prompt_tokens = count_tokens(system_prompt) + count_tokens(user_input)
        completion_tokens = count_tokens(reply)
        log_to_file_with_cost(user_input, reply, prompt_tokens, completion_tokens)

        # Geçmişe ekle
        history_messages.append(HumanMessage(content=user_input))
        history_messages.append(SystemMessage(content=reply))

        return jsonify({"reply": reply})

    except Exception as e:
        return jsonify({"reply": f"Hata: {str(e)}"})

@app.route("/get_topic", methods=["POST"])
def get_topic():
    data = request.get_json()
    topic = data.get("topic", "")
    if topic in topics:
        t = topics[topic]
        content = f"{t['explanation']}\n\nKod Örneği:\n{t['code']}\n{t['warning']}"

        # Geçmişe ekle ki "yukarıdaki kod" dendiğinde hatırlasın
        history_messages.append(HumanMessage(content=f"{topic} konusunu getir"))
        history_messages.append(SystemMessage(content=content))

        return jsonify({
            "explanation": t["explanation"],
            "code": t["code"],
            "warning": t["warning"]
        })
    else:
        return jsonify({"error": "Bu konuda bilgi yok."})


@app.route("/upload", methods=["POST"])
def upload_file():
    if "file" not in request.files:
        return {"error": "Dosya bulunamadı"}, 400

    file = request.files["file"]
    if file.filename == "":
        return {"error": "Dosya seçilmedi"}, 400

    save_path = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(save_path)

    content = ""
    if file.filename.endswith((".txt", ".html", ".md", ".py", ".js", ".css")):
        with open(save_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

    # Dosya içeriğini de geçmişe ekle
    if content:
        history_messages.append(HumanMessage(content=f"{file.filename} dosyası yüklendi."))
        history_messages.append(SystemMessage(content=content[:1000]))

    return {
        "filename": file.filename,
        "content": content[:2000]
    }


if __name__ == "__main__":
    app.run(debug=True)
