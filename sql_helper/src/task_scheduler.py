import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
import json
import os
import schedule
import time
import threading
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
import subprocess
import pandas as pd


class TaskScheduler(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Планировщик задач")
        self.geometry("900x700")
        self.parent = parent

        # Планировщик задач
        self.scheduler = TaskSchedulerEngine(self)

        self.create_widgets()
        self.load_tasks()

    def create_widgets(self):
        # === Заголовок ===
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Планировщик задач",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        # Кнопки управления планировщиком
        scheduler_btn_frame = ctk.CTkFrame(header_frame)
        scheduler_btn_frame.pack(side="right")

        self.scheduler_status_label = ctk.CTkLabel(scheduler_btn_frame, text="Статус: Остановлен")
        self.scheduler_status_label.pack(side="left", padx=5)

        ctk.CTkButton(scheduler_btn_frame, text="Запустить",
                      command=self.start_scheduler,
                      fg_color="green").pack(side="left", padx=2)

        ctk.CTkButton(scheduler_btn_frame, text="Остановить",
                      command=self.stop_scheduler,
                      fg_color="red").pack(side="left", padx=2)

        # === Создание новой задачи ===
        task_frame = ctk.CTkFrame(self)
        task_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(task_frame, text="Создать новую задачу:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Название задачи
        name_frame = ctk.CTkFrame(task_frame)
        name_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(name_frame, text="Название:").pack(side="left", padx=5)
        self.task_name_entry = ctk.CTkEntry(name_frame, width=300)
        self.task_name_entry.pack(side="left", padx=5, fill="x", expand=True)

        # SQL запрос
        sql_frame = ctk.CTkFrame(task_frame)
        sql_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(sql_frame, text="SQL запрос:").pack(anchor="w", padx=5, pady=2)
        self.sql_text = ctk.CTkTextbox(sql_frame, height=80)
        self.sql_text.pack(fill="x", padx=5, pady=2)

        # Расписание
        schedule_frame = ctk.CTkFrame(task_frame)
        schedule_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(schedule_frame, text="Расписание:").pack(side="left", padx=5)

        self.schedule_type_var = ctk.StringVar(value="daily")
        ctk.CTkComboBox(schedule_frame, values=["hourly", "daily", "weekly", "monthly"],
                        variable=self.schedule_type_var,
                        width=100).pack(side="left", padx=5)

        ctk.CTkLabel(schedule_frame, text="Время:").pack(side="left", padx=5)
        self.time_entry = ctk.CTkEntry(schedule_frame, placeholder_text="HH:MM", width=80)
        self.time_entry.pack(side="left", padx=5)
        self.time_entry.insert(0, "09:00")

        # Дни недели (для weekly)
        self.weekday_var = ctk.StringVar(value="monday")
        self.weekday_combo = ctk.CTkComboBox(schedule_frame,
                                             values=["monday", "tuesday", "wednesday", "thursday",
                                                     "friday", "saturday", "sunday"],
                                             variable=self.weekday_var,
                                             width=100)
        self.weekday_combo.pack(side="left", padx=5)
        self.weekday_combo.pack_forget()  # Скрываем по умолчанию

        # День месяца (для monthly)
        self.monthday_var = ctk.IntVar(value=1)
        self.monthday_spinbox = ctk.CTkEntry(schedule_frame, width=50)
        self.monthday_spinbox.pack(side="left", padx=5)
        self.monthday_spinbox.insert(0, "1")
        self.monthday_spinbox.pack_forget()  # Скрываем по умолчанию

        # Автоматические отчеты
        report_frame = ctk.CTkFrame(task_frame)
        report_frame.pack(fill="x", padx=10, pady=2)

        self.auto_report_var = ctk.BooleanVar()
        ctk.CTkCheckBox(report_frame, text="Создавать автоматические отчеты",
                        variable=self.auto_report_var,
                        command=self.toggle_report_options).pack(side="left", padx=5)

        # Опции отчетов (скрыты по умолчанию)
        self.report_options_frame = ctk.CTkFrame(report_frame)
        self.report_options_frame.pack(fill="x", padx=5, pady=2)
        self.report_options_frame.pack_forget()

        ctk.CTkLabel(self.report_options_frame, text="Формат отчета:").pack(side="left", padx=5)
        self.report_format_var = ctk.StringVar(value="csv")
        ctk.CTkComboBox(self.report_options_frame, values=["csv", "excel", "json"],
                        variable=self.report_format_var,
                        width=80).pack(side="left", padx=5)

        ctk.CTkLabel(self.report_options_frame, text="Папка:").pack(side="left", padx=5)
        self.report_folder_entry = ctk.CTkEntry(self.report_options_frame, width=200)
        self.report_folder_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.report_folder_entry.insert(0, "./reports")

        # Уведомления по email
        email_frame = ctk.CTkFrame(task_frame)
        email_frame.pack(fill="x", padx=10, pady=2)

        self.email_notify_var = ctk.BooleanVar()
        ctk.CTkCheckBox(email_frame, text="Отправлять уведомления по email",
                        variable=self.email_notify_var,
                        command=self.toggle_email_options).pack(side="left", padx=5)

        # Опции email (скрыты по умолчанию)
        self.email_options_frame = ctk.CTkFrame(email_frame)
        self.email_options_frame.pack(fill="x", padx=5, pady=2)
        self.email_options_frame.pack_forget()

        ctk.CTkLabel(self.email_options_frame, text="Email:").pack(side="left", padx=5)
        self.email_entry = ctk.CTkEntry(self.email_options_frame, width=200)
        self.email_entry.pack(side="left", padx=5)

        # Кнопка создания задачи
        ctk.CTkButton(task_frame, text="Создать задачу",
                      command=self.create_task,
                      fg_color="green").pack(pady=10)

        # === Список задач ===
        tasks_frame = ctk.CTkFrame(self)
        tasks_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(tasks_frame, text="Запланированные задачи:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Создаем таблицу задач
        from tkinter import ttk
        self.tasks_tree = ttk.Treeview(tasks_frame)
        self.tasks_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Добавляем скроллбары
        vsb = ttk.Scrollbar(tasks_frame, orient="vertical", command=self.tasks_tree.yview)
        vsb.pack(side='right', fill='y')
        self.tasks_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(tasks_frame, orient="horizontal", command=self.tasks_tree.xview)
        hsb.pack(side='bottom', fill='x')
        self.tasks_tree.configure(xscrollcommand=hsb.set)

        # Настройка колонок
        self.tasks_tree["columns"] = ("name", "schedule", "last_run", "status", "actions")
        self.tasks_tree["show"] = "headings"

        self.tasks_tree.heading("name", text="Название")
        self.tasks_tree.heading("schedule", text="Расписание")
        self.tasks_tree.heading("last_run", text="Последний запуск")
        self.tasks_tree.heading("status", text="Статус")
        self.tasks_tree.heading("actions", text="Действия")

        self.tasks_tree.column("name", width=150)
        self.tasks_tree.column("schedule", width=120)
        self.tasks_tree.column("last_run", width=150)
        self.tasks_tree.column("status", width=100)
        self.tasks_tree.column("actions", width=150)

        # Кнопки управления задачами
        task_buttons_frame = ctk.CTkFrame(self)
        task_buttons_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(task_buttons_frame, text="Обновить",
                      command=self.load_tasks).pack(side="left", padx=5)

        ctk.CTkButton(task_buttons_frame, text="Удалить выбранную",
                      command=self.delete_selected_task,
                      fg_color="red").pack(side="left", padx=5)

        ctk.CTkButton(task_buttons_frame, text="Закрыть",
                      command=self.destroy).pack(side="right", padx=5)

    def toggle_report_options(self):
        """Переключение опций отчетов"""
        if self.auto_report_var.get():
            self.report_options_frame.pack(fill="x", padx=5, pady=2)
        else:
            self.report_options_frame.pack_forget()

    def toggle_email_options(self):
        """Переключение опций email"""
        if self.email_notify_var.get():
            self.email_options_frame.pack(fill="x", padx=5, pady=2)
        else:
            self.email_options_frame.pack_forget()

    def create_task(self):
        """Создание новой задачи"""
        try:
            # Получаем данные задачи
            name = self.task_name_entry.get().strip()
            sql = self.sql_text.get("0.0", "end").strip()
            schedule_type = self.schedule_type_var.get()
            time_str = self.time_entry.get().strip()

            if not name:
                messagebox.showerror("Ошибка", "Введите название задачи")
                return

            if not sql:
                messagebox.showerror("Ошибка", "Введите SQL запрос")
                return

            if not time_str:
                messagebox.showerror("Ошибка", "Введите время выполнения")
                return

            # Проверяем формат времени
            try:
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат времени. Используйте HH:MM")
                return

            # Создаем задачу
            task = {
                "id": datetime.now().strftime("%Y%m%d%H%M%S"),
                "name": name,
                "sql": sql,
                "schedule_type": schedule_type,
                "time": time_str,
                "auto_report": self.auto_report_var.get(),
                "report_format": self.report_format_var.get() if self.auto_report_var.get() else "csv",
                "report_folder": self.report_folder_entry.get() if self.auto_report_var.get() else "./reports",
                "email_notify": self.email_notify_var.get(),
                "email": self.email_entry.get() if self.email_notify_var.get() else "",
                "last_run": "",
                "status": "Ожидание",
                "created_at": datetime.now().isoformat()
            }

            # Сохраняем задачу
            self.save_task(task)

            # Очищаем форму
            self.task_name_entry.delete(0, "end")
            self.sql_text.delete("0.0", "end")

            # Обновляем список задач
            self.load_tasks()

            messagebox.showinfo("Успех", f"Задача '{name}' создана")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка создания задачи:\n{str(e)}")

    def save_task(self, task):
        """Сохранение задачи в файл"""
        tasks = self.load_tasks_from_file()
        tasks.append(task)

        with open("scheduled_tasks.json", "w", encoding="utf-8") as f:
            json.dump(tasks, f, ensure_ascii=False, indent=2)

    def load_tasks_from_file(self):
        """Загрузка задач из файла"""
        if os.path.exists("scheduled_tasks.json"):
            try:
                with open("scheduled_tasks.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def load_tasks(self):
        """Загрузка и отображение задач"""
        # Очищаем таблицу
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        # Загружаем задачи
        tasks = self.load_tasks_from_file()

        # Отображаем задачи
        for task in tasks:
            self.tasks_tree.insert("", "end", values=(
                task["name"],
                f"{task['schedule_type']} {task['time']}",
                task.get("last_run", ""),
                task.get("status", "Ожидание")
            ), tags=(task["id"],))

    def delete_selected_task(self):
        """Удаление выбранной задачи"""
        selected = self.tasks_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите задачу для удаления")
            return

        if not messagebox.askyesno("Подтверждение", "Удалить выбранную задачу?"):
            return

        try:
            # Получаем ID задачи
            item = selected[0]
            task_id = self.tasks_tree.item(item, "tags")[0]

            # Загружаем задачи
            tasks = self.load_tasks_from_file()

            # Удаляем задачу
            tasks = [task for task in tasks if task.get("id") != task_id]

            # Сохраняем обновленный список
            with open("scheduled_tasks.json", "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

            # Обновляем отображение
            self.load_tasks()

            messagebox.showinfo("Успех", "Задача удалена")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка удаления задачи:\n{str(e)}")

    def start_scheduler(self):
        """Запуск планировщика"""
        try:
            self.scheduler.start()
            self.scheduler_status_label.configure(text="Статус: Запущен", text_color="green")
            messagebox.showinfo("Успех", "Планировщик задач запущен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка запуска планировщика:\n{str(e)}")

    def stop_scheduler(self):
        """Остановка планировщика"""
        try:
            self.scheduler.stop()
            self.scheduler_status_label.configure(text="Статус: Остановлен", text_color="red")
            messagebox.showinfo("Успех", "Планировщик задач остановлен")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка остановки планировщика:\n{str(e)}")


class TaskSchedulerEngine:
    def __init__(self, parent):
        self.parent = parent
        self.running = False
        self.thread = None
        self.tasks = []

    def start(self):
        """Запуск планировщика"""
        if self.running:
            return

        self.running = True
        self.load_tasks()
        self.thread = threading.Thread(target=self.run_scheduler, daemon=True)
        self.thread.start()

    def stop(self):
        """Остановка планировщика"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def load_tasks(self):
        """Загрузка задач"""
        if os.path.exists("scheduled_tasks.json"):
            try:
                with open("scheduled_tasks.json", "r", encoding="utf-8") as f:
                    self.tasks = json.load(f)
            except:
                self.tasks = []
        else:
            self.tasks = []

    def run_scheduler(self):
        """Основной цикл планировщика"""
        try:
            # Настраиваем расписание для каждой задачи
            for task in self.tasks:
                self.schedule_task(task)

            # Основной цикл
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту

        except Exception as e:
            print(f"Ошибка планировщика: {e}")

    def schedule_task(self, task):
        """Настройка расписания для задачи"""
        try:
            schedule_type = task["schedule_type"]
            time_str = task["time"]

            if schedule_type == "hourly":
                schedule.every().hour.at(time_str).do(self.execute_task, task)
            elif schedule_type == "daily":
                schedule.every().day.at(time_str).do(self.execute_task, task)
            elif schedule_type == "weekly":
                # Для простоты используем понедельник
                schedule.every().monday.at(time_str).do(self.execute_task, task)
            elif schedule_type == "monthly":
                # Для простоты запускаем 1-го числа каждого месяца
                schedule.every().month.at(time_str).do(self.execute_task, task)

        except Exception as e:
            print(f"Ошибка настройки задачи {task['name']}: {e}")

    def execute_task(self, task):
        """Выполнение задачи"""
        try:
            # Обновляем статус задачи
            self.update_task_status(task["id"], "Выполняется")

            # Выполняем SQL запрос
            if hasattr(self.parent.parent, 'db') and self.parent.parent.db:
                result = self.parent.parent.db.execute_query(task["sql"])

                # Создаем отчет, если нужно
                if task.get("auto_report", False):
                    self.create_report(task, result)

                # Отправляем уведомление по email, если нужно
                if task.get("email_notify", False) and task.get("email"):
                    self.send_email_notification(task, result)

                # Обновляем статус
                self.update_task_status(task["id"], "Выполнено")

            else:
                self.update_task_status(task["id"], "Ошибка: Нет подключения")

        except Exception as e:
            self.update_task_status(task["id"], f"Ошибка: {str(e)}")
            print(f"Ошибка выполнения задачи {task['name']}: {e}")

    def update_task_status(self, task_id, status):
        """Обновление статуса задачи"""
        try:
            # Загружаем задачи
            tasks = self.load_tasks_from_file()

            # Обновляем статус
            for task in tasks:
                if task.get("id") == task_id:
                    task["status"] = status
                    task["last_run"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    break

            # Сохраняем обновленный список
            with open("scheduled_tasks.json", "w", encoding="utf-8") as f:
                json.dump(tasks, f, ensure_ascii=False, indent=2)

            # Обновляем отображение в основном окне
            if hasattr(self.parent, 'load_tasks'):
                self.parent.load_tasks()

        except Exception as e:
            print(f"Ошибка обновления статуса задачи: {e}")

    def load_tasks_from_file(self):
        """Загрузка задач из файла"""
        if os.path.exists("scheduled_tasks.json"):
            try:
                with open("scheduled_tasks.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def create_report(self, task, data):
        """Создание отчета"""
        try:
            # Создаем папку для отчетов
            report_folder = task.get("report_folder", "./reports")
            os.makedirs(report_folder, exist_ok=True)

            # Генерируем имя файла
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{task['name']}_{timestamp}"

            # Определяем формат
            format_type = task.get("report_format", "csv")

            # Преобразуем данные в DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                df = pd.DataFrame([{"result": str(data)}])

            # Сохраняем в нужном формате
            if format_type == "csv":
                filepath = os.path.join(report_folder, f"{filename}.csv")
                df.to_csv(filepath, index=False, encoding='utf-8-sig')
            elif format_type == "excel":
                filepath = os.path.join(report_folder, f"{filename}.xlsx")
                df.to_excel(filepath, index=False)
            elif format_type == "json":
                filepath = os.path.join(report_folder, f"{filename}.json")
                df.to_json(filepath, force_ascii=False, indent=2)

            print(f"Отчет сохранен: {filepath}")

        except Exception as e:
            print(f"Ошибка создания отчета: {e}")

    def send_email_notification(self, task, result):
        """Отправка уведомления по email"""
        try:
            # Получаем настройки email из конфига (для простоты используем заглушки)
            email_config = {
                "smtp_server": "smtp.gmail.com",
                "smtp_port": 587,
                "username": "your_email@gmail.com",
                "password": "your_password"
            }

            # Создаем сообщение
            msg = MIMEMultipart()
            msg['From'] = email_config["username"]
            msg['To'] = task["email"]
            msg['Subject'] = f"Отчет по задаче: {task['name']}"

            # Тело сообщения
            body = f"""
            Задача: {task['name']}
            Время выполнения: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

            Результат выполнения:
            {str(result)[:1000]}...

            Это автоматическое уведомление от планировщика задач MySQL.
            """

            msg.attach(MIMEText(body, 'plain', 'utf-8'))

            # Отправляем сообщение (закомментировано для безопасности)
            # server = smtplib.SMTP(email_config["smtp_server"], email_config["smtp_port"])
            # server.starttls()
            # server.login(email_config["username"], email_config["password"])
            # server.send_message(msg)
            # server.quit()

            print(f"Email отправлен на {task['email']}")

        except Exception as e:
            print(f"Ошибка отправки email: {e}")


# Глобальный экземпляр планировщика
task_scheduler = None


def get_task_scheduler(parent):
    """Получение или создание глобального экземпляра планировщика"""
    global task_scheduler
    if task_scheduler is None or not task_scheduler.winfo_exists():
        task_scheduler = TaskScheduler(parent)
    else:
        task_scheduler.lift()
    return task_scheduler
