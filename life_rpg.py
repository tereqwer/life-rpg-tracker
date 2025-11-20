import json
import os, sys
import winsound
import math
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
from datetime import date
import time, datetime
import tkinter.font as tkfont
import uuid
import pyperclip

TASK_TEMPLATES = {
    "language": [
        {
            "label": "Подивитись урок (20 хв)",
            "name": "Урок англійської 20 хв",
            "category": "short",
            "xp_reward": 50,
            "target_value": 20
        },
        {
            "label": "10 хв shadowing",
            "name": "Shadowing 10 хв",
            "category": "short",
            "xp_reward": 60,
            "target_value": 10
        },
        {
            "label": "Повторити 20 слів",
            "name": "20 нових/повторити слова",
            "category": "short",
            "xp_reward": 50,
            "target_value": 20
        },
        {
            "label": "Абзац щоденника",
            "name": "Абзац щоденника англійською",
            "category": "short",
            "xp_reward": 40,
            "target_value": 1
        },
        {
            "label": "15 хв читання",
            "name": "Читання 15 хв",
            "category": "short",
            "xp_reward": 50,
            "target_value": 15
        },
        {
            "label": "5 хв говоріння",
            "name": "5 хв говоріння англійською",
            "category": "short",
            "xp_reward": 50,
            "target_value": 5
        }
    ],
    "default": [
        {
            "label": "Фокус 25 хв (Pomodoro)",
            "name": "Фокус-сесія 25 хв",
            "category": "short",
            "xp_reward": 50,
            "target_value": 25
        },
        {
            "label": "Міні-проєкт (1 день)",
            "name": "Міні-проєкт на 1 день",
            "category": "medium",
            "xp_reward": 120,
            "target_value": 1
        }
    ]
}


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LEVEL_UP_SOUND_PATH = os.path.join(BASE_DIR, "lvlup.wav")


if getattr(sys, "frozen", False):
    BASE_DIR = os.path.dirname(sys.executable)      # коли запаковано в .exe
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # звичайний .py

LEVEL_UP_SOUND_PATH = os.path.join(BASE_DIR, "lvlup.wav")
DATA_PATH = os.path.join(BASE_DIR, "data.json")
AVATAR_PATH = os.path.join(BASE_DIR, "avatar.jpg")

DATA_FILE = "data.json"

DEFAULT_SKILLS = [
    {"id": "english", "name": "Англійська"},
    {"id": "french", "name": "Французька"},
    {"id": "x_growth", "name": "X (Twitter) розвиток"},
    {"id": "youtube", "name": "YouTube канал"},
    {"id": "sport", "name": "Спорт"},
    {"id": "programming", "name": "Програмування"},
]


# ---------- Логіка XP / рівнів ----------

def xp_to_level(xp: float) -> int:
    """Обчислюємо рівень за XP. Формула: XP ≈ 120 * level^1.6"""
    if xp <= 0:
        return 0
    level = int((xp / 120.0) ** (1.0 / 1.6))
    return min(level, 40)  # обмеження до 40-го рівня

def title_for_level(level: int) -> str:
    """Титул за рівнем навички."""
    if level < 1:
        return "Новачок"
    if level <= 5:
        return "Новачок"
    if level <= 10:
        return "Учень"
    if level <= 15:
        return "Практик"
    if level <= 20:
        return "Просунутий"
    if level <= 25:
        return "Експерт"
    if level <= 30:
        return "Майстер"
    if level <= 35:
        return "Грандмайстер"
    return "Легенда"

def color_for_level(level: int) -> str:
    """Повертає колір тексту для рівня."""
    if level <= 0:
        return "#9ca3af"  # сірий
    if level <= 5:
        return "#22c55e"  # зелений
    if level <= 10:
        return "#3b82f6"  # синій
    if level <= 15:
        return "#a855f7"  # фіолетовий
    if level <= 20:
        return "#eab308"  # жовто-золотий
    if level <= 30:
        return "#f97316"  # помаранчевий
    return "#ef4444"      # червоний для легенд

def level_to_xp(level: int) -> float:
    """Скільки XP треба для певного рівня (сукупний поріг)."""
    if level <= 0:
        return 0.0
    return 120.0 * (level ** 1.6)

def cefr_from_level(level: int) -> str:
    """Грубе наближення CEFR за рівнем навички (тільки для мов)."""
    if level <= 0:
        return "A0"
    if level <= 5:
        return "A1"
    if level <= 10:
        return "A2"
    if level <= 15:
        return "B1"
    if level <= 20:
        return "B2"
    if level <= 30:
        return "C1"
    return "C2"



# ---------- Робота з data.json ----------

def create_default_data() -> dict:
    """Початковий стан, якщо data.json ще немає."""
    skills = []
    for s in DEFAULT_SKILLS:
        # для англійської та французької робимо тип "language"
        if s["id"] in ("english", "french"):
            skill_type = "language"
            cefr_value = "A0"
        else:
            skill_type = "general"
            cefr_value = ""

        skills.append({
            "id": s["id"],
            "name": s["name"],
            "type": skill_type,
            "xp": 0,
            "daily_done": False,
            "tasks": [],
            "cefr": cefr_value   
        })


    data = {
        "hero": {
            "name": "Pasha",
            "xp_total": 0,         # можна потім не зберігати
            "money_usdt": 1350.0,     # баланс у USDT
            "money_uah": 11590.0,       # баланс у hrn
            "hp_current": 100,     # поточне HP
            "hp_max": 100,         # максимум HP
            "avatar_path": "avatar.jpg"      # шлях до картинки героя (png/jpg)
        },
        "skills": skills,
        "global_tasks": [],
        "last_daily_reset": None
    }

    return data


def load_data() -> dict:
    """Завантажити стан з файлу або створити за замовчуванням."""
    if not os.path.exists(DATA_FILE):
        data = create_default_data()
        save_data(data)
        return data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        # Якщо файл битий — починаємо з нуля
        data = create_default_data()
        save_data(data)

    # Мінімальна перевірка
    if "hero" not in data or "skills" not in data:
        data = create_default_data()
        save_data(data)

    # ---- ДОБАВЛЯЄМО CEFР, ЯКЩО НЕМА ----
    for skill in data.get("skills", []):
        if "cefr" not in skill:
            if skill.get("type") == "language":
                skill["cefr"] = "A0"
            else:
                skill["cefr"] = ""
    save_data(data)
    return data



