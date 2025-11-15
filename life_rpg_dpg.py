import json
import os
from datetime import date
import time

import dearpygui.dearpygui as dpg

DATA_FILE = "data.json"

DEFAULT_SKILLS = [
    {"id": "english", "name": "Англійська"},
    {"id": "french", "name": "Французька"},
    {"id": "x_growth", "name": "X (Twitter) розвиток"},
    {"id": "youtube", "name": "YouTube канал"},
    {"id": "sport", "name": "Спорт"},
    {"id": "programming", "name": "Програмування"},
]

APP_STATE = {
    "data": None,
    "current_skill_id": None,
}


# ---------- Логіка XP / рівнів / титулів ----------

def xp_to_level(xp: float) -> int:
    """Обчислюємо рівень за XP. Формула: XP ≈ 120 * level^1.6"""
    if xp <= 0:
        return 0
    level = int((xp / 120.0) ** (1.0 / 1.6))
    return min(level, 40)


def level_to_xp(level: int) -> float:
    """Скільки XP треба для певного рівня (сукупний поріг)."""
    if level <= 0:
        return 0.0
    return 120.0 * (level ** 1.6)


def cefr_from_level(level: int) -> str:
    """Грубий CEFR для мов."""
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


# ---------- Робота з data.json ----------

def create_default_data() -> dict:
    skills = []
    for s in DEFAULT_SKILLS:
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
            "xp_total": 0,
            "money_usdt": 0.0,
            "money_uah": 0.0,
            "hp_current": 100,
            "hp_max": 100,
            "avatar_path": ""
        },
        "skills": skills,
        "global_tasks": [],
        "last_daily_reset": None
    }
    return data


def load_data() -> dict:
    if not os.path.exists(DATA_FILE):
        data = create_default_data()
        save_data(data)
        return data

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = create_default_data()
        save_data(data)
        return data

    if "hero" not in data or "skills" not in data:
        data = create_default_data()
        save_data(data)

    return data


def save_data(data: dict) -> None:
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def ensure_daily_reset(data: dict) -> dict:
    """Якщо новий день — скидаємо daily_done і чистимо виконані задачі."""
    today = date.today().isoformat()
    last = data.get("last_daily_reset")

    if last != today:
        for skill in data.get("skills", []):
            skill["daily_done"] = False
            tasks = skill.get("tasks", [])
            skill["tasks"] = [t for t in tasks if not t.get("completed", False)]

        data["last_daily_reset"] = today
        save_data(data)

    return data


# ---------- Хелпери ----------

def get_skill(skill_id: str) -> dict | None:
    for s in APP_STATE["data"].get("skills", []):
        if s.get("id") == skill_id:
            return s
    return None


def get_total_xp() -> float:
    return sum(s.get("xp", 0) for s in APP_STATE["data"].get("skills", []))


def get_total_level() -> int:
    return xp_to_level(get_total_xp())


# ---------- Логіка задач / скілів ----------

def execute_task_logic(skill_id: str, task_id: str):
    data = APP_STATE["data"]
    skill = get_skill(skill_id)
    if not skill:
        return

    tasks = skill.get("tasks", [])
    task = next((t for t in tasks if t.get("id") == task_id), None)
    if not task:
        return

    if task.get("completed", False):
        return

    xp_reward = int(task.get("xp_reward", 0) or 0)
    money_usdt = float(task.get("money_usdt", 0) or 0)
    money_uah = float(task.get("money_uah", 0) or 0)

    skill["xp"] = skill.get("xp", 0) + xp_reward

    hero = data.get("hero", {})
    hero["money_usdt"] = hero.get("money_usdt", 0.0) + money_usdt
    hero["money_uah"] = hero.get("money_uah", 0.0) + money_uah

    task["completed"] = True
    skill["daily_done"] = True

    save_data(data)


def add_task_logic(skill_id: str, name: str, category: str, xp_reward: int,
                   money_usdt: float, money_uah: float):
    data = APP_STATE["data"]
    skill = get_skill(skill_id)
    if not skill:
        return

    new_task = {
        "id": f"task_{int(time.time() * 1000)}",
        "name": name,
        "category": category,
        "xp_reward": xp_reward,
        "money_usdt": money_usdt,
        "money_uah": money_uah,
        "completed": False
    }

    skill.setdefault("tasks", []).append(new_task)
    save_data(data)


def add_skill_logic(name: str, skill_type: str):
    data = APP_STATE["data"]
    new_id = f"skill_{int(time.time() * 1000)}"
    skill = {
        "id": new_id,
        "name": name,
        "type": skill_type,
        "xp": 0,
        "daily_done": False,
        "tasks": []
    }
    data.setdefault("skills", []).append(skill)
    save_data(data)
    return new_id


# ---------- DearPyGui UI ----------

