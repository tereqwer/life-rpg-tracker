import json
import os
import math
import tkinter as tk
from tkinter import ttk, messagebox

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


def level_to_xp(level: int) -> float:
    """Скільки XP треба для певного рівня (сукупний поріг)."""
    if level <= 0:
        return 0.0
    return 120.0 * (level ** 1.6)


# ---------- Робота з data.json ----------

def create_default_data() -> dict:
    """Початковий стан, якщо data.json ще немає."""
    skills = []
    for s in DEFAULT_SKILLS:
        skills.append({
            "id": s["id"],
            "name": s["name"],
            "type": "general",     # потім можемо міняти (language/sport/etc.)
            "xp": 0,
            "daily_done": False,
            "tasks": []
        })

    data = {
        "hero": {
            "name": "Pasha",
            "xp_total": 0,      # можемо не зберігати, а рахувати з skills
            "money": 0,
            "avatar_path": ""   # додамо пізніше
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
        self.root = root
        self.root.title("Life RPG")

        # можна трохи розтягнути вікно
        self.root.geometry("700x500")

        # Завантажуємо дані
        self.data = load_data()

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

    # ---------- UI: головний екран ----------

    def build_main_screen(self):
        """Створюємо головний екран з картками навичок."""

        # Очистити вікно
        for widget in self.root.winfo_children():
            widget.destroy()

        # -------- Верхня панель героя --------
        hero_frame = ttk.Frame(self.root, padding=10)
        hero_frame.pack(fill="x")

        hero_name = self.data["hero"].get("name", "Hero")
        total_xp = self.get_total_xp()
        total_level = self.get_total_level()
        money = self.data["hero"].get("money", 0)

        lbl_hero = ttk.Label(
            hero_frame,
            text=f"Герой: {hero_name} | Загальний рівень: {total_level} | Загальний XP: {int(total_xp)} | Гроші: {money}",
            font=("Segoe UI", 11, "bold")
        )
        lbl_hero.pack(anchor="w")

        # -------- Список навичок (картки) --------
        skills_frame = ttk.Frame(self.root, padding=10)
        skills_frame.pack(fill="both", expand=True)

        lbl_skills_title = ttk.Label(skills_frame, text="Мої навички:", font=("Segoe UI", 10, "bold"))
        lbl_skills_title.pack(anchor="w", pady=(0, 5))

        # Для скролу, якщо скілів буде багато
        canvas = tk.Canvas(skills_frame, borderwidth=0, highlightthickness=0)
        inner_frame = ttk.Frame(canvas)
        scrollbar = ttk.Scrollbar(skills_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # щоб фрейм всередині канваса розтягнувся
        canvas.create_window((0, 0), window=inner_frame, anchor="nw")

        def on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        inner_frame.bind("<Configure>", on_frame_configure)

        # Картки для кожного скіла
        for skill in self.data.get("skills", []):
            self._create_skill_card(inner_frame, skill)

        # -------- Кнопка "Зберегти" --------
        btn_save = ttk.Button(self.root, text="Зберегти стан", command=self.handle_save)
        btn_save.pack(pady=(0, 10))

    def _create_skill_card(self, parent, skill: dict):
        """Створює одну картку скіла на головному екрані."""
        frame = ttk.Frame(parent, padding=8, relief="ridge")
        frame.pack(fill="x", pady=4)

        name = skill.get("name", "???")
        xp = skill.get("xp", 0)
        lvl = xp_to_level(xp)

        # Підрахунок прогресу до наступного рівня
        current_level_xp = level_to_xp(lvl)
        next_level_xp = level_to_xp(lvl + 1) if lvl < 40 else level_to_xp(lvl)
        if next_level_xp <= current_level_xp:
            progress = 1.0
        else:
            progress = (xp - current_level_xp) / (next_level_xp - current_level_xp)
            progress = max(0.0, min(1.0, progress))

        # Верхній рядок: назва, рівень, XP
        top_row = ttk.Frame(frame)
        top_row.pack(fill="x")

        lbl_name = ttk.Label(top_row, text=f"{name}", font=("Segoe UI", 10, "bold"))
        lbl_name.pack(side="left", anchor="w")

        lbl_level = ttk.Label(top_row, text=f"lvl {lvl} | XP: {int(xp)}")
        lbl_level.pack(side="right", anchor="e")

        # Другий рядок: прогрес-бар
        progress_row = ttk.Frame(frame)
        progress_row.pack(fill="x", pady=(4, 0))

        progressbar = ttk.Progressbar(
            progress_row,
            orient="horizontal",
            length=200,
            mode="determinate"
        )
        progressbar.pack(fill="x")
        progressbar["maximum"] = 100
        progressbar["value"] = int(progress * 100)

        # Текст з відсотком
        lbl_progress = ttk.Label(
            progress_row,
            text=f"{int(progress * 100)}% до наступного рівня"
        )
        lbl_progress.pack(anchor="w")

        # Третій рядок: індикатор daily_done + кнопка "Відкрити"
        bottom_row = ttk.Frame(frame)
        bottom_row.pack(fill="x", pady=(4, 0))

        daily_done = skill.get("daily_done", False)
        if daily_done:
            text = "Сьогодні зроблено ✅"
            color = "green"
        else:
            text = "Сьогодні ще нічого ❗"
            color = "red"

        lbl_daily = tk.Label(bottom_row, text=text, fg=color)  # tk.Label для кольору
        lbl_daily.pack(side="left", anchor="w")

        btn_open = ttk.Button(bottom_row, text="Відкрити", command=lambda s_id=skill["id"]: self.open_skill(s_id))
        btn_open.pack(side="right")

    # ---------- Обробники ----------

    def handle_save(self):
        """Обробка натискання кнопки збереження."""
        save_data(self.data)
        messagebox.showinfo("Збережено", "Стан успішно збережено у data.json")

    def open_skill(self, skill_id: str):
        """Поки що заглушка: потім тут зробимо екран навички."""
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", f"Скіл з id={skill_id} не знайдено")
            return

        messagebox.showinfo("Навичка", f"Тут буде екран навички: {skill.get('name', '???')}")

        # Пізніше замість messagebox будемо:
        # self.build_skill_screen(skill_id)


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
