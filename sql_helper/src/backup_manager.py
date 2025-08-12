import customtkinter as ctk
from tkinter import filedialog, messagebox
import subprocess
import os
import json
from datetime import datetime, timedelta
import threading
import schedule
import time


class BackupManager(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Резервное копирование")
        self.geometry("800x700")
        self.parent = parent

        # Планировщик бэкапов
        self.backup_scheduler = BackupScheduler(self)

        self.create_widgets()
        self.load_backup_history()

    def create_widgets(self):
        # === Заголовок ===
        ctk.CTkLabel(self, text="Резервное копирование баз данных",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # === Создание дампа ===
        backup_frame = ctk.CTkFrame(self)
        backup_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(backup_frame, text="Создание дампа:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Настройки дампа
        settings_frame = ctk.CTkFrame(backup_frame)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Имя файла дампа
        filename_frame = ctk.CTkFrame(settings_frame)
        filename_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(filename_frame, text="Имя файла:").pack(side="left", padx=5)
        self.filename_entry = ctk.CTkEntry(filename_frame)
        self.filename_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.filename_entry.insert(0, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}")

        # Формат файла
        format_frame = ctk.CTkFrame(settings_frame)
        format_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(format_frame, text="Формат:").pack(side="left", padx=5)
        self.format_var = ctk.StringVar(value="sql")
        ctk.CTkComboBox(format_frame, values=["sql", "gz"],
                        variable=self.format_var).pack(side="left", padx=5)

        # Опции дампа
        options_frame = ctk.CTkFrame(settings_frame)
        options_frame.pack(fill="x", pady=5)

        self.structure_only_var = ctk.BooleanVar()
        ctk.CTkCheckBox(options_frame, text="Только структура",
                        variable=self.structure_only_var).pack(side="left", padx=10)

        self.data_only_var = ctk.BooleanVar()
        ctk.CTkCheckBox(options_frame, text="Только данные",
                        variable=self.data_only_var).pack(side="left", padx=10)

        # Кнопка создания дампа
        ctk.CTkButton(backup_frame, text="Создать дамп",
                      command=self.create_backup,
                      fg_color="green").pack(pady=10)

        # === Восстановление из дампа ===
        restore_frame = ctk.CTkFrame(self)
        restore_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(restore_frame, text="Восстановление из дампа:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Выбор файла для восстановления
        file_select_frame = ctk.CTkFrame(restore_frame)
        file_select_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(file_select_frame, text="Файл дампа:").pack(side="left", padx=5)
        self.restore_file_entry = ctk.CTkEntry(file_select_frame)
        self.restore_file_entry.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(file_select_frame, text="Обзор...",
                      command=self.browse_restore_file).pack(side="left", padx=5)

        # Предупреждение
        ctk.CTkLabel(restore_frame, text="⚠ ВНИМАНИЕ: Восстановление перезапишет текущие данные!",
                     text_color="red").pack(pady=5)

        # Кнопка восстановления
        ctk.CTkButton(restore_frame, text="Восстановить из дампа",
                      command=self.restore_backup,
                      fg_color="orange").pack(pady=10)

        # === Планирование бэкапов ===
        schedule_frame = ctk.CTkFrame(self)
        schedule_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(schedule_frame, text="Планирование бэкапов:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Настройки расписания
        schedule_settings_frame = ctk.CTkFrame(schedule_frame)
        schedule_settings_frame.pack(fill="x", padx=10, pady=5)

        # Интервал
        interval_frame = ctk.CTkFrame(schedule_settings_frame)
        interval_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(interval_frame, text="Интервал:").pack(side="left", padx=5)
        self.interval_var = ctk.StringVar(value="daily")
        ctk.CTkComboBox(interval_frame, values=["hourly", "daily", "weekly"],
                        variable=self.interval_var).pack(side="left", padx=5)

        # Время выполнения
        time_frame = ctk.CTkFrame(schedule_settings_frame)
        time_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(time_frame, text="Время:").pack(side="left", padx=5)
        self.time_entry = ctk.CTkEntry(time_frame, placeholder_text="HH:MM")
        self.time_entry.pack(side="left", padx=5)
        self.time_entry.insert(0, "02:00")

        # Папка для бэкапов
        folder_frame = ctk.CTkFrame(schedule_settings_frame)
        folder_frame.pack(fill="x", pady=2)

        ctk.CTkLabel(folder_frame, text="Папка:").pack(side="left", padx=5)
        self.backup_folder_entry = ctk.CTkEntry(folder_frame)
        self.backup_folder_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.backup_folder_entry.insert(0, "./backups")

        # Кнопки управления расписанием
        schedule_buttons_frame = ctk.CTkFrame(schedule_frame)
        schedule_buttons_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(schedule_buttons_frame, text="Запланировать",
                      command=self.schedule_backup).pack(side="left", padx=5)
        ctk.CTkButton(schedule_buttons_frame, text="Остановить",
                      command=self.stop_scheduled_backups,
                      fg_color="red").pack(side="left", padx=5)

        self.schedule_status_label = ctk.CTkLabel(schedule_buttons_frame, text="Статус: Не запланирован")
        self.schedule_status_label.pack(side="left", padx=10)

        # === История бэкапов ===
        history_frame = ctk.CTkFrame(self)
        history_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(history_frame, text="История бэкапов:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Таблица истории
        self.history_tree = ctk.CTkScrollableFrame(history_frame)
        self.history_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Кнопки управления историей
        history_buttons_frame = ctk.CTkFrame(history_frame)
        history_buttons_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(history_buttons_frame, text="Обновить",
                      command=self.load_backup_history).pack(side="left", padx=5)
        ctk.CTkButton(history_buttons_frame, text="Очистить историю",
                      command=self.clear_backup_history,
                      fg_color="red").pack(side="left", padx=5)

    def create_backup(self):
        """Создание дампа базы данных"""
        if not self.parent.db:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        try:
            # Получаем настройки
            filename = self.filename_entry.get().strip()
            if not filename:
                filename = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

            format_ext = self.format_var.get()
            if not filename.endswith(f".{format_ext}"):
                filename += f".{format_ext}"

            # Создаем папку для бэкапов
            backup_dir = "./backups"
            os.makedirs(backup_dir, exist_ok=True)

            filepath = os.path.join(backup_dir, filename)

            # Формируем команду mysqldump
            cmd = [
                "mysqldump",
                f"--host={self.parent.db.host}",
                f"--user={self.parent.db.user}",
                f"--password={self.parent.db.password}",
                self.parent.db.database
            ]

            # Добавляем опции
            if self.structure_only_var.get():
                cmd.append("--no-data")
            if self.data_only_var.get():
                cmd.append("--no-create-info")

            # Выполняем команду
            with open(filepath, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                # Сохраняем в историю
                self.save_backup_record(filepath, "Создан")
                messagebox.showinfo("Успех", f"Дамп успешно создан:\n{filepath}")
                self.load_backup_history()
            else:
                messagebox.showerror("Ошибка", f"Ошибка создания дампа:\n{result.stderr}")

        except FileNotFoundError:
            messagebox.showerror("Ошибка", "mysqldump не найден. Убедитесь, что MySQL установлен и доступен в PATH")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка создания дампа:\n{str(e)}")

    def browse_restore_file(self):
        """Выбор файла для восстановления"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл дампа",
            filetypes=[
                ("SQL файлы", "*.sql"),
                ("GZ файлы", "*.gz"),
                ("Все файлы", "*.*")
            ]
        )

        if file_path:
            self.restore_file_entry.delete(0, "end")
            self.restore_file_entry.insert(0, file_path)

    def restore_backup(self):
        """Восстановление из дампа"""
        if not self.parent.db:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        filepath = self.restore_file_entry.get().strip()
        if not filepath:
            messagebox.showerror("Ошибка", "Выберите файл дампа")
            return

        if not os.path.exists(filepath):
            messagebox.showerror("Ошибка", "Файл дампа не найден")
            return

        # Подтверждение
        if not messagebox.askyesno("Подтверждение",
                                   "Восстановление перезапишет текущие данные!\nПродолжить?"):
            return

        try:
            # Формируем команду mysql
            cmd = [
                "mysql",
                f"--host={self.parent.db.host}",
                f"--user={self.parent.db.user}",
                f"--password={self.parent.db.password}",
                self.parent.db.database
            ]

            # Выполняем команду
            with open(filepath, 'r') as f:
                result = subprocess.run(cmd, stdin=f, stderr=subprocess.PIPE, text=True)

            if result.returncode == 0:
                # Сохраняем в историю
                self.save_backup_record(filepath, "Восстановлен")
                messagebox.showinfo("Успех", "Данные успешно восстановлены из дампа")
                self.load_backup_history()
            else:
                messagebox.showerror("Ошибка", f"Ошибка восстановления:\n{result.stderr}")

        except FileNotFoundError:
            messagebox.showerror("Ошибка", "mysql не найден. Убедитесь, что MySQL установлен и доступен в PATH")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка восстановления:\n{str(e)}")

    def schedule_backup(self):
        """Запланировать бэкапы"""
        try:
            interval = self.interval_var.get()
            time_str = self.time_entry.get().strip()
            backup_folder = self.backup_folder_entry.get().strip()

            if not time_str:
                messagebox.showerror("Ошибка", "Введите время выполнения")
                return

            # Проверяем формат времени
            try:
                datetime.strptime(time_str, "%H:%M")
            except ValueError:
                messagebox.showerror("Ошибка", "Неверный формат времени. Используйте HH:MM")
                return

            # Создаем папку для бэкапов
            os.makedirs(backup_folder, exist_ok=True)

            # Запускаем планировщик
            self.backup_scheduler.start(interval, time_str, backup_folder)
            self.schedule_status_label.configure(text="Статус: Запланирован", text_color="green")

            messagebox.showinfo("Успех", f"Бэкапы запланированы на {interval} в {time_str}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка планирования:\n{str(e)}")

    def stop_scheduled_backups(self):
        """Остановить запланированные бэкапы"""
        self.backup_scheduler.stop()
        self.schedule_status_label.configure(text="Статус: Остановлен", text_color="red")
        messagebox.showinfo("Успех", "Запланированные бэкапы остановлены")

    def save_backup_record(self, filepath, action):
        """Сохранить запись о бэкапе в историю"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "filepath": filepath,
            "action": action,
            "size": os.path.getsize(filepath) if os.path.exists(filepath) else 0
        }

        # Загружаем существующую историю
        history = self.load_backup_history_from_file()
        history.append(record)

        # Сохраняем (оставляем последние 100 записей)
        history = history[-100:]

        with open("backup_history.json", "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=2)

    def load_backup_history_from_file(self):
        """Загрузить историю бэкапов из файла"""
        if os.path.exists("backup_history.json"):
            try:
                with open("backup_history.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return []
        return []

    def load_backup_history(self):
        """Загрузить и отобразить историю бэкапов"""
        # Очищаем предыдущее содержимое
        for widget in self.history_tree.winfo_children():
            widget.destroy()

        # Создаем заголовки
        header_frame = ctk.CTkFrame(self.history_tree)
        header_frame.pack(fill="x", padx=2, pady=1)

        ctk.CTkLabel(header_frame, text="Время", font=ctk.CTkFont(weight="bold"), width=150).pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="Файл", font=ctk.CTkFont(weight="bold"), width=200).pack(side="left", padx=2)
        ctk.CTkLabel(header_frame, text="Действие", font=ctk.CTkFont(weight="bold"), width=100).pack(side="left",
                                                                                                     padx=2)
        ctk.CTkLabel(header_frame, text="Размер", font=ctk.CTkFont(weight="bold"), width=100).pack(side="left", padx=2)

        # Загружаем историю
        history = self.load_backup_history_from_file()

        # Отображаем записи (в обратном порядке - новые сверху)
        for record in reversed(history):
            try:
                timestamp = datetime.fromisoformat(record["timestamp"]).strftime("%Y-%m-%d %H:%M:%S")
                filepath = os.path.basename(record["filepath"])
                action = record["action"]
                size = self.format_file_size(record["size"])

                row_frame = ctk.CTkFrame(self.history_tree)
                row_frame.pack(fill="x", padx=2, pady=1)

                ctk.CTkLabel(row_frame, text=timestamp, width=150).pack(side="left", padx=2)
                ctk.CTkLabel(row_frame, text=filepath, width=200).pack(side="left", padx=2)
                ctk.CTkLabel(row_frame, text=action, width=100).pack(side="left", padx=2)
                ctk.CTkLabel(row_frame, text=size, width=100).pack(side="left", padx=2)

            except Exception as e:
                print(f"Ошибка отображения записи: {e}")

    def clear_backup_history(self):
        """Очистить историю бэкапов"""
        if messagebox.askyesno("Подтверждение", "Очистить историю бэкапов?"):
            try:
                if os.path.exists("backup_history.json"):
                    os.remove("backup_history.json")
                self.load_backup_history()
                messagebox.showinfo("Успех", "История бэкапов очищена")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка очистки истории:\n{str(e)}")

    def format_file_size(self, size_bytes):
        """Форматирование размера файла"""
        if size_bytes == 0:
            return "0 B"
        elif size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class BackupScheduler:
    def __init__(self, parent):
        self.parent = parent
        self.running = False
        self.thread = None

    def start(self, interval, time_str, backup_folder):
        """Запустить планировщик"""
        self.running = True
        self.thread = threading.Thread(target=self.run_scheduler,
                                       args=(interval, time_str, backup_folder),
                                       daemon=True)
        self.thread.start()

    def stop(self):
        """Остановить планировщик"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=1)

    def run_scheduler(self, interval, time_str, backup_folder):
        """Основной цикл планировщика"""
        try:
            # Настраиваем расписание
            if interval == "hourly":
                schedule.every().hour.at(time_str).do(self.create_scheduled_backup, backup_folder)
            elif interval == "daily":
                schedule.every().day.at(time_str).do(self.create_scheduled_backup, backup_folder)
            elif interval == "weekly":
                schedule.every().week.at(time_str).do(self.create_scheduled_backup, backup_folder)

            # Основной цикл
            while self.running:
                schedule.run_pending()
                time.sleep(60)  # Проверяем каждую минуту

        except Exception as e:
            print(f"Ошибка планировщика: {e}")

    def create_scheduled_backup(self, backup_folder):
        """Создать запланированный бэкап"""
        try:
            # Генерируем имя файла
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"scheduled_backup_{timestamp}.sql"
            filepath = os.path.join(backup_folder, filename)

            # Здесь должна быть логика создания бэкапа
            # Пока просто создаем тестовый файл
            with open(filepath, 'w') as f:
                f.write(f"-- Scheduled backup created at {datetime.now()}\n")
                f.write("-- This is a placeholder for actual backup\n")

            # Сохраняем в историю
            self.parent.save_backup_record(filepath, "Запланирован")

            print(f"Запланированный бэкап создан: {filepath}")

        except Exception as e:
            print(f"Ошибка создания запланированного бэкапа: {e}")


# Глобальный экземпляр менеджера бэкапов
backup_manager = None


def get_backup_manager(parent):
    """Получение или создание глобального экземпляра менеджера бэкапов"""
    global backup_manager
    if backup_manager is None or not backup_manager.winfo_exists():
        backup_manager = BackupManager(parent)
    else:
        backup_manager.lift()
    return backup_manager