def save_data(data: dict) -> None:
    """Зберегти стан у data.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- Клас застосунку ----------

class App:
    def __init__(self, root: ctk.CTk):
        self.hero_image = None  # щоб картинку не зʼїв GC
        self.root = root
        self.root.geometry("1200x980")

        self.hero_image = None

        self.data = load_data()
        self.ensure_daily_reset()

        self.build_main_screen()


        self.hero_image = None  # для аватарки

        # Завантажуємо дані
        self.data = load_data()
        # Перевіряємо, чи новий день — якщо так, скидаємо daily_done
        self.ensure_daily_reset()
        # Побудова головного екрану
        self.build_main_screen()

    def show_xp_gain_animation(self, skill_id: str, skill: dict, xp_gained: int, old_xp: float, new_xp: float, old_lvl: int, new_lvl: int):
        """Плаваючий попап з анімацією XP та мотиваційним повідомленням."""
        # --- 1. Створення вікна ---
        win = ctk.CTkToplevel(self.root)
        win.title("XP Gained!")
        win.attributes("-topmost", True)
        win.geometry("500x300")
        win.transient(self.root) # Зробить його залежним від головного вікна

        win_width = 500
        win_height = 300
        # Розміщуємо по центру екрану
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (win_width // 2)
        y = (screen_height // 2) - (win_height // 2)
        win.geometry(f"{win_width}x{win_height}+{x}+{y}")
        
        frame = ctk.CTkFrame(win, corner_radius=15)
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        # --- 2. Текст та повідомлення ---
        ctk.CTkLabel(
            frame,
            text=f"Навичка: {skill.get('name')}",
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            frame,
            text=f"+{xp_gained} XP",
            font=("Segoe UI", 18, "bold"),
            text_color="#eab308"
        ).pack(pady=(0, 8))
        
        # --- 3. Розрахунок прогресу для анімації ---
        
        # Визначаємо XP-поріг поточного та наступного рівня
        current_level_xp_threshold = level_to_xp(old_lvl)
        next_level_xp_threshold = level_to_xp(old_lvl + 1)
        
        # Якщо вже був максимальний рівень або поточний рівень > нового, анімація не потрібна
        if old_lvl >= 40 or next_level_xp_threshold <= current_level_xp_threshold:
            start_progress = 1.0
            end_progress = 1.0
            
            progress_msg = "Майстер! Максимальний XP."
            progress_bar = ctk.CTkProgressBar(frame, height=12)
            progress_bar.set(1.0) # Вже повний
        else:
            # Визначаємо початковий та кінцевий прогрес для анімації
            # Початковий прогрес (до додавання XP)
            start_progress = (old_xp - current_level_xp_threshold) / (next_level_xp_threshold - current_level_xp_threshold)
            start_progress = max(0.0, min(1.0, start_progress))
            
            # Кінцевий прогрес (з доданим XP). Якщо XP виходить за рівень, обмежуємо 1.0
            end_progress = (new_xp - current_level_xp_threshold) / (next_level_xp_threshold - current_level_xp_threshold)
            end_progress = min(1.0, end_progress)

            progress_msg = f"Рівень: {old_lvl} ➜ {new_lvl}"
            
            progress_bar = ctk.CTkProgressBar(frame, height=12)
            progress_bar.set(start_progress) # Починаємо з поточного XP
            progress_bar.pack(fill="x", padx=10, pady=(0, 8))

        progress_bar.pack(fill="x", padx=10, pady=(0, 8))

        # --- НОВЕ: ДЕТАЛІЗАЦІЯ XP ---
        
        current_total_xp = int(new_xp)
        
        # Розраховуємо XP до наступного рівня
        if new_lvl >= 40: # Якщо досягнуто макс. рівня
             xp_text = f"Загальний XP: {current_total_xp} / Макс. рівень! 🚀"
             xp_color = "#eab308"
        else:
             next_level_xp_needed = level_to_xp(new_lvl + 1)
             xp_remaining = next_level_xp_needed - new_xp
             
             # Формат: Поточний XP / XP для наступного рівня (Рівень X)
             xp_text = f"XP зараз: {current_total_xp} / До {new_lvl + 1} ще {int(xp_remaining)} XP"
             xp_color = "#99f6e4" # Світлий колір для контрасту
             
        ctk.CTkLabel(
            frame,
            text=xp_text,
            font=("Segoe UI", 11, "bold"),
            text_color=xp_color
        ).pack(pady=(4, 0))

        # ... (Код animate_bar та виклик animate_bar(0) залишаються без змін)
        
        # Мотиваційне повідомлення
        motivational_label = ctk.CTkLabel(
            frame,
            text="Молодець! Продовжуй в тому ж дусі! 💪",
            font=("Segoe UI", 12),
            text_color="#22c55e" 
        )
        motivational_label.pack(pady=(4, 0))

        btn_ok = ctk.CTkButton(
                    win, 
                    text="Зрозуміло", 
                    # При натисканні: викликаємо функцію, яка оновить екран і закриє вікно
                    command=lambda: on_ok_clicked(skill_id), 
                    width=100
                )
        btn_ok.pack(pady=(10, 15))

        def on_ok_clicked(skill_id_to_update):
            """Викликається кнопкою "ОК". Оновлює екран та закриває вікно анімації."""
            
            # Оновлюємо екрани тут, коли користувач готовий
            self.build_main_screen() 
            self.build_skill_screen(skill_id_to_update) 
            
            # Закриваємо вікно (win має бути доступний у цій локальній області видимості)
            win.destroy()

            
            
        # --- 4. Логіка анімації ---
        ANIMATION_STEPS = 50 
        ANIMATION_DURATION_MS = 1000 # 1 секунда
        step_delay = ANIMATION_DURATION_MS // ANIMATION_STEPS
        
        def animate_bar(step):
            if not win.winfo_exists(): # ДОДАТИ ЦЮ ПЕРЕВІРКУ
                return
            if step < ANIMATION_STEPS:
                current_progress = start_progress + (end_progress - start_progress) * (step / ANIMATION_STEPS)
                progress_bar.set(current_progress)
                win.after(step_delay, lambda: animate_bar(step + 1))
            else:
                
                progress_bar.set(end_progress)
            


        # Стартуємо анімацію
        animate_bar(0)

    def copy_to_clipboard(self, text_to_copy: str):
        """Копіює вказаний текст у буфер обміну та показує повідомлення."""
        try:
            pyperclip.copy(text_to_copy)
            # Можна використати тимчасовий CTkLabel у вікні або messagebox, але messagebox простіше:
            messagebox.showinfo("Скопійовано", f"ID скопійовано: {text_to_copy}")
        except pyperclip.PyperclipException:
            messagebox.showerror("Помилка", "Не вдалося отримати доступ до буфера обміну.")
        except Exception as e:
            print(f"Помилка копіювання: {e}")

    def _create_subtask_checklist(self, parent_frame, skill_id: str, parent_task: dict):
        """Рендерить неактивний список підзадач під батьківською задачею."""
        
        subtask_ids = parent_task.get("required_subtasks_ids", [])
        if not subtask_ids:
            return

        # Збираємо всі активні задачі навички для швидкого пошуку
        all_tasks = {t['id']: t for t in next((s for s in self.data.get('skills', []) if s.get('id') == skill_id), {}).get('tasks', [])}

        # Фрейм для списку підзадач (з відступом для візуального підпорядкування)
        list_frame = ctk.CTkFrame(parent_frame, fg_color="transparent")
        list_frame.pack(fill="x", padx=(20, 0), pady=(4, 0)) 
        
        # Відображення кожної підзадачі
        for sub_id in subtask_ids:
            sub_task = all_tasks.get(sub_id)
            if not sub_task:
                continue # Пропускаємо, якщо задача з цим ID не знайдена

            is_completed = sub_task.get("completed", False)
            
            # Визначаємо стиль: сірий колір та закреслення
            text_color = "#6b7280" # Темно-сірий колір
            
            # Створюємо кастомний шрифт для закреслення
            if is_completed:
                text_color = "#6b7280"
                prefix = "✅ "
            else:
                text_color = "#9ca3af"
                prefix = "• "

            # Рядок підзадачі
            sub_row = ctk.CTkFrame(list_frame, fg_color="transparent")
            sub_row.pack(fill="x", pady=(1, 1))

            ctk.CTkLabel(
                sub_row,
                text=prefix + sub_task.get("name", "Невідома підзадача"),
                font=("Segoe UI", 9),
                text_color=text_color
            ).pack(anchor="w")

    def apply_task_template(self, choice: str, templates: list,
                            entry_name, combo_cat, entry_xp, entry_target):
        """Підставляє значення в поля вікна задачі за вибраним шаблоном."""
        if choice.startswith("—"):
            return

        template = next((t for t in templates if t["label"] == choice), None)
        if not template:
            return

        # Назва = та ж, що і label (або name, якщо хочеш відрізняти)
        entry_name.delete(0, "end")
        entry_name.insert(0, template.get("name", choice))

        # Категорія
        combo_cat.set(template.get("category", "short"))

        # XP
        entry_xp.delete(0, "end")
        entry_xp.insert(0, str(template.get("xp_reward", 50)))

        # Ціль
        target_val = template.get("target_value")
        if target_val is not None:
            entry_target.delete(0, "end")
            entry_target.insert(0, str(target_val))




    # ---------- Допоміжні методи ----------
    def start_task_timer(self, skill_id: str, task_id: str):
        """Плаваючий таймер поверх усіх вікон для задачі."""
        # шукаємо навичку і задачу
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            return

        task = next((t for t in skill.get("tasks", []) if t.get("id") == task_id), None)
        if not task:
            return

        # базові значення
        base_seconds = int(task.get("time_spent", 0))
        

        win = ctk.CTkToplevel(self.root)
        win.title("Таймер задачі")
        win.geometry("260x160")
        win.attributes("-topmost", True)
        win.grab_set()

        frame = ctk.CTkFrame(win, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(
            frame,
            text=task.get("name", "Задача"),
            font=("Segoe UI", 13, "bold")
        ).pack(pady=(0, 4))

        timer_label = ctk.CTkLabel(
            frame,
            text="00:00:00",
            font=("Segoe UI", 24, "bold")
        )
        timer_label.pack(pady=(0, 6))

        status_label = ctk.CTkLabel(
            frame,
            text="Йде відлік...",
            font=("Segoe UI", 11)
        )
        status_label.pack(pady=(0, 8))

        start_time = time.time()
        running = {"value": True}  # маленький хак через dict, щоб змінювати всередині

        def format_time(total_sec: int) -> str:
            h = total_sec // 3600
            m = (total_sec % 3600) // 60
            s = total_sec % 60
            return f"{h:02d}:{m:02d}:{s:02d}"

        def tick():
            if not running["value"]:
                return
            if not win.winfo_exists():
                return

            now = time.time()
            elapsed = int(now - start_time)
            total = base_seconds + elapsed
            timer_label.configure(text=format_time(total))
            win.after(1000, tick)

        tick()  # стартуємо цикл

        def save_time_and_close(mark_completed: bool):
            """Зберігає час, оновлює задачу, закриває таймер."""
            running["value"] = False
            now = time.time()
            elapsed = int(now - start_time)
            total = base_seconds + elapsed

            task["time_spent"] = total
            save_data(self.data)

            if mark_completed:
                # виконуємо задачу і додаємо XP
                self.execute_task(skill_id, task_id)

            win.destroy()

        def on_in_progress():
            status_label.configure(text="Збережено як 'в процесі'")
            save_time_and_close(mark_completed=False)

        def on_done():
            status_label.configure(text="Завершено ✅")
            save_time_and_close(mark_completed=True)

        btn_row = ctk.CTkFrame(frame, fg_color="transparent")
        btn_row.pack(pady=(4, 0))

        ctk.CTkButton(
            btn_row,
            text="В процесі",
            width=90,
            command=on_in_progress
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            btn_row,
            text="Виконано",
            width=90,
            fg_color="#22c55e",
            command=on_done
        ).pack(side="left", padx=4)



    def get_total_xp(self) -> float:
        """Сумарний XP героя — сума XP по всіх скілах."""
        return sum(skill.get("xp", 0) for skill in self.data.get("skills", []))

    def get_total_level(self) -> int:
        """Рахуємо загальний рівень героя з total_xp."""
        total_xp = self.get_total_xp()
        return xp_to_level(total_xp)
    
    def on_level_up(self, skill: dict, old_lvl: int, new_lvl: int):
        """Попап + кастомний звук при переході на новий рівень — без системного дзвону."""
        skill_name = skill.get("name", "Навичка")

        # ---- наше кастомне вікно замість messagebox ----
        popup = ctk.CTkToplevel(self.root)
        popup.title("Новий рівень!")
        popup.grab_set()
        popup.geometry("320x160")

        frame = ctk.CTkFrame(popup, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            frame,
            text="Новий рівень!",
            font=("Segoe UI", 16, "bold")
        ).pack(pady=(5, 2))

        ctk.CTkLabel(
            frame,
            text=f"'{skill_name}'\n{old_lvl} ➜ {new_lvl}",
            font=("Segoe UI", 13)
        ).pack(pady=(0, 10))

        ctk.CTkButton(
            frame,
            text="Ок",
            width=80,
            command=popup.destroy
        ).pack(pady=(5, 0))

        # ---- програємо твій звук ----
        try:
            if os.path.exists(LEVEL_UP_SOUND_PATH):
                winsound.PlaySound(
                    LEVEL_UP_SOUND_PATH,
                    winsound.SND_FILENAME | winsound.SND_ASYNC
                )
        except Exception as e:
            print("LEVEL UP: sound error:", repr(e))

    def update_cefr_for_skill(self, skill: dict):
        """Оновлює CEFR для мовної навички з комбобокса."""
        if not hasattr(self, "cefr_var"):
            return
        new_cefr = self.cefr_var.get()
        skill["cefr"] = new_cefr
        save_data(self.data)
        messagebox.showinfo("CEFR оновлено", f"Новий рівень CEFR: {new_cefr}")
        # можна оновити тільки екран навички, але простіше:
        self.build_skill_screen(skill["id"])


        # ефект звуку (опційно)
        try:
            import winsound
            winsound.PlaySound("lvlup.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)
        except:
            pass

    # ---------- UI: головний екран ----------
    def ensure_daily_reset(self):
            """Якщо сьогодні новий день — скидаємо daily_done для всіх навичок."""
            today = date.today().isoformat()
            last = self.data.get("last_daily_reset")

            if last != today:
            # новий день — скидаємо daily_done і очищаємо виконані задачі
                for skill in self.data.get("skills", []):
                    skill["daily_done"] = False
                    tasks = skill.get("tasks", [])
                    # залишаємо тільки невиконані
                    skill["tasks"] = [t for t in tasks if not t.get("completed")]
                self.data["last_daily_reset"] = today
                save_data(self.data)

    def build_quests_screen(self):
        """Екран з усіма квестами по всіх навичках."""
        # очистка
        for w in self.root.winfo_children():
            w.destroy()

        main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # верхній рядок: Назад до навичок + заголовок
        top_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkButton(
            top_row,
            text="← Навички",
            width=110,
            command=self.build_main_screen
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text="Квести",
            font=("Segoe UI", 20, "bold")
        ).pack(side="left", padx=12)

        # основний Tabview: Активні / Виконані
        tabview = ctk.CTkTabview(main_frame)
        tabview.pack(fill="both", expand=True, pady=(10, 0))

        tab_active = tabview.add("Активні")
        tab_done = tabview.add("Виконані")

        categories = [
            ("short", "Короткі"),
            ("medium", "Середні"),
            ("long", "Довгі"),
            ("boss", "Боси"),
        ]

        # ---- вкладки категорій в "Активні" ----
        cat_tabs_active = ctk.CTkTabview(tab_active)
        cat_tabs_active.pack(fill="both", expand=True, padx=10, pady=10)

        for key, label in categories:
            cat_tab = cat_tabs_active.add(label)
            self._create_quests_category(
                parent=cat_tab,
                category_key=key,
                category_label=label,
                completed=False
            )

        # ---- вкладки категорій в "Виконані" ----
        cat_tabs_done = ctk.CTkTabview(tab_done)
        cat_tabs_done.pack(fill="both", expand=True, padx=10, pady=10)

        for key, label in categories:
            cat_tab = cat_tabs_done.add(label)
            self._create_quests_category(
                parent=cat_tab,
                category_key=key,
                category_label=label,
                completed=True
            )


    def _create_quest_row(self, parent, skill_name: str, skill_id: str, task: dict):
        """Один квест в екрані 'Квести'."""
        row = ctk.CTkFrame(parent, corner_radius=8, fg_color="#101624")
        row.pack(fill="x", padx=16, pady=4)

        name = task.get("name", "Без назви")
        xp_reward = task.get("xp_reward", 0)
        money_usdt = task.get("money_usdt", 0)
        money_uah = task.get("money_uah", 0)
        completed = bool(task.get("completed", False))

        # Ліва частина
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        title_color = "#9ca3af" if completed else "#e5e7eb"
        reward_color = "#6b7280" if completed else "#9ca3af"

        ctk.CTkLabel(
            left,
            text=name,
            font=("Segoe UI", 13, "bold"),
            text_color=title_color
        ).pack(anchor="w")

        ctk.CTkLabel(
            left,
            text=f"[{skill_name}]  +{xp_reward} XP  |  +{money_usdt} USDT  |  +{money_uah} UAH",
            font=("Segoe UI", 11),
            text_color=reward_color
        ).pack(anchor="w", pady=(2, 0))

        # Прогрес по цілі, якщо є target/current
        target_val = task.get("target_value", 0)
        current_val = task.get("current_value", 0)
        try:
            target_val = float(target_val)
            current_val = float(current_val)
        except (TypeError, ValueError):
            target_val = 0
            current_val = 0

        if target_val and target_val > 0:
            progress = max(0.0, min(1.0, current_val / target_val))
            bar = ctk.CTkProgressBar(row, width=140)
            bar.pack(side="left", padx=(8, 0))
            bar.set(progress)

            percent = int(progress * 100)
            ctk.CTkLabel(
                row,
                text=f"{current_val:.0f} / {target_val:.0f} ({percent}%)",
                font=("Segoe UI", 10),
                text_color="#9ca3af"
            ).pack(side="left", padx=(6, 0))

        # Права частина — кнопки
        buttons = ctk.CTkFrame(row, fg_color="transparent")
        buttons.pack(side="right", padx=8)

        # Перейти до навички
        ctk.CTkButton(
            buttons,
            text="До навички",
            width=90,
            command=lambda s_id=skill_id: self.open_skill(s_id)
        ).pack(side="top", pady=(0, 3))

        # Виконати (якщо ще не виконаний)
        if not completed:
            ctk.CTkButton(
                buttons,
                text="Виконати",
                width=90,
                fg_color="#22c55e",
                command=lambda s_id=skill_id, t_id=task.get("id"): self.execute_task(s_id, t_id)
            ).pack(side="top")
        else:
            ctk.CTkLabel(
                buttons,
                text="✓ Виконано",
                font=("Segoe UI", 11),
                text_color="#22c55e"
            ).pack(side="top")


    def _create_quests_category(self, parent, category_key: str, category_label: str, completed: bool):
        """Категорія квестів у вкладці (short/medium/long/boss), згрупована по навичках."""
        container = ctk.CTkFrame(parent, corner_radius=10)
        container.pack(fill="both", expand=True, padx=5, pady=5)

        any_tasks_overall = False

        for skill in self.data.get("skills", []):
            skill_name = skill.get("name", "???")
            skill_id = skill.get("id")

            # вибираємо задачі цієї навички та категорії
            tasks_for_skill = []
            for task in skill.get("tasks", []):
                if task.get("category") != category_key:
                    continue
                is_completed = bool(task.get("completed", False))
                if is_completed != completed:
                    continue
                tasks_for_skill.append(task)

            if not tasks_for_skill:
                continue  # для цієї навички в цій категорії нічого немає

            any_tasks_overall = True

            # блок для конкретної навички
            skill_block = ctk.CTkFrame(container, corner_radius=8, fg_color="#050816")
            skill_block.pack(fill="x", padx=8, pady=(6, 4))

            # заголовок навички
            ctk.CTkLabel(
                skill_block,
                text=skill_name,
                font=("Segoe UI", 16, "bold")
            ).pack(anchor="w", padx=10, pady=(6, 4))

            # самі квести цієї навички
            for task in tasks_for_skill:
                self._create_quest_row(skill_block, skill_name, skill_id, task)

        if not any_tasks_overall:
            ctk.CTkLabel(
                container,
                text="Немає квестів у цій категорії.",
                font=("Segoe UI", 11),
                text_color="#9ca3af"
            ).pack(anchor="w", padx=16, pady=(6, 6))




    def build_main_screen(self):
        """Головний екран: зліва навички, справа герой (CustomTkinter)."""

        # очистка
        for w in self.root.winfo_children():
            w.destroy()

        # головний контейнер
        main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # ліво/право
        left_frame = ctk.CTkFrame(main_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right_frame = ctk.CTkFrame(main_frame, width=260)
        right_frame.pack(side="right", fill="y")

        # ---------- ПАНЕЛЬ ГЕРОЯ ----------
        hero = self.data.get("hero", {})
        hero_name = hero.get("name", "Hero")
        total_xp = self.get_total_xp()
        total_lvl = self.get_total_level()
        money_usdt = hero.get("money_usdt", 0.0)
        money_uah = hero.get("money_uah", 0.0)
        hp_current = hero.get("hp_current", 100)
        hp_max = hero.get("hp_max", 100)

        title_lbl = ctk.CTkLabel(right_frame, text="Герой", font=("Segoe UI", 18, "bold"))
        title_lbl.pack(pady=(10, 5))

        # аватар
        avatar_path = hero.get("avatar_path") or ""
        if avatar_path and os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path).resize((180, 180))
                self.hero_image = ImageTk.PhotoImage(img)
                avatar_lbl = ctk.CTkLabel(right_frame, image=self.hero_image, text="")
            except Exception:
                avatar_lbl = ctk.CTkLabel(right_frame, text="[ avatar ]")
        else:
            avatar_lbl = ctk.CTkLabel(right_frame, text="[ 3D моделька героя ]")
        avatar_lbl.pack(pady=(0, 10))

        ctk.CTkLabel(
            right_frame,
            text=f"{hero_name}",
            font=("Segoe UI", 14, "bold")
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            right_frame,
            text=f"Рівень: {total_lvl} | XP: {int(total_xp)}",
            font=("Segoe UI", 12)
        ).pack(anchor="w", padx=10)

        ctk.CTkLabel(
            right_frame,
            text=f"HP: {hp_current}/{hp_max}",
            font=("Segoe UI", 12)
        ).pack(anchor="w", padx=10, pady=(5, 0))

        self.money_usdt_var = ctk.StringVar(value=f"{money_usdt:.2f}")
        self.money_uah_var = ctk.StringVar(value=f"{money_uah:.2f}")

        money_frame = ctk.CTkFrame(right_frame, fg_color="transparent")
        money_frame.pack(anchor="w", padx=10, pady=(5, 5))

        ctk.CTkLabel(money_frame, text="USDT:", font=("Segoe UI", 11)).grid(row=0, column=0, sticky="w")
        entry_usdt = ctk.CTkEntry(money_frame, width=90, textvariable=self.money_usdt_var)
        entry_usdt.grid(row=0, column=1, padx=(4, 10), pady=(0, 2))

        ctk.CTkLabel(money_frame, text="UAH:", font=("Segoe UI", 11)).grid(row=1, column=0, sticky="w")
        entry_uah = ctk.CTkEntry(money_frame, width=90, textvariable=self.money_uah_var)
        entry_uah.grid(row=1, column=1, padx=(4, 10), pady=(0, 2))

        ctk.CTkButton(
            right_frame,
            text="Оновити баланс",
            width=140,
            command=self.update_money_from_inputs
        ).pack(anchor="w", padx=10, pady=(0, 12))

        ctk.CTkButton(
            right_frame,
            text="Зберегти стан",
            command=self.handle_save
        ).pack(pady=(0, 15))

        ctk.CTkButton(
            right_frame,
            text="Додати навичку",
            width=140,
            command=self.open_add_skill_dialog
        ).pack(pady=(0, 10))

        ctk.CTkButton(
            right_frame,
            text="Квести",
            width=140,
            command=self.build_quests_screen
        ).pack(pady=(0, 10))

        # ---------- ЛІВО: СПИСОК НАВИЧОК ----------
        ctk.CTkLabel(
            left_frame,
            text="Мої навички",
            font=("Segoe UI", 18, "bold")
        ).pack(anchor="w", pady=(10, 5), padx=5)

        scroll = ctk.CTkScrollableFrame(left_frame)
        scroll.pack(fill="both", expand=True, pady=(0, 5))

        for skill in self.data.get("skills", []):
            self._create_skill_card(scroll, skill)

    def open_edit_task_dialog(self, skill_id: str, task_id: str):
        """Вікно для редагування існуючої задачі (CustomTkinter)."""
        # шукаємо навичку
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", "Скіл не знайдено")
            return

        # шукаємо задачу
        task = next((t for t in skill.get("tasks", []) if t.get("id") == task_id), None)
        if not task:
            messagebox.showerror("Помилка", "Задачу не знайдено")
            return

        win = ctk.CTkToplevel(self.root)
        win.title("Редагувати задачу")
        win.grab_set()
        win.geometry("480x440")

        frame = ctk.CTkFrame(win, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        # ---- Назва ----
        ctk.CTkLabel(frame, text="Назва задачі:").grid(row=0, column=0, sticky="w")
        entry_name = ctk.CTkEntry(frame, width=220)
        entry_name.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 6))
        entry_name.insert(0, task.get("name", ""))

        # ---- Категорія ----
        ctk.CTkLabel(frame, text="Категорія:").grid(row=1, column=0, sticky="w")
        cat_var = ctk.StringVar(value=task.get("category", "short"))
        combo_cat = ctk.CTkComboBox(
            frame,
            variable=cat_var,
            values=["short", "medium", "long", "boss"],
            width=120
        )
        combo_cat.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(0, 6))

        # ---- XP ----
        ctk.CTkLabel(frame, text="XP нагорода:").grid(row=2, column=0, sticky="w")
        entry_xp = ctk.CTkEntry(frame, width=80)
        entry_xp.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(0, 6))
        entry_xp.insert(0, str(task.get("xp_reward", 0)))

        # ---- USDT ----
        ctk.CTkLabel(frame, text="USDT нагорода:").grid(row=3, column=0, sticky="w")
        entry_usdt = ctk.CTkEntry(frame, width=80)
        entry_usdt.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(0, 6))
        entry_usdt.insert(0, str(task.get("money_usdt", 0.0)))

        # ---- UAH ----
        ctk.CTkLabel(frame, text="UAH нагорода:").grid(row=4, column=0, sticky="w")
        entry_uah = ctk.CTkEntry(frame, width=80)
        entry_uah.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(0, 6))
        entry_uah.insert(0, str(task.get("money_uah", 0.0)))

        # ---- ЦІЛЬ ----
        ctk.CTkLabel(frame, text="Ціль (всього):").grid(row=5, column=0, sticky="w")
        entry_target = ctk.CTkEntry(frame, width=80)
        entry_target.grid(row=5, column=1, sticky="w", padx=(8, 0), pady=(0, 6))
        entry_target.insert(0, str(task.get("target_value", 0)))

        # ---- ЗАРАЗ ЗРОБЛЕНО ----
        ctk.CTkLabel(frame, text="Зараз зроблено:").grid(row=6, column=0, sticky="w")
        entry_current = ctk.CTkEntry(frame, width=80)
        entry_current.grid(row=6, column=1, sticky="w", padx=(8, 0), pady=(0, 10))
        entry_current.insert(0, str(task.get("current_value", 0)))

        # Зчитуємо поточні ID, з'єднуючи їх комою для відображення
        current_sub_ids = ", ".join(task.get("required_subtasks_ids", []))

        ctk.CTkLabel(frame, text="ID Підзадач:").grid(row=7, column=0, sticky="w")
        entry_subtask_ids = ctk.CTkEntry(frame, width=220)
        entry_subtask_ids.grid(row=7, column=1, sticky="w", padx=(8, 0), pady=(0, 10))
        entry_subtask_ids.insert(0, current_sub_ids)

        # (опціонально) можна показати скільки часу вже витрачено
        time_spent = int(task.get("time_spent", 0))
        if time_spent > 0:
            h = time_spent // 3600
            m = (time_spent % 3600) // 60
            s = time_spent % 60
            ctk.CTkLabel(
                frame,
                text=f"Час на задачі: {h:02d}:{m:02d}:{s:02d}",
                font=("Segoe UI", 10),
                text_color="#9ca3af"
            ).grid(row=8, column=0, columnspan=2, pady=(0, 6))

        def on_save():
            name = entry_name.get().strip()
            if not name:
                messagebox.showerror("Помилка", "Назва задачі не може бути порожньою")
                return

            # XP
            try:
                xp_val = int(entry_xp.get())
            except ValueError:
                messagebox.showerror("Помилка", "XP має бути числом")
                return

            # Гроші
            try:
                usdt_val = float(entry_usdt.get())
            except ValueError:
                usdt_val = 0.0

            try:
                uah_val = float(entry_uah.get())
            except ValueError:
                uah_val = 0.0

            # Ціль / поточне
            try:
                target_val = float(entry_target.get())
            except ValueError:
                target_val = 0.0

            try:
                current_val = float(entry_current.get())
            except ValueError:
                current_val = 0.0

            # -----------------------------
            # ДОДАНО: ЗБЕРЕЖЕННЯ ID ПІДЗАДАЧ
            # -----------------------------
            subtask_input = entry_subtask_ids.get()
            if subtask_input:
                # Розділяємо рядок за пробілами (включаючи множинні пробіли та переноси)
                sub_ids_list = [
                     id.strip() for id in subtask_input.split() if id.strip()
                ]
                task["required_subtasks_ids"] = sub_ids_list
            elif "required_subtasks_ids" in task:
                # Якщо поле порожнє, але поле було в задачі, видаляємо його
                del task["required_subtasks_ids"]

            # оновлюємо задачу
            task["name"] = name
            task["category"] = cat_var.get()
            task["xp_reward"] = xp_val
            task["money_usdt"] = usdt_val
            task["money_uah"] = uah_val
            task["target_value"] = target_val
            task["current_value"] = current_val

            save_data(self.data)
            win.destroy()
            self.build_skill_screen(skill_id)

        btn_save = ctk.CTkButton(frame, text="Зберегти", command=on_save, width=120)
        btn_save.grid(row=8, column=0, columnspan=2, pady=(8, 0))

        for i in range(2):
            frame.grid_columnconfigure(i, weight=1)


    def delete_task(self, skill_id: str, task_id: str):
        """Видалити задачу з навички."""
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", "Скіл не знайдено")
            return

        tasks = skill.get("tasks", [])
        task = next((t for t in tasks if t.get("id") == task_id), None)
        if not task:
            messagebox.showerror("Помилка", "Задачу не знайдено")
            return

        confirm = messagebox.askyesno(
            "Підтвердження",
            f"Точно видалити задачу:\n\n{task.get('name', 'Без назви')}?"
        )
        if not confirm:
            return

        # видаляємо
        tasks.remove(task)
        save_data(self.data)

        # якщо після видалення в скіла немає невиконаних задач — daily_done можна скинути
        if not any(not t.get("completed") for t in tasks):
            skill["daily_done"] = False

        # оновлюємо екран навички
        self.build_skill_screen(skill_id)


    def build_skill_screen(self, skill_id: str):
        """Екран конкретної навички: стати + задачі."""
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", f"Скіл з id={skill_id} не знайдено")
            return

        # очищаємо вікно
        for widget in self.root.winfo_children():
            widget.destroy()

        # базові дані
        name = skill.get("name", "???")
        xp = skill.get("xp", 0)
        lvl = xp_to_level(xp)
        title = title_for_level(lvl)
        current_level_xp = level_to_xp(lvl)
        next_level_xp = level_to_xp(lvl + 1) if lvl < 40 else level_to_xp(lvl)
        if next_level_xp <= current_level_xp:
            progress = 1.0
        else:
            progress = (xp - current_level_xp) / (next_level_xp - current_level_xp)
            progress = max(0.0, min(1.0, progress))

               # головний фрейм
        main_frame = ctk.CTkFrame(self.root, corner_radius=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        # верхній рядок: Назад + назва навички
        top_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        top_row.pack(fill="x")

        btn_back = ctk.CTkButton(
            top_row,
            text="← Назад",
            width=90,
            command=self.build_main_screen
        )
        btn_back.pack(side="left", padx=(0, 10), pady=5)

        lbl_title = ctk.CTkLabel(
            top_row,
            text=f"Навичка: {name}",
            font=("Segoe UI", 18, "bold")
        )
        lbl_title.pack(side="left", padx=12, pady=5)

        # блок статів навички
        stats_frame = ctk.CTkFrame(main_frame, corner_radius=10)
        stats_frame.pack(fill="x", pady=(12, 8), padx=5)

        lbl_lvl = ctk.CTkLabel(
            stats_frame,
            text=f"Рівень: {lvl} ({title})   XP: {int(xp)} / {int(next_level_xp)}" ,
            font=("Segoe UI", 14)
        )
        lbl_lvl.pack(anchor="w", padx=10, pady=(8, 0))

        lvl_color = color_for_level(lvl)
        ctk.CTkLabel(
            stats_frame,
            text=title.upper(),
            font=("Segoe UI", 15, "bold"),
            text_color=lvl_color
        ).pack(anchor="w", padx=10, pady=(0, 4))

        # -----------------------------
        # ДОДАНО: ВІДОБРАЖЕННЯ STREAK
        # -----------------------------
        current_streak = skill.get("current_streak", 0)
        
        ctk.CTkLabel(
            stats_frame, # <--- ТУТ ТРЕБА ВИКОРИСТОВУВАТИ stats_frame
            text=f"🔥 Серія (Streak): {current_streak} днів",
            font=("Segoe UI", 10, "bold"),
            text_color="#f59e0b" # Помаранчевий колір для "вогню"
        ).pack(pady=(5, 5), anchor="w", padx=(10, 0))
        # -----------------------------

        # CEFR для мов
        is_language = skill.get("type") == "language"

        if is_language:
            # поточний CEFR з data.json
            current_cefr = skill.get("cefr", "A0")

            cefr_row = ctk.CTkFrame(stats_frame, fg_color="transparent")
            cefr_row.pack(anchor="w", padx=10, pady=(4, 4))

            ctk.CTkLabel(
                cefr_row,
                text=f"CEFR:",
                font=("Segoe UI", 12)
            ).pack(side="left")

            self.cefr_var = ctk.StringVar(value=current_cefr)
            cefr_combo = ctk.CTkComboBox(
                cefr_row,
                variable=self.cefr_var,
                values=["A0", "A1", "A2", "B1", "B2", "C1", "C2"],
                width=80
            )
            cefr_combo.pack(side="left", padx=(6, 6))

            ctk.CTkButton(
                cefr_row,
                text="Оновити",
                width=80,
                command=lambda s=skill: self.update_cefr_for_skill(s)
            ).pack(side="left")


        # прогрес-бар
        progressbar = ctk.CTkProgressBar(stats_frame, height=14)
        progressbar.pack(fill="x", padx=10, pady=(8, 0))
        progressbar.set(progress)   # progress у тебе вже порахований 0..1

        lbl_progress = ctk.CTkLabel(
            stats_frame,
            text=f"{int(progress * 100)}% до наступного рівня",
            font=("Segoe UI", 11)
        )
        lbl_progress.pack(anchor="w", padx=10, pady=(4, 8))

   # -------- Загальний час на цю навичку --------
        total_seconds = 0
        for t in skill.get("tasks", []):
            try:
                total_seconds += int(t.get("time_spent", 0) or 0)
            except (TypeError, ValueError):
                pass

        h = total_seconds // 3600
        m = (total_seconds % 3600) // 60
        s = total_seconds % 60

        ctk.CTkLabel(
            stats_frame,
            text=f"Час на навичці: {h:02d}:{m:02d}:{s:02d}",
            font=("Segoe UI", 11),
            text_color="#9ca3af"
        ).pack(anchor="w", pady=(2, 0))




         # --------- блок задач ---------
        tasks_header = ctk.CTkFrame(main_frame, fg_color="transparent")
        tasks_header.pack(fill="x", pady=(12, 4), padx=5)

        lbl_tasks = ctk.CTkLabel(
            tasks_header,
            text="Задачі",
            font=("Segoe UI", 18, "bold")
        )
        lbl_tasks.pack(side="left")

        btn_add_task = ctk.CTkButton(
            tasks_header,
            text="+ Додати задачу",
            width=140,
            command=lambda s_id=skill_id: self.open_add_task_dialog(s_id)
        )
        btn_add_task.pack(side="right")

        # блок задач (скрол)
        tasks_outer = ctk.CTkFrame(main_frame, corner_radius=10)
        tasks_outer.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        tasks_scroll = ctk.CTkScrollableFrame(tasks_outer)
        tasks_scroll.pack(fill="both", expand=True, padx=5, pady=5)


        # категорії
        categories = [
            ("short", "Короткі задачі"),
            ("medium", "Середні задачі"),
            ("long", "Довготривалі задачі"),
            ("boss", "Боси"),
        ]

        tasks = skill.get("tasks", [])

        for cat_key, cat_label in categories:
            cat_tasks = [t for t in tasks if t.get("category") == cat_key]

            # рамка категорії
            cat_frame = ctk.CTkFrame(tasks_scroll)
            cat_frame.pack(fill="x", pady=(4, 8), padx=5)

            lbl_cat = ctk.CTkLabel(
                cat_frame,
                text=cat_label,
                font=("Segoe UI", 13, "bold")
            )
            lbl_cat.pack(anchor="w", padx=8, pady=(4, 2))

            if not cat_tasks:
                ctk.CTkLabel(
                    cat_frame,
                    text="Поки немає задач у цій категорії",
                    font=("Segoe UI", 11)
                ).pack(anchor="w", padx=16, pady=(0, 4))
            else:
                for task in cat_tasks:
                    self._create_task_row(cat_frame, skill_id, task)


    def _create_task_row(self, parent, skill_id: str, task: dict):
        """Одна задача з кнопкою 'Виконати' (CustomTkinter)."""
        row = ctk.CTkFrame(parent)
        row.pack(fill="x", padx=10, pady=4)

        name = task.get("name", "Без назви")
        xp_reward = task.get("xp_reward", 0)
        money_usdt = task.get("money_usdt", 0)
        money_uah = task.get("money_uah", 0)
        completed = task.get("completed", False)

        # ліва частина — текст
        left = ctk.CTkFrame(row, fg_color="transparent")
        left.pack(side="left", fill="x", expand=True)

        # стилі для виконаних / невиконаних
        if completed:
            prefix = "✅ "
            name_color = "#9ca3af"
            reward_color = "#6b7280"
        else:
            prefix = "• "
            name_color = "#e5e7eb"
            reward_color = "#9ca3af"

        lbl_name = ctk.CTkLabel(
            left,
            text=prefix + name,
            font=("Segoe UI", 12),
            text_color=name_color
        )
        lbl_name.pack(anchor="w")

        lbl_rewards = ctk.CTkLabel(
            left,
            text=f"+{xp_reward} XP  |  +{money_usdt} USDT  |  +{money_uah} UAH",
            font=("Segoe UI", 10),
            text_color=reward_color
        )
        lbl_rewards.pack(anchor="w", pady=(2, 0))
        
        # -----------------------------
        # ДОДАНО: ID ТА КНОПКА КОПІЮВАННЯ
        # -----------------------------
        task_id = task.get("id", "ID відсутній")
        
        # Створюємо фрейм для вирівнювання ID та кнопки
        id_row_frame = ctk.CTkFrame(left, fg_color="transparent")
        id_row_frame.pack(anchor="w", pady=(0, 2))

        # Мітка з ID
        ctk.CTkLabel(
            id_row_frame,
            text=f"ID: {task_id}",
            font=("Segoe UI", 8),
            text_color="#6b7280"
        ).pack(side="left")
        
        # Кнопка "Копіювати"
        ctk.CTkButton(
            id_row_frame,
            text="Копіювати",
            width=60, 
            height=15,
            font=("Segoe UI", 8),
            fg_color="#3b82f6", # Синій колір
            command=lambda tid=task_id: self.copy_to_clipboard(tid)
        ).pack(side="left", padx=(10, 0))
        # -----------------------------

        # --- Прогрес-бар по задачі (якщо задана ціль) ---
        target_val = task.get("target_value", 0)
        current_val = task.get("current_value", 0)

        if target_val and target_val > 0:
            progress = max(0.0, min(1.0, current_val / target_val))
            progress_bar = ctk.CTkProgressBar(row, width=180)
            progress_bar.pack(side="left", padx=(10, 0), pady=(4, 4))
            progress_bar.set(progress)

            percent = int(progress * 100)
            ctk.CTkLabel(
                row,
                text=f"{current_val:.0f} / {target_val:.0f} ({percent}%)",
                font=("Segoe UI", 10),
                text_color="#9ca3af"
            ).pack(side="left", padx=(8, 0))


        # права частина — кнопки дій
        buttons_frame = ctk.CTkFrame(row, fg_color="transparent")
        buttons_frame.pack(side="right", padx=5)

        btn_do = ctk.CTkButton(
            buttons_frame,
            text="Виконати",
            width=90,
            command=lambda s_id=skill_id, t_id=task.get("id"): self.execute_task(s_id, t_id)
        )
        btn_do.pack(side="top", pady=(0, 2))

        if completed:
            btn_do.configure(state="disabled", text="Виконано")

        btn_do.pack(side="right", padx=(0, 10))

        is_parent = "required_subtasks_ids" in task
        
        # Якщо це батьківська задача, і вона не виконана, показуємо чек-лист
        if is_parent and not completed:
            
            # Ваш код відображення прогрес-бару та блокування кнопки має бути тут...
            # ...
            
            # Викликаємо функцію для відображення неактивних підзадач
            self._create_subtask_checklist(parent, skill_id, task)

        # Таймер тільки для коротких задач
        if task.get("category") == "short":
            btn_timer = ctk.CTkButton(
                buttons_frame,
                text="До виконання",
                width=90,
                fg_color="#22c55e",
                command=lambda s=skill_id, t=task.get("id"): self.start_task_timer(s, t)
            )
            btn_timer.pack(side="top", pady=(3, 0))

            if completed:
                btn_timer.configure(state="disabled", text="Виконано")
            # -----------------------------
            
            btn_timer.pack(side="top", pady=(3, 0))

        # маленькі кнопки редагувати / видалити
        btn_edit = ctk.CTkButton(
            buttons_frame,
            text="Редагувати",
            width=40,
            fg_color="#3b82f6",
            command=lambda s_id=skill_id, t_id=task.get("id"): self.open_edit_task_dialog(s_id, t_id)
        )
        btn_edit.pack(side="left", padx=(0, 2))

        btn_delete = ctk.CTkButton(
            buttons_frame,
            text="Видалити",
            width=40,
            fg_color="#ef4444",
            command=lambda s_id=skill_id, t_id=task.get("id"): self.delete_task(s_id, t_id)
        )
        btn_delete.pack(side="left")

        if completed:
            btn_do.configure(state="disabled")


    def execute_task(self, skill_id: str, task_id: str):
        """Виконати задачу — додати XP, гроші, позначити completed."""

        # ДОДАНО: СЬОГОДНІШНЯ ДАТА (ДЛЯ STREAK)
        # -----------------------------
        today = datetime.date.today()
        today_str = today.isoformat() # Формат YYYY-MM-DD
        # -----------------------------

        # знаходимо навичку
        skill = next((s for s in self.data.get("skills", []) if s["id"] == skill_id), None)
        if not skill:
            return

        # знаходимо задачу
        task = next((t for t in skill.get("tasks", []) if t["id"] == task_id), None)
        if not task:
            return

        # якщо вже виконана — ігноруємо
        if task.get("completed"):
            return

        xp_reward = task.get("xp_reward", 0)
        money_usdt = task.get("money_usdt", 0.0)
        money_uah = task.get("money_uah", 0.0)

        # -----------------------------
        # XP + LEVEL UP LOGIC
        # -----------------------------
        old_xp = skill.get("xp", 0)
        old_lvl = xp_to_level(old_xp)

        new_xp = old_xp + xp_reward
        skill["xp"] = new_xp

        new_lvl = xp_to_level(new_xp)

        # Якщо отримали новий рівень → викликаємо анімацію/звук/попап
        if new_lvl > old_lvl:
            self.on_level_up(skill, old_lvl, new_lvl)

        # -----------------------------
        # Гроші
        # -----------------------------
        hero = self.data.get("hero", {})
        hero["money_usdt"] = hero.get("money_usdt", 0.0) + money_usdt
        hero["money_uah"] = hero.get("money_uah", 0.0) + money_uah

        # -----------------------------
        # Позначаємо задачу як виконану
        # -----------------------------
        task["completed"] = True
        skill["daily_done"] = True

        # -----------------------------
        # ЛОГІКА РОЗРАХУНКУ STREAK
        # -----------------------------
        last_date_str = skill.get("last_completed_date")
        current_streak = skill.get("current_streak", 0)

        # 1. Якщо це перше виконання
        if not last_date_str:
            skill["current_streak"] = 1
        else:
            last_date = datetime.date.fromisoformat(last_date_str)
            delta = today - last_date

            if delta.days == 1:
                # 2. Якщо виконання було вчора - збільшуємо лічильник
                skill["current_streak"] = current_streak + 1
            elif delta.days > 1:
                # 3. Якщо перерва більше доби - скидаємо
                skill["current_streak"] = 1 # Або 0, якщо не виконано сьогодні
            # Якщо delta.days == 0 (виконано сьогодні раніше) - лічильник не змінюється

        # Оновлюємо дату останнього виконання
        skill["last_completed_date"] = today_str
        # -----------------------------

        save_data(self.data)

        # ДОДАЄМО ВИКЛИК НОВОЇ ФУНКЦІЇ АНІМАЦІЇ ПЕРЕД ПЕРЕБУДОВОЮ ЕКРАНУ
        self.show_xp_gain_animation(skill_id, skill, xp_reward, old_xp, new_xp, old_lvl, new_lvl)

    def open_add_skill_dialog(self):
            """Вікно для створення нової навички."""
            win = ctk.CTkToplevel(self.root)
            win.title("Нова навичка")
            win.grab_set()
            win.geometry("360x200")

            frame = ctk.CTkFrame(win, corner_radius=10)
            frame.pack(fill="both", expand=True, padx=15, pady=15)

            # Назва
            ctk.CTkLabel(frame, text="Назва навички:").grid(row=0, column=0, sticky="w")
            entry_name = ctk.CTkEntry(frame, width=200)
            entry_name.grid(row=0, column=1, sticky="w", padx=(8, 0), pady=(0, 8))

            # Тип
            ctk.CTkLabel(frame, text="Тип:").grid(row=1, column=0, sticky="w")
            type_var = ctk.StringVar(value="general")
            combo_type = ctk.CTkComboBox(
                frame,
                variable=type_var,
                values=["general", "language"],
                width=120
            )
            combo_type.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(0, 8))

            def on_save():
                name = entry_name.get().strip()
                if not name:
                    messagebox.showerror("Помилка", "Назва навички не може бути порожня")
                    return

                skill_type = type_var.get()
                new_id = f"skill_{int(time.time() * 1000)}"

                # базова структура навички
                skill = {
                    "id": new_id,
                    "name": name,
                    "type": skill_type,
                    "xp": 0,
                    "daily_done": False,
                    "tasks": []
                }

                # якщо мова — додаємо CEFR
                if skill_type == "language":
                    skill["cefr"] = "A0"
                else:
                    skill["cefr"] = ""

                self.data.setdefault("skills", []).append(skill)
                save_data(self.data)

                win.destroy()
                # оновлюємо головний екран, щоб новий скіл зʼявився
                self.build_main_screen()

            btn_save = ctk.CTkButton(frame, text="Зберегти", command=on_save)
            btn_save.grid(row=2, column=0, columnspan=2, pady=(10, 0))

            # трохи розтягування, щоб воно виглядало норм
            for i in range(2):
                frame.grid_columnconfigure(i, weight=1)

    def open_add_task_dialog(self, skill_id: str):
        """Вікно для створення нової задачі (з шаблонами)."""
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", "Скіл не знайдено")
            return

        win = ctk.CTkToplevel(self.root)
        win.title("Нова задача")
        win.grab_set()

        frame = ctk.CTkFrame(win, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=12, pady=12)

        # ---- Назва ----
        ctk.CTkLabel(frame, text="Назва задачі:").grid(row=1, column=0, sticky="w", pady=(0, 6))
        entry_name = ctk.CTkEntry(frame, width=220)
        entry_name.grid(row=1, column=1, sticky="w", pady=(0, 6))

        # ---- Категорія ----
        ctk.CTkLabel(frame, text="Категорія:").grid(row=2, column=0, sticky="w", pady=(0, 6))
        cat_var = ctk.StringVar(value="short")
        combo_cat = ctk.CTkComboBox(
            frame,
            values=["short", "medium", "long", "boss"],
            variable=cat_var,
            width=120
        )
        combo_cat.grid(row=2, column=1, sticky="w", pady=(0, 6))

        # ---- XP ----
        ctk.CTkLabel(frame, text="XP нагорода:").grid(row=3, column=0, sticky="w", pady=(0, 6))
        entry_xp = ctk.CTkEntry(frame, width=80)
        entry_xp.insert(0, "50")
        entry_xp.grid(row=3, column=1, sticky="w", pady=(0, 6))

        # ---- USDT ----
        ctk.CTkLabel(frame, text="USDT нагорода:").grid(row=4, column=0, sticky="w", pady=(0, 6))
        entry_usdt = ctk.CTkEntry(frame, width=80)
        entry_usdt.insert(0, "0")
        entry_usdt.grid(row=4, column=1, sticky="w", pady=(0, 6))

        # ---- UAH ----
        ctk.CTkLabel(frame, text="UAH нагорода:").grid(row=5, column=0, sticky="w", pady=(0, 6))
        entry_uah = ctk.CTkEntry(frame, width=80)
        entry_uah.insert(0, "0")
        entry_uah.grid(row=5, column=1, sticky="w", pady=(0, 6))

        # ---- Ціль ----
        ctk.CTkLabel(frame, text="Ціль (всього):").grid(row=6, column=0, sticky="w", pady=(0, 6))
        entry_target = ctk.CTkEntry(frame, width=80)
        entry_target.insert(0, "0")
        entry_target.grid(row=6, column=1, sticky="w", pady=(0, 6))

        # ---- Зараз зроблено ----
        ctk.CTkLabel(frame, text="Зараз зроблено:").grid(row=7, column=0, sticky="w", pady=(0, 10))
        entry_current = ctk.CTkEntry(frame, width=80)
        entry_current.insert(0, "0")
        entry_current.grid(row=7, column=1, sticky="w", pady=(0, 10))

        # ---- ШАБЛОН (ставимо зверху, але створюємо після полів) ----
        skill_type = skill.get("type", "default")
        templates = TASK_TEMPLATES.get(skill_type, TASK_TEMPLATES["default"])
        template_labels = ["— без шаблону —"] + [t["label"] for t in templates]

        ctk.CTkLabel(frame, text="Шаблон:").grid(row=0, column=0, sticky="w", pady=(0, 6))
        template_var = ctk.StringVar(value=template_labels[0])
        combo_template = ctk.CTkComboBox(
            frame,
            values=template_labels,
            variable=template_var,
            command=lambda choice: self.apply_task_template(
                choice,
                templates,
                entry_name,
                combo_cat,
                entry_xp,
                entry_target
            )
        )
        combo_template.grid(row=0, column=1, sticky="w", pady=(0, 6))

        # ---- Кнопка збереження ----
        def on_save():
            name = entry_name.get().strip()
            if not name:
                messagebox.showerror("Помилка", "Введи назву задачі")
                return

            category = cat_var.get()
            try:
                xp_reward = int(entry_xp.get())
            except ValueError:
                xp_reward = 0

            try:
                money_usdt = float(entry_usdt.get())
            except ValueError:
                money_usdt = 0.0

            try:
                money_uah = float(entry_uah.get())
            except ValueError:
                money_uah = 0.0

            try:
                target_val = float(entry_target.get())
            except ValueError:
                target_val = 0.0

            try:
                current_val = float(entry_current.get())
            except ValueError:
                current_val = 0.0

            task_id = str(uuid.uuid4())
            task = {
                "id": task_id,
                "name": name,
                "category": category,
                "xp_reward": xp_reward,
                "money_usdt": money_usdt,
                "money_uah": money_uah,
                "target_value": target_val,
                "current_value": current_val,
                "time_spent": 0,
                "completed": False
            }

            # якщо раптом масиву tasks ще немає — створюємо
            if "tasks" not in skill:
                skill["tasks"] = []
            skill["tasks"].append(task)

            # тихо зберігаємо у data.json, без попапів
            try:
                save_data(self.data)   # глобальна функція з твого файлу
            except NameError:
                # якщо раптом переіменуєш — просто не впаде
                pass

            win.destroy()
            self.open_skill(skill_id)



        btn_save = ctk.CTkButton(frame, text="Зберегти", command=on_save)
        btn_save.grid(row=8, column=0, columnspan=2, pady=(4, 0))


    def _create_skill_card(self, parent, skill: dict):
        """Одна картка навички в списку (CustomTkinter)."""
        frame = ctk.CTkFrame(parent)
        frame.pack(fill="x", pady=6, padx=5)

        name = skill.get("name", "???")
        xp = skill.get("xp", 0)
        lvl = xp_to_level(xp)
        title = title_for_level(lvl)

        current_level_xp = level_to_xp(lvl)
        next_level_xp = level_to_xp(lvl + 1) if lvl < 40 else level_to_xp(lvl)
        if next_level_xp <= current_level_xp:
            progress = 1.0
        else:
            progress = (xp - current_level_xp) / (next_level_xp - current_level_xp)
            progress = max(0.0, min(1.0, progress))

        top_row = ctk.CTkFrame(frame, fg_color="transparent")
        top_row.pack(fill="x", pady=(5, 0))

        # назва навички
        ctk.CTkLabel(
            top_row,
            text=name,
            font=("Segoe UI", 15, "bold")
        ).pack(side="left", anchor="w")

        # великий рівень справа з кольором
        lvl_color = color_for_level(lvl)
        lvl_label = ctk.CTkLabel(
            top_row,
            text=f"lvl {lvl}",
            font=("Segoe UI", 16, "bold"),
            text_color=lvl_color
        )
        lvl_label.pack(side="right", anchor="e")

        # великий статус під назвою
        ctk.CTkLabel(
            frame,
            text=title.upper(),          # НОВАЧОК / МАЙСТЕР / ЛЕГЕНДА
            font=("Segoe UI", 13, "bold"),
            text_color=lvl_color
        ).pack(anchor="w", padx=5, pady=(0, 2))

        bar = ctk.CTkProgressBar(frame)
        bar.pack(fill="x", padx=5, pady=(5, 0))
        bar.set(progress)

  # --- XP + титул + CEFR (ручний) ---
        subtitle_parts = [f"XP: {int(xp)}", title]

        if skill.get("type") == "language":
            cefr = skill.get("cefr", "A0")
            subtitle_parts.append(f"CEFR: {cefr}")

        subtitle_text = " | ".join(subtitle_parts)

        ctk.CTkLabel(
            frame,
            text=subtitle_text,
            font=("Segoe UI", 11)
        ).pack(anchor="w", padx=5, pady=(2, 0))

        ctk.CTkLabel(
            frame,
            text=subtitle_text,
            font=("Segoe UI", 11)
        ).pack(anchor="w", padx=5, pady=(2, 0))


        bottom_row = ctk.CTkFrame(frame, fg_color="transparent")
        bottom_row.pack(fill="x", pady=(4, 5))

        daily_done = skill.get("daily_done", False)
        if daily_done:
            text = "Сьогодні зроблено ✅"
            color = "#22c55e"
        else:
            text = "Сьогодні ще нічого ❗"
            color = "#f97316"

        ctk.CTkLabel(
            bottom_row,
            text=text,
            text_color=color,
            font=("Segoe UI", 10)
        ).pack(side="left", anchor="w", padx=5)

        ctk.CTkButton(
            bottom_row,
            text="Відкрити",
            width=100,
            command=lambda s_id=skill["id"]: self.open_skill(s_id)
        ).pack(side="right", padx=5)


    # ---------- Обробники ----------

    def handle_save(self):
        """Обробка натискання кнопки збереження."""
        save_data(self.data)
        messagebox.showinfo("Збережено", "Стан успішно збережено у data.json")

    def update_money_from_inputs(self):
        """Бере значення з полів вводу і зберігає в hero.money_*."""
        hero = self.data.get("hero", {})

        try:
            hero["money_usdt"] = float(self.money_usdt_var.get())
        except Exception:
            hero["money_usdt"] = hero.get("money_usdt", 0.0)

        try:
            hero["money_uah"] = float(self.money_uah_var.get())
        except Exception:
            hero["money_uah"] = hero.get("money_uah", 0.0)

        save_data(self.data)
        # перезбираємо головний екран, щоб все оновилось
        self.build_main_screen()


    def open_skill(self, skill_id: str):
        """Переходимо на екран конкретної навички."""
        self.build_skill_screen(skill_id)



if __name__ == "__main__":
    
    ctk.set_appearance_mode("dark")         # "dark" / "light" / "system"
    ctk.set_default_color_theme("dark-blue")  # або "green", "blue", "dark-blue"

    root = ctk.CTk()
    root.title("RPGLife")
    app = App(root)
    root.mainloop()