import json
import os
import math
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk
from datetime import date
import time
import tkinter.font as tkfont



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
        else:
            skill_type = "general"

        skills.append({
            "id": s["id"],
            "name": s["name"],
            "type": skill_type,
            "xp": 0,
            "daily_done": False,
            "tasks": []
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

    return data


def save_data(data: dict) -> None:
    """Зберегти стан у data.json."""
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ---------- Клас застосунку ----------

class App:
    def __init__(self, root: tk.Tk):
        self.hero_image = None  # щоб картинку не зʼїв GC
        self.root = root
        self.root.title("RPGLife: Hero’s Journey")
        self.root.geometry("900x550")
        self.root.configure(bg="#050816")  # темний фон

        self.hero_image = None  # для аватарки

        # стилі
        self.setup_styles()

        # Завантажуємо дані
        self.data = load_data()
        # Перевіряємо, чи новий день — якщо так, скидаємо daily_done
        self.ensure_daily_reset()

        # Побудова головного екрану
        self.build_main_screen()


    # ---------- Допоміжні методи ----------

    def get_total_xp(self) -> float:
        """Сумарний XP героя — сума XP по всіх скілах."""
        return sum(skill.get("xp", 0) for skill in self.data.get("skills", []))

    def get_total_level(self) -> int:
        """Рахуємо загальний рівень героя з total_xp."""
        total_xp = self.get_total_xp()
        return xp_to_level(total_xp)

    def setup_styles(self):
            style = ttk.Style()
            # тема, яка дозволяє кастомізувати кольори
            try:
                style.theme_use("clam")
            except Exception:
                pass

            # Головний фон
            style.configure(
                "Main.TFrame",
                background="#050816"
            )

            # Карти (скіли, герой)
            style.configure(
                "Card.TFrame",
                background="#0b1220",
                relief="flat",
                borderwidth=0
            )

            style.configure(
                "Hero.TFrame",
                background="#020617",
                relief="flat",
                borderwidth=0
            )

            # Тексти
            style.configure(
                "Title.TLabel",
                background="#050816",
                foreground="#e5e7eb",
                font=("Segoe UI", 12, "bold")
            )

            style.configure(
                "SkillName.TLabel",
                background="#0b1220",
                foreground="#e5e7eb",
                font=("Segoe UI", 10, "bold")
            )

            style.configure(
                "Stat.TLabel",
                background="#0b1220",
                foreground="#9ca3af",
                font=("Segoe UI", 9)
            )

            style.configure(
                "HeroStat.TLabel",
                background="#020617",
                foreground="#e5e7eb",
                font=("Segoe UI", 9)
            )

            # Кнопки
            style.configure(
                "RPG.TButton",
                background="#1d283a",
                foreground="#e5e7eb",
                font=("Segoe UI", 9, "bold"),
                padding=4
            )
            style.map(
                "RPG.TButton",
                background=[("active", "#111827")]
            )

            # Прогрес-бар XP
            style.configure(
                "XP.Horizontal.TProgressbar",
                troughcolor="#020617",
                bordercolor="#020617",
                background="#22c55e",
                lightcolor="#4ade80",
                darkcolor="#16a34a"
            )

    # ---------- UI: головний екран ----------
    def ensure_daily_reset(self):
            """Якщо сьогодні новий день — скидаємо daily_done для всіх навичок."""
            today = date.today().isoformat()
            last = self.data.get("last_daily_reset")

            if last != today:
                # новий день — скидаємо daily_done
                for skill in self.data.get("skills", []):
                    skill["daily_done"] = False
                self.data["last_daily_reset"] = today
                save_data(self.data)



    def build_main_screen(self):
        """Головний екран: зліва навички, справа герой."""

        # Очистити вікно
        for widget in self.root.winfo_children():
            widget.destroy()

        # Головний контейнер: ліво/право
        main_frame = ttk.Frame(self.root, padding=16, style="Main.TFrame")
        main_frame.pack(fill="both", expand=True)

        # Ліво — навички
        left_frame = ttk.Frame(main_frame, style="Main.TFrame")
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 12))

        # Право — герой (панель)
        right_frame_outer = ttk.Frame(main_frame, style="Main.TFrame")
        right_frame_outer.pack(side="right", fill="y")

        hero_frame = ttk.Frame(right_frame_outer, padding=12, style="Hero.TFrame")
        hero_frame.pack(fill="y")

        # --------- ПАНЕЛЬ ГЕРОЯ (СПРАВА) ---------
        hero = self.data.get("hero", {})
        hero_name = hero.get("name", "Hero")

        total_xp = self.get_total_xp()
        total_level = self.get_total_level()

        money_usdt = hero.get("money_usdt", hero.get("money", 0.0))
        money_uah = hero.get("money_uah", 0.0)

        hp_current = hero.get("hp_current", 100)
        hp_max = hero.get("hp_max", 100)

        lbl_hero_title = ttk.Label(
            hero_frame,
            text="Герой",
            style="Title.TLabel"
        )
        lbl_hero_title.pack(pady=(0, 8), anchor="center")

        # Аватар
        avatar_path = hero.get("avatar_path") or ""
        if avatar_path and os.path.exists(avatar_path):
            try:
                img = Image.open(avatar_path)
                img = img.resize((180, 180))
                self.hero_image = ImageTk.PhotoImage(img)
                avatar_box = tk.Label(
                    hero_frame,
                    image=self.hero_image,
                    bg="#020617"
                )
                avatar_box.pack(pady=(0, 8))
            except Exception:
                avatar_box = tk.Label(
                    hero_frame,
                    text="[ 3D моделька героя ]",
                    width=22,
                    height=10,
                    bg="#111827",
                    fg="#9ca3af"
                )
                avatar_box.pack(pady=(0, 8))
        else:
            avatar_box = tk.Label(
                hero_frame,
                text="[ 3D моделька героя ]",
                width=22,
                height=10,
                bg="#111827",
                fg="#9ca3af"
            )
            avatar_box.pack(pady=(0, 8))

        # Стати героя
        lbl_name = ttk.Label(
            hero_frame,
            text=f"{hero_name}",
            style="HeroStat.TLabel",
            font=("Segoe UI", 11, "bold")
        )
        lbl_name.pack(anchor="w")

        lbl_level = ttk.Label(
            hero_frame,
            text=f"Рівень: {total_level}   XP: {int(total_xp)}",
            style="HeroStat.TLabel"
        )
        lbl_level.pack(anchor="w")

        lbl_hp = ttk.Label(
            hero_frame,
            text=f"HP: {hp_current}/{hp_max}",
            style="HeroStat.TLabel"
        )
        lbl_hp.pack(anchor="w", pady=(4, 0))

        lbl_money = ttk.Label(
            hero_frame,
            text=f"USDT: {money_usdt:.2f}\nUAH: {money_uah:.2f}",
            style="HeroStat.TLabel"
        )
        lbl_money.pack(anchor="w", pady=(4, 0))

        btn_save = ttk.Button(hero_frame, text="Зберегти стан", style="RPG.TButton", command=self.handle_save)
        btn_save.pack(pady=(12, 0), anchor="center")

        # --------- ЛІВО — СПИСОК НАВИЧОК ---------
        lbl_skills_title = ttk.Label(left_frame, text="Мої навички", style="Title.TLabel")
        lbl_skills_title.pack(anchor="w", pady=(0, 8))

        # фрейм зі скролом
        canvas = tk.Canvas(left_frame, borderwidth=0, highlightthickness=0, bg="#050816")
        inner_frame = ttk.Frame(canvas, style="Main.TFrame")
        scrollbar = ttk.Scrollbar(left_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_frame_configure)

        for skill in self.data.get("skills", []):
            self._create_skill_card(inner_frame, skill)

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
        main_frame = ttk.Frame(self.root, padding=16, style="Main.TFrame")
        main_frame.pack(fill="both", expand=True)

        # верхній рядок: Назад + назва навички
        top_row = ttk.Frame(main_frame, style="Main.TFrame")
        top_row.pack(fill="x")

        btn_back = ttk.Button(top_row, text="← Назад", style="RPG.TButton", command=self.build_main_screen)
        btn_back.pack(side="left")

        lbl_title = ttk.Label(
            top_row,
            text=f"Навичка: {name}",
            style="Title.TLabel"
        )
        lbl_title.pack(side="left", padx=12)

        # блок статів навички
        stats_frame = ttk.Frame(main_frame, padding=12, style="Card.TFrame")
        stats_frame.pack(fill="x", pady=(12, 8))

        lbl_lvl = ttk.Label(
            stats_frame,
            text=f"Рівень: {lvl} ({title})   XP: {int(xp)}",
            style="HeroStat.TLabel"
        )
        lbl_lvl.pack(anchor="w")

        # CEFR для мов
        if skill.get("type") == "language":
            cefr = cefr_from_level(lvl)
            lbl_cefr = ttk.Label(
                stats_frame,
                text=f"CEFR: {cefr}",
                style="HeroStat.TLabel"
            )
            lbl_cefr.pack(anchor="w")

        # прогрес-бар
        progressbar = ttk.Progressbar(
            stats_frame,
            orient="horizontal",
            mode="determinate",
            style="XP.Horizontal.TProgressbar"
        )
        progressbar.pack(fill="x", pady=(6, 0))
        progressbar["maximum"] = 100
        progressbar["value"] = int(progress * 100)

        lbl_progress = ttk.Label(
            stats_frame,
            text=f"{int(progress * 100)}% до наступного рівня",
            style="HeroStat.TLabel"
        )
        lbl_progress.pack(anchor="w", pady=(2, 0))

        # --------- блок задач ---------
        tasks_header = ttk.Frame(main_frame, style="Main.TFrame")
        tasks_header.pack(fill="x", pady=(12, 4))

        lbl_tasks = ttk.Label(tasks_header, text="Задачі", style="Title.TLabel")
        lbl_tasks.pack(side="left")

        btn_add_task = ttk.Button(
            tasks_header,
            text="+ Додати задачу",
            style="RPG.TButton",
            command=lambda s_id=skill_id: self.open_add_task_dialog(s_id)
        )
        btn_add_task.pack(side="right")

        # скрол для задач
        tasks_outer = ttk.Frame(main_frame, style="Main.TFrame")
        tasks_outer.pack(fill="both", expand=True)

        canvas = tk.Canvas(tasks_outer, borderwidth=0, highlightthickness=0, bg="#050816")
        inner_frame = ttk.Frame(canvas, style="Main.TFrame")
        scrollbar = ttk.Scrollbar(tasks_outer, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_frame_configure)

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

            cat_frame = ttk.Frame(inner_frame, padding=8, style="Main.TFrame")
            cat_frame.pack(fill="x", pady=(4, 8))

            lbl_cat = ttk.Label(cat_frame, text=cat_label, style="SkillName.TLabel")
            lbl_cat.pack(anchor="w")

            if not cat_tasks:
                lbl_empty = ttk.Label(
                    cat_frame,
                    text="Поки немає задач у цій категорії",
                    style="Stat.TLabel"
                )
                lbl_empty.pack(anchor="w", padx=8, pady=(2, 0))
            else:
                for task in cat_tasks:
                    self._create_task_row(cat_frame, skill_id, task)

    def _create_task_row(self, parent, skill_id: str, task: dict):
        """Одна задача з кнопкою 'Виконати'."""
        row = ttk.Frame(parent, padding=6, style="Card.TFrame")
        row.pack(fill="x", padx=8, pady=3)

        name = task.get("name", "Без назви")
        xp_reward = task.get("xp_reward", 0)
        money_usdt = task.get("money_usdt", 0)
        money_uah = task.get("money_uah", 0)

        left = ttk.Frame(row, style="Card.TFrame")
        left.pack(side="left", fill="x", expand=True)

        lbl_name = ttk.Label(left, text=name, style="SkillName.TLabel")
        lbl_name.pack(anchor="w")

        lbl_rewards = ttk.Label(
            left,
            text=f"+{xp_reward} XP  |  +{money_usdt} USDT  |  +{money_uah} UAH",
            style="Stat.TLabel"
        )
        lbl_rewards.pack(anchor="w")

        btn_do = ttk.Button(
            row,
            text="Виконати",
            style="RPG.TButton",
            command=lambda s_id=skill_id, t_id=task.get("id"): self.execute_task(s_id, t_id)
        )
        btn_do.pack(side="right")

    def execute_task(self, skill_id: str, task_id: str):
        """Виконання задачі: додаємо XP, гроші, daily_done."""
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", "Скіл не знайдено")
            return

        tasks = skill.get("tasks", [])
        task = next((t for t in tasks if t.get("id") == task_id), None)
        if not task:
            messagebox.showerror("Помилка", "Задачу не знайдено")
            return

        xp_reward = task.get("xp_reward", 0)
        money_usdt = task.get("money_usdt", 0)
        money_uah = task.get("money_uah", 0)

        # додаємо XP навичці
        skill["xp"] = skill.get("xp", 0) + xp_reward

        # додаємо гроші герою
        hero = self.data.get("hero", {})
        hero["money_usdt"] = hero.get("money_usdt", 0.0) + money_usdt
        hero["money_uah"] = hero.get("money_uah", 0.0) + money_uah

        # daily_done
        skill["daily_done"] = True

        save_data(self.data)

        # оновлюємо екран навички (щоб прогрес змінився)
        self.build_skill_screen(skill_id)

    def open_add_task_dialog(self, skill_id: str):
        """Невелике вікно для створення нової задачі."""
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", "Скіл не знайдено")
            return

        win = tk.Toplevel(self.root)
        win.title("Нова задача")
        win.grab_set()

        frame = ttk.Frame(win, padding=12)
        frame.pack(fill="both", expand=True)

        # Назва
        ttk.Label(frame, text="Назва задачі:").grid(row=0, column=0, sticky="w")
        entry_name = ttk.Entry(frame, width=30)
        entry_name.grid(row=0, column=1, sticky="w")

        # Категорія
        ttk.Label(frame, text="Категорія:").grid(row=1, column=0, sticky="w", pady=(6, 0))
        cat_var = tk.StringVar(value="short")
        combo_cat = ttk.Combobox(
            frame,
            textvariable=cat_var,
            values=["short", "medium", "long", "boss"],
            state="readonly",
            width=10
        )
        combo_cat.grid(row=1, column=1, sticky="w", pady=(6, 0))

        # XP
        ttk.Label(frame, text="XP нагорода:").grid(row=2, column=0, sticky="w", pady=(6, 0))
        entry_xp = ttk.Entry(frame, width=10)
        entry_xp.insert(0, "50")
        entry_xp.grid(row=2, column=1, sticky="w", pady=(6, 0))

        # USDT
        ttk.Label(frame, text="USDT нагорода:").grid(row=3, column=0, sticky="w", pady=(6, 0))
        entry_usdt = ttk.Entry(frame, width=10)
        entry_usdt.insert(0, "0")
        entry_usdt.grid(row=3, column=1, sticky="w", pady=(6, 0))

        # UAH
        ttk.Label(frame, text="UAH нагорода:").grid(row=4, column=0, sticky="w", pady=(6, 0))
        entry_uah = ttk.Entry(frame, width=10)
        entry_uah.insert(0, "0")
        entry_uah.grid(row=4, column=1, sticky="w", pady=(6, 0))

        def on_save():
            name = entry_name.get().strip()
            if not name:
                messagebox.showerror("Помилка", "Назва задачі не може бути порожня")
                return

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

            new_task = {
                "id": f"task_{int(time.time() * 1000)}",
                "name": name,
                "category": cat_var.get(),
                "xp_reward": xp_reward,
                "money_usdt": money_usdt,
                "money_uah": money_uah,
            }

            skill.setdefault("tasks", []).append(new_task)
            save_data(self.data)
            win.destroy()
            self.build_skill_screen(skill_id)

        btn_save = ttk.Button(frame, text="Зберегти", style="RPG.TButton", command=on_save)
        btn_save.grid(row=5, column=0, columnspan=2, pady=(12, 0))

        for i in range(2):
            frame.grid_columnconfigure(i, weight=1)


    def _create_skill_card(self, parent, skill: dict):
        """Створює одну картку скіла на головному екрані."""
        frame = ttk.Frame(parent, padding=10, style="Card.TFrame")
        frame.pack(fill="x", pady=6)

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

        # Верхній рядок
        top_row = ttk.Frame(frame, style="Card.TFrame")
        top_row.pack(fill="x")

        lbl_name = ttk.Label(top_row, text=f"{name}", style="SkillName.TLabel")
        lbl_name.pack(side="left", anchor="w")

        lbl_level = ttk.Label(
            top_row,
            text=f"lvl {lvl} ({title}) | XP: {int(xp)}",
            style="Stat.TLabel"
        )
        lbl_level.pack(side="right", anchor="e")

        # Прогрес-бар
        progress_row = ttk.Frame(frame, style="Card.TFrame")
        progress_row.pack(fill="x", pady=(4, 0))

        progressbar = ttk.Progressbar(
            progress_row,
            orient="horizontal",
            length=200,
            mode="determinate",
            style="XP.Horizontal.TProgressbar"
        )
        progressbar.pack(fill="x")
        progressbar["maximum"] = 100
        progressbar["value"] = int(progress * 100)

        lbl_progress = ttk.Label(
            progress_row,
            text=f"{int(progress * 100)}% до наступного рівня",
            style="Stat.TLabel"
        )
        lbl_progress.pack(anchor="w")

        # Нижній рядок: daily + кнопка
        bottom_row = ttk.Frame(frame, style="Card.TFrame")
        bottom_row.pack(fill="x", pady=(4, 0))

        daily_done = skill.get("daily_done", False)
        if daily_done:
            text = "Сьогодні зроблено ✅"
            fg = "#22c55e"
        else:
            text = "Сьогодні ще нічого ❗"
            fg = "#f97316"

        lbl_daily = tk.Label(
            bottom_row,
            text=text,
            fg=fg,
            bg="#0b1220",
            font=("Segoe UI", 9)
        )
        lbl_daily.pack(side="left", anchor="w")

        btn_open = ttk.Button(
            bottom_row,
            text="Відкрити",
            style="RPG.TButton",
            command=lambda s_id=skill["id"]: self.open_skill(s_id)
        )
        btn_open.pack(side="right")

    # ---------- Обробники ----------

    def handle_save(self):
        """Обробка натискання кнопки збереження."""
        save_data(self.data)
        messagebox.showinfo("Збережено", "Стан успішно збережено у data.json")

    def open_skill(self, skill_id: str):
        """Переходимо на екран конкретної навички."""
        self.build_skill_screen(skill_id)



if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
