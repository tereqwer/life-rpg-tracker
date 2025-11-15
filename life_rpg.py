import json
import os
import math
import customtkinter as ctk
from tkinter import messagebox
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
        self.font_task = tkfont.Font(family="Segoe UI", size=9)
        self.font_task_completed = tkfont.Font(family="Segoe UI", size=9, overstrike=1)
        self.root = root
        self.root.geometry("900x550")

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


    # ---------- Допоміжні методи ----------

    def get_total_xp(self) -> float:
        """Сумарний XP героя — сума XP по всіх скілах."""
        return sum(skill.get("xp", 0) for skill in self.data.get("skills", []))

    def get_total_level(self) -> int:
        """Рахуємо загальний рівень героя з total_xp."""
        total_xp = self.get_total_xp()
        return xp_to_level(total_xp)
    
    def on_level_up(self, skill: dict, old_lvl: int, new_lvl: int):
        """Попап + звук при переході на новий рівень."""
        skill_name = skill.get("name", "Навичка")

        messagebox.showinfo(
            "Новий рівень!",
            f"Ви отримали новий рівень у '{skill_name}'!\n"
            f"{old_lvl} ➜ {new_lvl}"
        )

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
            winsound.PlaySound("lvlup.mp3", winsound.SND_FILENAME | winsound.SND_ASYNC)
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
            text=f"Рівень: {lvl} ({title})   XP: {int(xp)}",
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

        # права частина — кнопка
        btn_do = ctk.CTkButton(
            row,
            text="Виконати",
            width=100,
            command=lambda s_id=skill_id, t_id=task.get("id"): self.execute_task(s_id, t_id)
        )
        btn_do.pack(side="right", padx=5)

        if completed:
            btn_do.configure(state="disabled")


    def execute_task(self, skill_id: str, task_id: str):
        """Виконати задачу — додати XP, гроші, позначити completed."""
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

        save_data(self.data)

        # Перебудовуємо екран
        self.build_main_screen()


    def open_add_task_dialog(self, skill_id: str):
        """Невелике вікно для створення нової задачі (CustomTkinter)."""
        skill = next((s for s in self.data.get("skills", []) if s.get("id") == skill_id), None)
        if not skill:
            messagebox.showerror("Помилка", "Скіл не знайдено")
            return

        win = ctk.CTkToplevel(self.root)
        win.title("Нова задача")
        win.grab_set()
        win.geometry("380x260")

        frame = ctk.CTkFrame(win, corner_radius=10)
        frame.pack(fill="both", expand=True, padx=15, pady=15)

        # Назва
        ctk.CTkLabel(frame, text="Назва задачі:").grid(row=0, column=0, sticky="w")
        entry_name = ctk.CTkEntry(frame, width=200)
        entry_name.grid(row=0, column=1, sticky="w", padx=(8, 0))

        # Категорія
        ctk.CTkLabel(frame, text="Категорія:").grid(row=1, column=0, sticky="w", pady=(8, 0))
        cat_var = ctk.StringVar(value="short")
        combo_cat = ctk.CTkComboBox(
            frame,
            variable=cat_var,
            values=["short", "medium", "long", "boss"],
            width=120
        )
        combo_cat.grid(row=1, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        # XP
        ctk.CTkLabel(frame, text="XP нагорода:").grid(row=2, column=0, sticky="w", pady=(8, 0))
        entry_xp = ctk.CTkEntry(frame, width=80)
        entry_xp.insert(0, "50")
        entry_xp.grid(row=2, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        # USDT
        ctk.CTkLabel(frame, text="USDT нагорода:").grid(row=3, column=0, sticky="w", pady=(8, 0))
        entry_usdt = ctk.CTkEntry(frame, width=80)
        entry_usdt.insert(0, "0")
        entry_usdt.grid(row=3, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

        # UAH
        ctk.CTkLabel(frame, text="UAH нагорода:").grid(row=4, column=0, sticky="w", pady=(8, 0))
        entry_uah = ctk.CTkEntry(frame, width=80)
        entry_uah.insert(0, "0")
        entry_uah.grid(row=4, column=1, sticky="w", padx=(8, 0), pady=(8, 0))

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
                "completed": False,
            }

            skill.setdefault("tasks", []).append(new_task)
            save_data(self.data)
            win.destroy()
            # оновлюємо екран навички, щоб нова задача зʼявилась
            self.build_skill_screen(skill_id)

        btn_save = ctk.CTkButton(frame, text="Зберегти", command=on_save)
        btn_save.grid(row=5, column=0, columnspan=2, pady=(15, 0))

        # щоб форма не зʼїжджала
        for i in range(2):
            frame.grid_columnconfigure(i, weight=1)



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