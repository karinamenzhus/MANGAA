import os
import re
import socket
from flask import Flask, send_from_directory, request, jsonify

app = Flask(__name__)

# ====================================================================
# ВАШ КОРНЕВОЙ ПУТЬ:
MANGA_DIR = r"E:\Manga" 
# ====================================================================

HISTORY_FILE = "read_history.txt"

def get_last_read():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
            if len(lines) >= 3:
                return lines, lines, lines  # title, chapter_folder, scroll
    return None, None, "0"

def save_last_read(title, chapter_folder, scroll_pos):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        f.write(f"{title}\n{chapter_folder}\n{scroll_pos}")

def extract_numbers(folder_name):
    """Вытаскивает из названия папки номера тома и главы для идеальной сортировки"""
    vol_match = re.search(r'Том\s*(\d+)', folder_name, re.IGNORECASE)
    ch_match = re.search(r'Глава\s*(\d+)', folder_name, re.IGNORECASE)
    
    vol_num = int(vol_match.group(1)) if vol_match else 0
    ch_num = int(ch_match.group(1)) if ch_match else 0
    return vol_num, ch_num

def sort_chapters(chapters_list):
    """Сортирует сначала по томам, а затем внутри тома по главам"""
    return sorted(chapters_list, key=lambda x: (extract_numbers(x), [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', x)]))

def natural_sort_key(s):
    """Сортировка картинок внутри главы"""
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

def get_local_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

BASE_STYLE = """
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
    body { background: #121212; color: #fff; font-family: sans-serif; text-align: center; padding: 20px; margin: 0; }
    .container { max-width: 600px; margin: 0 auto; padding: 10px; }
    h1 { font-size: 24px; margin-bottom: 5px; color: #fff; }
    .ip-info { color: #888; font-size: 14px; margin-bottom: 25px; background: #1e1e1e; padding: 8px; border-radius: 5px; display: inline-block; }
    .resume-box { background: #1a2a1a; padding: 15px; border-radius: 8px; margin-bottom: 25px; border: 1px solid #28a745; text-align: center; }
    .resume-btn { display: inline-block; background: #28a745; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 10px; }
    .list-box { text-align: left; background: #1a1a1a; padding: 10px; border-radius: 8px; }
    .item-link { color: #1e90ff; display: block; padding: 14px 10px; font-size: 18px; text-decoration: none; border-bottom: 1px solid #2a2a2a; }
    .item-link:last-child { border-bottom: none; }
    .item-link:hover { background: #222; text-decoration: underline; }
    .back-btn { display: block; text-align: left; color: #aaa; text-decoration: none; margin-bottom: 15px; font-size: 15px; }
    .manga-img { max-width: 800px; width: 100%; display: block; height: auto; margin: 0 auto; background: #222; }
    .nav-container { width: 100%; max-width: 800px; display: flex; justify-content: space-between; padding: 5px 0; background: #111; box-sizing: border-box; }
    .nav-btn { display: inline-block; padding: 12px 20px; background: #007bff; color: white; text-decoration: none; font-size: 16px; border-radius: 5px; font-weight: bold; margin: 10px; }
</style>
"""

@app.route('/')
def index():
    if not os.path.exists(MANGA_DIR): return f"<h1>Папка '{MANGA_DIR}' не найдена!</h1>", 404
    titles = sorted([d for d in os.listdir(MANGA_DIR) if os.path.isdir(os.path.join(MANGA_DIR, d))], key=str.lower)
    l_title, l_chapter_folder, _ = get_last_read()
    
    res_box = ""
    if l_title and l_title in titles and l_chapter_folder:
        res_box = f'<div class="resume-box"><div style="color: #aaa;">Вы остановились на:</div><div style="font-weight:bold;color:#28a745;margin:5px 0;">{l_title} — {l_chapter_folder}</div><a href="/manga/{l_title}/{l_chapter_folder}?resume=1" class="resume-btn">Продолжить чтение</a></div>'
        
    links = "".join([f'<a class="item-link" href="/manga/{t}">📁 {t}</a>' for t in titles])
    return f'<html><head>{BASE_STYLE}</head><body><div class="container"><h1>📚 Моя Библиотека</h1><div class="ip-info">📱 Ссылка для телефона: <b>http://{get_local_ip()}:5000</b></div>{res_box}<div class="list-box"><div style="padding:10px;color:#888;">Ваши Тайтлы:</div>{links}</div></div></body></html>'

@app.route('/manga/<title_name>')
def view_title(title_name):
    t_path = os.path.join(MANGA_DIR, title_name)
    if not os.path.exists(t_path): return "Тайтл не найден", 404
    
    # Сканируем папки глав прямо внутри тайтла и упорядочиваем их
    raw_chapters = [d for d in os.listdir(t_path) if os.path.isdir(os.path.join(t_path, d))]
    chapters = sort_chapters(raw_chapters)
    
    links = "".join([f'<a class="item-link" href="/manga/{title_name}/{c}">📖 {c}</a>' for c in chapters])
    return f'<html><head>{BASE_STYLE}</head><body><div class="container"><a href="/" class="back-btn">⬅ Назад в библиотеку</a><h1>{title_name}</h1><div class="list-box"><div style="padding:10px;color:#888;">Список глав (упорядочен):</div>{links}</div></div></body></html>'

@app.route('/manga/<title_name>/<chapter_name>')
def view_chapter(title_name, chapter_name):
    c_path = os.path.join(MANGA_DIR, title_name, chapter_name)
    if not os.path.exists(c_path): return "Глава не найдена", 404
    
    images = sorted([f for f in os.listdir(c_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.webp'))], key=natural_sort_key)
    
    t_path = os.path.join(MANGA_DIR, title_name)
    raw_chapters = [d for d in os.listdir(t_path) if os.path.isdir(os.path.join(t_path, d))]
    all_ch = sort_chapters(raw_chapters)
    
    c_idx = all_ch.index(chapter_name)
    next_ch = all_ch[c_idx + 1] if c_idx + 1 < len(all_ch) else None
    
    _, _, saved_scroll = get_last_read()
    target_scroll = saved_scroll if request.args.get('resume', '0') == '1' else '0'
    
    next_btn = f'<a href="/manga/{title_name}/{next_ch}" class="nav-btn" style="padding:18px 35px;background:#007bff;color:white;text-decoration:none;border-radius:5px;font-weight:bold;">Читать следующую главу ➔</a>' if next_ch else '<p style="color:gray;">🎉 Вы прочитали все доступные главы!</p>'
    top_next = f'<a href="/manga/{title_name}/{next_ch}" class="nav-btn">След. Глава ➔</a>' if next_ch else ''
    img_tags = "".join([f'<img class="manga-img" src="/images/{title_name}/{chapter_name}/{i}">' for i in images])
    
    return f'<html><head>{BASE_STYLE}<script>setInterval(function(){{fetch("/save_position",{{method:"POST",headers:{{"Content-Type":"application/json"}},body:JSON.stringify({{title:"{title_name}",chapter:"{chapter_name}",scroll:window.scrollY||window.pageYOffset}})}});}},2000);window.onload=function(){{let t=parseInt("{target_scroll}");if(t>0)setTimeout(()=>{{window.scrollTo(0,t);}},150);}};</script></head><body><div style="width:100%;max-width:800px;display:flex;justify-content:space-between;background:#111;"><a href="/manga/{title_name}" class="nav-btn" style="background:#444;color:white;text-decoration:none;border-radius:5px;padding:12px 20px;">🗂 К главама</a>{top_next}</div><div>{img_tags if images else "<p style='color:gray;padding:50px;'>В этой папке нет картинок</p>"}</div><div style="margin:30px 0 50px 0;">{next_btn}</div></body></html>'

@app.route('/save_position', methods=['POST'])
def save_position():
    data = request.get_json()
    save_last_read(data['title'], data['chapter'], data['scroll'])
    return jsonify({"status": "success"})

@app.route('/images/<title_name>/<chapter_name>/<filename>')
def get_image(title_name, chapter_name, filename):
    return send_from_directory(os.path.join(MANGA_DIR, title_name, chapter_name), filename)

if __name__ == '__main__':
    local_ip = get_local_ip()
    print(f"\n 🚀 СЕРВЕР ЗАПУЩЕН ПОД ВАШУ СТРУКТУРУ!\n Читать тут: http://localhost:5000\n Телефон:    http://{local_ip}:5000\n")
    app.run(host='0.0.0.0', port=5000, debug=False)