def rebuild_hero_panel():
    data = APP_STATE["data"]
    hero = data.get("hero", {})
    hero_name = hero.get("name", "Hero")
    total_xp = get_total_xp()
    total_lvl = get_total_level()
    money_usdt = hero.get("money_usdt", 0.0)
    money_uah = hero.get("money_uah", 0.0)
    hp_current = hero.get("hp_current", 100)
    hp_max = hero.get("hp_max", 100)

    dpg.set_value("hero_main_text", f"Герой: {hero_name} | lvl {total_lvl} | XP: {int(total_xp)}")
    dpg.set_value("hero_hp_text", f"HP: {hp_current}/{hp_max}")
    dpg.set_value("hero_money_text", f"USDT: {money_usdt:.2f} | UAH: {money_uah:.2f}")


def rebuild_skills_panel():
    if not dpg.does_item_exist("SkillsPanel"):
        return

    dpg.delete_item("SkillsPanel", children_only=True)

    panel = "SkillsPanel"

    with dpg.group(parent=panel):
        dpg.add_text("Мої навички", bullet=False)
        dpg.add_button(label="+ Додати навичку", callback=open_add_skill_dialog)

    for skill in APP_STATE["data"].get("skills", []):
        name = skill.get("name", "???")
        xp = skill.get("xp", 0)
        lvl = xp_to_level(xp)
        title = title_for_level(lvl)

        current_xp = level_to_xp(lvl)
        next_xp = level_to_xp(lvl + 1) if lvl < 40 else level_to_xp(lvl)
        if next_xp <= current_xp:
            progress = 1.0
        else:
            progress = (xp - current_xp) / (next_xp - current_xp)
            progress = max(0.0, min(1.0, progress))

        daily_done = skill.get("daily_done", False)
        daily_text = "Сьогодні зроблено ✅" if daily_done else "Сьогодні ще нічого ❗"
        daily_color = (0, 255, 0, 255) if daily_done else (255, 160, 0, 255)

        with dpg.group(parent=panel):
            dpg.add_text(f"{name} — lvl {lvl} ({title}) | XP: {int(xp)}")
            dpg.add_progress_bar(
                default_value=progress,
                overlay=f"{int(progress * 100)}% до наступного рівня",
                width=-1
            )
            dpg.add_text(daily_text, color=daily_color)
            dpg.add_button(
                label="Відкрити",
                callback=open_skill_callback,
                user_data=skill["id"]
            )
            dpg.add_separator()


def refresh_skill_panel():
    if not dpg.does_item_exist("SkillPanel"):
        return

    dpg.delete_item("SkillPanel", children_only=True)

    skill_id = APP_STATE.get("current_skill_id")
    if not skill_id:
        dpg.add_text("Вибери навичку зліва", parent="SkillPanel")
        return

    skill = get_skill(skill_id)
    if not skill:
        dpg.add_text("Навичку не знайдено", parent="SkillPanel")
        return

    name = skill.get("name", "???")
    xp = skill.get("xp", 0)
    lvl = xp_to_level(xp)
    title = title_for_level(lvl)

    progress_current = level_to_xp(lvl)
    progress_next = level_to_xp(lvl + 1) if lvl < 40 else level_to_xp(lvl)
    if progress_next <= progress_current:
        progress_value = 1.0
    else:
        progress_value = (xp - progress_current) / (progress_next - progress_current)
        progress_value = max(0.0, min(1.0, progress_value))

    dpg.add_text(f"Навичка: {name}", parent="SkillPanel")
    dpg.add_text(f"Рівень: {lvl} ({title})   XP: {int(xp)}", parent="SkillPanel")

    if skill.get("type") == "language":
        cefr = cefr_from_level(lvl)
        dpg.add_text(f"CEFR: {cefr}", parent="SkillPanel")

    dpg.add_progress_bar(
        default_value=progress_value,
        overlay=f"{int(progress_value * 100)}% до наступного рівня",
        width=-1,
        parent="SkillPanel"
    )

    with dpg.group(parent="SkillPanel"):
        dpg.add_separator()
        dpg.add_text("Задачі:")

        dpg.add_button(
            label="+ Додати задачу",
            callback=open_add_task_dialog,
            user_data=skill_id
        )

    categories = [
        ("short", "Короткі задачі"),
        ("medium", "Середні задачі"),
        ("long", "Довготривалі задачі"),
        ("boss", "Боси"),
    ]

    tasks = skill.get("tasks", [])

    for cat_key, cat_label in categories:
        cat_tasks = [t for t in tasks if t.get("category") == cat_key]

        dpg.add_separator(parent="SkillPanel")
        dpg.add_text(cat_label, parent="SkillPanel")
        if not cat_tasks:
            dpg.add_text("  (поки немає задач)", parent="SkillPanel", color=(130, 130, 130, 255))
        else:
            for task in cat_tasks:
                task_name = task.get("name", "Без назви")
                xp_reward = task.get("xp_reward", 0)
                money_usdt = task.get("money_usdt", 0)
                money_uah = task.get("money_uah", 0)
                completed = task.get("completed", False)

                with dpg.group(parent="SkillPanel"):
                    if completed:
                        name_color = (150, 150, 150, 255)
                        prefix = "✅ "
                    else:
                        name_color = (230, 230, 230, 255)
                        prefix = "• "

                    dpg.add_text(f"{prefix}{task_name}", color=name_color)
                    dpg.add_text(
                        f"   +{xp_reward} XP | +{money_usdt} USDT | +{money_uah} UAH",
                        color=(160, 160, 160, 255)
                    )
                    dpg.add_button(
                        label="Виконати",
                        callback=execute_task_callback,
                        user_data=(skill_id, task.get("id")),
                        enabled=not completed
                    )


# ---------- Callbacks ----------

def open_skill_callback(sender, app_data, user_data):
    skill_id = user_data
    APP_STATE["current_skill_id"] = skill_id
    refresh_skill_panel()


def execute_task_callback(sender, app_data, user_data):
    skill_id, task_id = user_data
    execute_task_logic(skill_id, task_id)
    rebuild_skills_panel()
    refresh_skill_panel()
    rebuild_hero_panel()


def open_add_task_dialog(sender, app_data, user_data):
    skill_id = user_data

    with dpg.window(label="Нова задача", modal=True, autosize=True, tag="AddTaskWindow"):
        dpg.add_text("Додати задачу")
        dpg.add_input_text(label="Назва", tag="task_name_input")
        dpg.add_combo(
            label="Категорія",
            items=["short", "medium", "long", "boss"],
            default_value="short",
            tag="task_category_input"
        )
        dpg.add_input_int(label="XP нагорода", default_value=50, tag="task_xp_input")
        dpg.add_input_float(label="USDT нагорода", default_value=0.0, tag="task_usdt_input")
        dpg.add_input_float(label="UAH нагорода", default_value=0.0, tag="task_uah_input")

        def save_task_cb():
            name = dpg.get_value("task_name_input").strip()
            if not name:
                return

            category = dpg.get_value("task_category_input")
            xp_reward = int(dpg.get_value("task_xp_input"))
            money_usdt = float(dpg.get_value("task_usdt_input"))
            money_uah = float(dpg.get_value("task_uah_input"))

            add_task_logic(skill_id, name, category, xp_reward, money_usdt, money_uah)
            dpg.delete_item("AddTaskWindow")
            refresh_skill_panel()

        dpg.add_button(label="Зберегти", callback=lambda: save_task_cb())


def open_add_skill_dialog(sender, app_data, user_data=None):
    with dpg.window(label="Нова навичка", modal=True, autosize=True, tag="AddSkillWindow"):
        dpg.add_text("Додати навичку")
        dpg.add_input_text(label="Назва", tag="skill_name_input")
        dpg.add_combo(
            label="Тип",
            items=["general", "language"],
            default_value="general",
            tag="skill_type_input"
        )

        def save_skill_cb():
            name = dpg.get_value("skill_name_input").strip()
            if not name:
                return
            skill_type = dpg.get_value("skill_type_input")
            new_id = add_skill_logic(name, skill_type)
            APP_STATE["current_skill_id"] = new_id
            dpg.delete_item("AddSkillWindow")
            rebuild_skills_panel()
            refresh_skill_panel()

        dpg.add_button(label="Зберегти", callback=lambda: save_skill_cb())


# ---------- Старт вікна ----------

def build_main_window():
    dpg.create_context()

    data = load_data()
    data = ensure_daily_reset(data)
    APP_STATE["data"] = data

    dpg.create_viewport(title="RPGLife (DearPyGui)", width=1100, height=650)

    with dpg.window(tag="MainWindow", label="RPGLife", width=1080, height=630, pos=(10, 10)):
        with dpg.group(tag="HeroPanel"):
            dpg.add_text("", tag="hero_main_text")
            dpg.add_text("", tag="hero_hp_text")
            dpg.add_text("", tag="hero_money_text")
            dpg.add_separator()

        with dpg.group(horizontal=True):
            with dpg.child_window(tag="SkillsPanel", width=520, autosize_y=True):
                pass

            with dpg.child_window(tag="SkillPanel", autosize_x=True, autosize_y=True):
                dpg.add_text("Вибери навичку зліва")

    rebuild_hero_panel()
    rebuild_skills_panel()

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.set_primary_window("MainWindow", True)
    dpg.start_dearpygui()
    dpg.destroy_context()


if __name__ == "__main__":
    build_main_window()
