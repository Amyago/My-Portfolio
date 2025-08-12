import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
from database import MySQLConnector
import pandas as pd
import os
import json
import sqlparse
from query_builder import QueryBuilder
from query_monitor import get_query_monitor
import time
from data_importer import DataImporter
from backup_manager import get_backup_manager
from schema_comparator import get_schema_comparator
from table_editor import get_table_editor
from data_visualizer import get_data_visualizer
from task_scheduler import get_task_scheduler
from multi_table_editor import get_multi_table_editor
from cloud_integration import get_cloud_integration

class SQLTextWidget(ctk.CTkTextbox):
    """Текстовый виджет с подсветкой синтаксиса SQL"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sql_keywords = [
            'SELECT', 'FROM', 'WHERE', 'INSERT', 'UPDATE', 'DELETE',
            'CREATE', 'DROP', 'ALTER', 'TABLE', 'DATABASE', 'INDEX',
            'PRIMARY', 'KEY', 'FOREIGN', 'REFERENCES', 'CONSTRAINT',
            'UNIQUE', 'NOT', 'NULL', 'DEFAULT', 'AUTO_INCREMENT',
            'INT', 'VARCHAR', 'TEXT', 'DATE', 'DATETIME', 'BOOLEAN',
            'AND', 'OR', 'LIKE', 'IN', 'BETWEEN', 'ORDER', 'BY',
            'GROUP', 'HAVING', 'LIMIT', 'OFFSET', 'JOIN', 'INNER',
            'LEFT', 'RIGHT', 'OUTER', 'ON', 'AS', 'DISTINCT',
            'COUNT', 'SUM', 'AVG', 'MIN', 'MAX', 'CASE', 'WHEN',
            'THEN', 'ELSE', 'END', 'IF', 'EXISTS', 'SHOW', 'DESCRIBE'
        ]

    def highlight_syntax(self):
        """Базовая подсветка синтаксиса"""
        content = self.get("1.0", "end-1c")
        # Очищаем предыдущую подсветку
        self.tag_remove("keyword", "1.0", "end")
        self.tag_remove("string", "1.0", "end")
        self.tag_remove("comment", "1.0", "end")

        # Создаем теги для подсветки
        self.tag_config("keyword", foreground="#569CD6", font=ctk.CTkFont(weight="bold"))
        self.tag_config("string", foreground="#CE9178")
        self.tag_config("comment", foreground="#6A9955", font=ctk.CTkFont(slant="italic"))

        # Подсвечиваем ключевые слова
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            words = line.split()
            pos = 0
            for word in words:
                clean_word = word.upper().strip('(),;')
                if clean_word in self.sql_keywords:
                    start_pos = line.find(word, pos)
                    if start_pos != -1:
                        start_index = f"{i}.{start_pos}"
                        end_index = f"{i}.{start_pos + len(word)}"
                        self.tag_add("keyword", start_index, end_index)
                pos = line.find(word, pos) + len(word)


class ResultsWindow(ctk.CTkToplevel):
    """Отдельное окно для отображения результатов"""

    def __init__(self, parent, title="Результаты запроса"):
        super().__init__(parent)
        self.title(title)
        self.geometry("800x600")
        self.parent = parent

        self.create_widgets()

    def create_widgets(self):
        # Создаем фрейм для таблицы
        self.frame_table = ctk.CTkFrame(self)
        self.frame_table.pack(fill="both", expand=True, padx=10, pady=10)

        # Создаем Treeview для отображения таблицы
        self.tree_result = ttk.Treeview(self.frame_table)
        self.tree_result.pack(fill="both", expand=True, padx=5, pady=5)

        # Добавляем скроллбары
        vsb = ttk.Scrollbar(self.frame_table, orient="vertical", command=self.tree_result.yview)
        vsb.pack(side='right', fill='y')
        self.tree_result.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(self.frame_table, orient="horizontal", command=self.tree_result.xview)
        hsb.pack(side='bottom', fill='x')
        self.tree_result.configure(xscrollcommand=hsb.set)

        # Кнопки управления
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=5)

        self.btn_export = ctk.CTkButton(button_frame, text="Экспорт", command=self.export_results)
        self.btn_export.pack(side="left", padx=5)

        self.btn_visualize = ctk.CTkButton(button_frame, text="Визуализация",
                                           command=self.visualize_data,
                                           fg_color="purple")
        self.btn_visualize.pack(side="left", padx=5)

        self.btn_close = ctk.CTkButton(button_frame, text="Закрыть", command=self.destroy)
        self.btn_close.pack(side="right", padx=5)

        self.results_data = None

    def display_results(self, data):
        """Отображение результатов в таблице"""
        # Сохраняем данные для экспорта
        self.results_data = data

        # Очищаем таблицу
        for item in self.tree_result.get_children():
            self.tree_result.delete(item)

        # Получаем колонки
        columns = list(data[0].keys()) if data else []

        # Настраиваем столбцы
        self.tree_result["columns"] = columns
        self.tree_result["show"] = "headings"

        for col in columns:
            self.tree_result.heading(col, text=col)
            self.tree_result.column(col, width=100)

        # Добавляем данные
        for row in data:
            values = [str(row.get(col, "")) for col in columns]
            self.tree_result.insert("", "end", values=values)

    def display_message(self, message):
        """Отображение сообщения"""
        # Очищаем таблицу
        for item in self.tree_result.get_children():
            self.tree_result.delete(item)

        # Добавляем сообщение
        self.tree_result["columns"] = ("message",)
        self.tree_result.heading("message", text="Сообщение")
        self.tree_result.insert("", "end", values=(message,))
        self.results_data = None

    def export_results(self):
        """Экспорт результатов"""
        if not self.results_data:
            messagebox.showwarning("Экспорт", "Нет данных для экспорта")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[
                ("CSV files", "*.csv"),
                ("Excel files", "*.xlsx"),
                ("All files", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            df = pd.DataFrame(self.results_data)

            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)

            messagebox.showinfo("Экспорт", f"Данные успешно экспортированы в {file_path}")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")

    def visualize_data(self):
        """Открытие визуализатора данных"""
        if not self.results_data:
            messagebox.showwarning("Ошибка", "Нет данных для визуализации")
            return

        get_data_visualizer(self.parent, self.results_data)

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("SQL Помощник")
        self.geometry("1000x800")

        # Загрузка настроек
        self.settings = self.load_settings()
        self.current_theme = self.settings.get("theme", "dark")

        # Установка темы
        if self.current_theme == "light":
            ctk.set_appearance_mode("light")
            ctk.set_default_color_theme("blue")
        else:
            ctk.set_appearance_mode("dark")
            ctk.set_default_color_theme("dark-blue")

        self.db = None
        self.query_history = []
        self.connections = {}
        self.last_result = None
        self.tables = []
        self.templates = self.get_sql_templates()
        self.results_window = None

        self.load_history()
        self.load_connections()

        # UI элементы
        self.create_widgets()

    def create_widgets(self):
        # === Верхняя панель с настройками ===
        top_frame = ctk.CTkFrame(self)
        top_frame.pack(fill="x", padx=10, pady=5)

        # Тема
        theme_label = ctk.CTkLabel(top_frame, text="Тема:")
        theme_label.pack(side="left", padx=5)

        self.theme_switch = ctk.CTkSwitch(
            top_frame,
            text="Светлая",
            command=self.toggle_theme
        )
        self.theme_switch.pack(side="left", padx=5)

        if self.current_theme == "light":
            self.theme_switch.select()

        # === Панель подключения ===
        ctk.CTkLabel(self, text="Подключение к MySQL", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=5)

        frame_conn = ctk.CTkFrame(self)
        frame_conn.pack(padx=10, pady=5, fill="x")

        # Выбор сохраненного подключения
        ctk.CTkLabel(frame_conn, text="Сохраненные подключения:").grid(row=0, column=0, sticky="w", padx=5, pady=5)
        self.conn_combo = ctk.CTkComboBox(frame_conn, values=["Новое подключение"] + list(self.connections.keys()))
        self.conn_combo.grid(row=0, column=1, padx=5, pady=5)
        self.conn_combo.set("Новое подключение")
        self.conn_combo.configure(command=self.load_connection)

        ctk.CTkLabel(frame_conn, text="Название подключения:").grid(row=1, column=0, sticky="w", padx=5, pady=5)
        self.entry_conn_name = ctk.CTkEntry(frame_conn)
        self.entry_conn_name.grid(row=1, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_conn, text="Хост:").grid(row=2, column=0, sticky="w", padx=5, pady=5)
        self.entry_host = ctk.CTkEntry(frame_conn)
        self.entry_host.grid(row=2, column=1, padx=5, pady=5)
        self.entry_host.insert(0, "localhost")

        ctk.CTkLabel(frame_conn, text="Пользователь:").grid(row=3, column=0, sticky="w", padx=5, pady=5)
        self.entry_user = ctk.CTkEntry(frame_conn)
        self.entry_user.grid(row=3, column=1, padx=5, pady=5)
        self.entry_user.insert(0, "root")

        ctk.CTkLabel(frame_conn, text="Пароль:").grid(row=4, column=0, sticky="w", padx=5, pady=5)
        self.entry_password = ctk.CTkEntry(frame_conn, show="*")
        self.entry_password.grid(row=4, column=1, padx=5, pady=5)

        ctk.CTkLabel(frame_conn, text="База данных:").grid(row=5, column=0, sticky="w", padx=5, pady=5)
        self.entry_db = ctk.CTkEntry(frame_conn)
        self.entry_db.grid(row=5, column=1, padx=5, pady=5)

        # Кнопки подключения
        conn_btn_frame = ctk.CTkFrame(frame_conn)
        conn_btn_frame.grid(row=6, column=0, columnspan=2, pady=10)

        self.btn_connect = ctk.CTkButton(conn_btn_frame, text="Подключиться", command=self.connect_db)
        self.btn_connect.pack(side="left", padx=5)

        self.btn_save_conn = ctk.CTkButton(conn_btn_frame, text="Сохранить", command=self.save_connection)
        self.btn_save_conn.pack(side="left", padx=5)

        self.btn_delete_conn = ctk.CTkButton(conn_btn_frame, text="Удалить", command=self.delete_connection)
        self.btn_delete_conn.pack(side="left", padx=5)

        # === Кнопки стандартных действий ===
        ctk.CTkLabel(self, text="Быстрые действия", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))

        frame_actions = ctk.CTkFrame(self)
        frame_actions.pack(padx=10, pady=5, fill="x")

        self.btn_create = ctk.CTkButton(frame_actions, text="Создать таблицу", command=self.template_create)
        self.btn_create.grid(row=0, column=0, padx=5, pady=5)

        self.btn_select = ctk.CTkButton(frame_actions, text="Выбрать данные", command=self.template_select)
        self.btn_select.grid(row=0, column=1, padx=5, pady=5)

        self.btn_insert = ctk.CTkButton(frame_actions, text="Добавить запись", command=self.template_insert)
        self.btn_insert.grid(row=0, column=2, padx=5, pady=5)

        self.btn_update = ctk.CTkButton(frame_actions, text="Обновить запись", command=self.template_update)
        self.btn_update.grid(row=1, column=0, padx=5, pady=5)

        self.btn_delete = ctk.CTkButton(frame_actions, text="Удалить запись", command=self.template_delete)
        self.btn_delete.grid(row=1, column=1, padx=5, pady=5)

        self.btn_drop = ctk.CTkButton(frame_actions, text="Удалить таблицу", command=self.template_drop)
        self.btn_drop.grid(row=1, column=2, padx=5, pady=5)

        # === КОНСТРУКТОР ЗАПРОСОВ ===
        self.btn_query_builder = ctk.CTkButton(
            frame_actions,
            text="Конструктор запросов",
            command=self.open_query_builder
        )
        self.btn_query_builder.grid(row=2, column=0, padx=5, pady=5, sticky="ew")

        # Мониторинг запросов
        self.btn_monitor = ctk.CTkButton(
            frame_actions,
            text="Монитор запросов",
            command=self.open_query_monitor
        )
        self.btn_monitor.grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Импорт данных
        self.btn_import_data = ctk.CTkButton(
            frame_actions,
            text="Импорт данных",
            command=self.open_data_importer
        )
        self.btn_import_data.grid(row=2, column=2, padx=5, pady=5, sticky="ew")

        # Резервное копирование
        self.btn_backup = ctk.CTkButton(
            frame_actions,
            text="Резевное копирование",
            command=self.open_backup_manager,
            fg_color="orange"
        )
        self.btn_backup.grid(row=3, column=0, padx=5, pady=5, sticky="ew")

        # Сравнение схем
        self.btn_schema_compare = ctk.CTkButton(
            frame_actions,
            text="Сравнение схем",
            command=self.open_schema_comparator,
            fg_color="purple"
        )
        self.btn_schema_compare.grid(row=3, column=1, padx=5, pady=5, sticky="ew")

        # Редактор таблиц
        self.btn_table_editor = ctk.CTkButton(
            frame_actions,
            text="Редактор таблиц",
            command=self.open_table_editor,
            fg_color="darkblue"
        )
        self.btn_table_editor.grid(row=3, column=2, padx=5, pady=5, sticky="ew")

        # Планировщик задач
        self.btn_scheduler = ctk.CTkButton(
            frame_actions,
            text="Планировщик задач",
            command=self.open_task_scheduler,
            fg_color="brown"
        )
        self.btn_scheduler.grid(row=3, column=3, padx=5, pady=5, sticky="ew")

        # Многотабличный редактор
        self.btn_multi_editor = ctk.CTkButton(
            frame_actions,
            text="Многотабличный редактор",
            command=self.open_multi_table_editor,
            fg_color="teal"
        )
        self.btn_multi_editor.grid(row=3, column=4, padx=5, pady=5, sticky="ew")

        # Облачные сервисы
        self.btn_cloud_integration = ctk.CTkButton(
            frame_actions,
            text="Облачные сервисы",
            command=self.open_cloud_integration,
            fg_color="indigo"
        )
        self.btn_cloud_integration.grid(row=3, column=5, padx=5, pady=5, sticky="ew")

        # === Шаблоны запросов ===
        ctk.CTkLabel(self, text="Шаблоны запросов", font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(15, 5))

        frame_templates = ctk.CTkFrame(self)
        frame_templates.pack(padx=10, pady=5, fill="x")

        template_names = list(self.templates.keys())
        cols = 4
        for i, template_name in enumerate(template_names):
            btn = ctk.CTkButton(
                frame_templates,
                text=template_name,
                width=120,
                command=lambda t=template_name: self.insert_template(t)
            )
            btn.grid(row=i // cols, column=i % cols, padx=5, pady=5)

        # === Поле ввода SQL ===
        ctk.CTkLabel(self, text="SQL-запрос:", font=ctk.CTkFont(size=14)).pack(pady=(15, 5))

        # Создаем фрейм для текстового поля и кнопок
        frame_query = ctk.CTkFrame(self)
        frame_query.pack(fill="both", expand=True, padx=10, pady=5)

        # Создаем текстовый виджет с автодополнением
        self.text_query = SQLTextWidget(frame_query, height=150)
        self.text_query.pack(fill="both", expand=True, side="left", padx=(0, 5))

        # Привязываем события для автодополнения
        self.text_query.bind("<KeyRelease>", self.on_key_release)
        self.text_query.bind("<Button-1>", self.hide_autocomplete)

        # Кнопки справа от текстового поля
        frame_query_buttons = ctk.CTkFrame(frame_query)
        frame_query_buttons.pack(side="right", fill="y")

        self.btn_validate = ctk.CTkButton(frame_query_buttons, text="Проверить", command=self.validate_query)
        self.btn_validate.pack(pady=5)

        self.btn_execute = ctk.CTkButton(frame_query_buttons, text="Выполнить", command=self.execute_query)
        self.btn_execute.pack(pady=5)

        self.btn_history = ctk.CTkButton(frame_query_buttons, text="История", command=self.show_history)
        self.btn_history.pack(pady=5)

        self.btn_highlight = ctk.CTkButton(frame_query_buttons, text="Подсветить", command=self.highlight_sql)
        self.btn_highlight.pack(pady=5)

        # === Выпадающий список для автодополнения таблиц ===
        self.table_dropdown = ctk.CTkComboBox(self, values=[], command=self.select_table_from_dropdown)
        self.table_dropdown.pack_forget()  # Скрываем по умолчанию

    # === Шаблоны SQL запросов ===
    def get_sql_templates(self):
        return {
            "SELECT *": "SELECT * FROM table_name;",
            "SELECT WHERE": "SELECT * FROM table_name WHERE condition;",
            "INSERT": "INSERT INTO table_name (column1, column2) VALUES (value1, value2);",
            "UPDATE": "UPDATE table_name SET column1 = value1 WHERE condition;",
            "DELETE": "DELETE FROM table_name WHERE condition;",
            "CREATE TABLE": "CREATE TABLE table_name (\n    id INT AUTO_INCREMENT PRIMARY KEY,\n    name VARCHAR(100)\n);",
            "ALTER TABLE": "ALTER TABLE table_name ADD COLUMN column_name datatype;",
            "DROP TABLE": "DROP TABLE IF EXISTS table_name;",
            "SHOW TABLES": "SHOW TABLES;",
            "DESCRIBE": "DESCRIBE table_name;"
        }

    def insert_template(self, template_name):
        template = self.templates.get(template_name, "")
        self.text_query.delete("0.0", "end")
        self.text_query.insert("0.0", template)
        self.highlight_sql()

    # === Автодополнение ===
    def on_key_release(self, event):
        # Получаем текущую позицию курсора
        cursor_pos = self.text_query.index("insert")
        line, col = map(int, cursor_pos.split('.'))

        # Получаем текст до курсора
        line_text = self.text_query.get(f"{line}.0", cursor_pos)

        # Проверяем, если вводим слово после FROM или INTO
        words = line_text.upper().split()
        if words and (words[-1] in ['FROM', 'INTO', 'UPDATE', 'TABLE']):
            self.show_table_autocomplete(line, col)
        elif words and words[-1].startswith('SEL'):  # SELECT
            self.show_keyword_autocomplete(line, col, ['SELECT'])
        else:
            self.hide_autocomplete()

    def show_table_autocomplete(self, line, col):
        if not self.tables:
            return

        # Показываем выпадающий список таблиц
        self.table_dropdown.configure(values=self.tables)
        self.table_dropdown.set("")
        self.table_dropdown.pack(pady=5)

        # Позиционируем рядом с текстовым полем
        self.table_dropdown.place(x=200, y=400)  # Примерные координаты

    def select_table_from_dropdown(self, selection):
        # Вставляем выбранную таблицу в текст
        current_text = self.text_query.get("0.0", "end-1c")
        # Простая замена последнего слова на имя таблицы
        lines = current_text.split('\n')
        if lines:
            last_line = lines[-1]
            words = last_line.split()
            if words:
                # Заменяем последнее слово
                words[-1] = selection
                lines[-1] = ' '.join(words)
                new_text = '\n'.join(lines)
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", new_text)
        self.hide_autocomplete()

    def hide_autocomplete(self, event=None):
        self.table_dropdown.pack_forget()

    def show_keyword_autocomplete(self, line, col, keywords):
        # Пока просто скрываем таблицы
        self.hide_autocomplete()

    # === Подсветка синтаксиса ===
    def highlight_sql(self):
        self.text_query.highlight_syntax()

    # === Настройки и темы ===
    def load_settings(self):
        if os.path.exists("settings.json"):
            try:
                with open("settings.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def save_settings(self):
        with open("settings.json", "w", encoding="utf-8") as f:
            json.dump(self.settings, f, ensure_ascii=False, indent=2)

    def toggle_theme(self):
        if self.theme_switch.get():
            ctk.set_appearance_mode("light")
            self.settings["theme"] = "light"
        else:
            ctk.set_appearance_mode("dark")
            self.settings["theme"] = "dark"
        self.save_settings()

    # === Работа с подключениями ===
    def load_connections(self):
        if os.path.exists("connections.json"):
            try:
                with open("connections.json", "r", encoding="utf-8") as f:
                    self.connections = json.load(f)
                    self.update_connection_combo()
            except:
                self.connections = {}

    def save_connections(self):
        with open("connections.json", "w", encoding="utf-8") as f:
            json.dump(self.connections, f, ensure_ascii=False, indent=2)

    def update_connection_combo(self):
        current = self.conn_combo.get()
        self.conn_combo.configure(values=["Новое подключение"] + list(self.connections.keys()))
        if current in self.connections or current == "Новое подключение":
            self.conn_combo.set(current)
        else:
            self.conn_combo.set("Новое подключение")

    def load_connection(self, selection):
        if selection == "Новое подключение":
            self.clear_connection_fields()
        elif selection in self.connections:
            conn_data = self.connections[selection]
            self.entry_conn_name.delete(0, "end")
            self.entry_conn_name.insert(0, selection)
            self.entry_host.delete(0, "end")
            self.entry_host.insert(0, conn_data.get("host", ""))
            self.entry_user.delete(0, "end")
            self.entry_user.insert(0, conn_data.get("user", ""))
            self.entry_password.delete(0, "end")
            self.entry_password.insert(0, conn_data.get("password", ""))
            self.entry_db.delete(0, "end")
            self.entry_db.insert(0, conn_data.get("database", ""))

    def save_connection(self):
        name = self.entry_conn_name.get().strip()
        if not name:
            messagebox.showwarning("Сохранение", "Введите название подключения")
            return

        connection_data = {
            "host": self.entry_host.get(),
            "user": self.entry_user.get(),
            "password": self.entry_password.get(),
            "database": self.entry_db.get()
        }

        self.connections[name] = connection_data
        self.save_connections()
        self.update_connection_combo()
        messagebox.showinfo("Сохранение", f"Подключение '{name}' сохранено")

    def delete_connection(self):
        name = self.entry_conn_name.get().strip()
        if not name or name not in self.connections:
            messagebox.showwarning("Удаление", "Выберите подключение для удаления")
            return

        if messagebox.askyesno("Удаление", f"Удалить подключение '{name}'?"):
            del self.connections[name]
            self.save_connections()
            self.update_connection_combo()
            self.clear_connection_fields()
            messagebox.showinfo("Удаление", f"Подключение '{name}' удалено")

    def clear_connection_fields(self):
        self.entry_conn_name.delete(0, "end")
        self.entry_host.delete(0, "end")
        self.entry_user.delete(0, "end")
        self.entry_password.delete(0, "end")
        self.entry_db.delete(0, "end")
        self.entry_host.insert(0, "localhost")
        self.entry_user.insert(0, "root")

    # === Функции подключения ===
    def connect_db(self):
        host = self.entry_host.get()
        user = self.entry_user.get()
        password = self.entry_password.get()
        database = self.entry_db.get()

        self.db = MySQLConnector(host, user, password, database)
        if self.db.connect():
            messagebox.showinfo("Подключение", "✅ Подключение успешно")
            self.update_table_list()
        else:
            messagebox.showerror("Подключение", "❌ Ошибка подключения")

    def update_table_list(self):
        if self.db:
            self.tables = self.db.get_tables()
            print(f"Доступные таблицы: {self.tables}")

    # === Загрузка истории ===
    def load_history(self):
        if os.path.exists("history.txt"):
            with open("history.txt", "r", encoding="utf-8") as f:
                self.query_history = [line.strip() for line in f.readlines()]

    # === Сохранение истории ===
    def save_history(self):
        with open("history.txt", "w", encoding="utf-8") as f:
            for query in self.query_history:
                f.write(query + "\n")

    # === Добавление запроса в историю ===
    def add_to_history(self, query):
        if query not in self.query_history:
            self.query_history.append(query)
            if len(self.query_history) > 50:
                self.query_history.pop(0)
            self.save_history()

    def open_query_builder(self):
        """Открытие конструктора запросов"""
        if not self.db:
            messagebox.showwarning("Ошибка", "Сначала подключитесь к базе данных")
            return
        QueryBuilder(self)

    # === Шаблоны запросов ===
    def template_create(self):
        sql = "CREATE TABLE IF NOT EXISTS users (\n    id INT AUTO_INCREMENT PRIMARY KEY,\n    name VARCHAR(100),\n    email VARCHAR(100)\n);"
        self.text_query.delete("0.0", "end")
        self.text_query.insert("0.0", sql)
        self.highlight_sql()

    def template_select(self):
        if self.tables:
            # Создаем диалог с выпадающим списком таблиц
            dialog = TableSelectDialog(self, self.tables)
            table_name = dialog.get_selection()
            if table_name:
                sql = f"SELECT * FROM {table_name};"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()
        else:
            dialog = ctk.CTkInputDialog(text="Введите имя таблицы:", title="Выбор данных")
            table_name = dialog.get_input()
            if table_name:
                sql = f"SELECT * FROM {table_name};"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()

    def template_insert(self):
        if self.tables:
            dialog = TableSelectDialog(self, self.tables)
            table_name = dialog.get_selection()
            if table_name:
                sql = f"INSERT INTO {table_name} (column1, column2) VALUES ('value1', 'value2');"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()
        else:
            dialog = ctk.CTkInputDialog(text="Введите имя таблицы:", title="Добавление записи")
            table_name = dialog.get_input()
            if table_name:
                sql = f"INSERT INTO {table_name} (column1, column2) VALUES ('value1', 'value2');"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()

    def template_update(self):
        if self.tables:
            dialog = TableSelectDialog(self, self.tables)
            table_name = dialog.get_selection()
            if table_name:
                sql = f"UPDATE {table_name} SET column1 = 'new_value' WHERE condition;"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()
        else:
            dialog = ctk.CTkInputDialog(text="Введите имя таблицы:", title="Обновление записи")
            table_name = dialog.get_input()
            if table_name:
                sql = f"UPDATE {table_name} SET column1 = 'new_value' WHERE condition;"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()

    def template_delete(self):
        if self.tables:
            dialog = TableSelectDialog(self, self.tables)
            table_name = dialog.get_selection()
            if table_name:
                sql = f"DELETE FROM {table_name} WHERE condition;"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()
        else:
            dialog = ctk.CTkInputDialog(text="Введите имя таблицы:", title="Удаление записи")
            table_name = dialog.get_input()
            if table_name:
                sql = f"DELETE FROM {table_name} WHERE condition;"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()

    def template_drop(self):
        if self.tables:
            dialog = TableSelectDialog(self, self.tables)
            table_name = dialog.get_selection()
            if table_name:
                sql = f"DROP TABLE IF EXISTS {table_name};"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()
        else:
            dialog = ctk.CTkInputDialog(text="Введите имя таблицы:", title="Удаление таблицы")
            table_name = dialog.get_input()
            if table_name:
                sql = f"DROP TABLE IF EXISTS {table_name};"
                self.text_query.delete("0.0", "end")
                self.text_query.insert("0.0", sql)
                self.highlight_sql()

    # === Валидация SQL ===
    def validate_query(self):
        query = self.text_query.get("0.0", "end").strip()
        if not query:
            messagebox.showwarning("Проверка", "Введите SQL-запрос для проверки")
            return

        if self.db:
            is_valid, message = self.db.validate_query(query)
            if is_valid:
                messagebox.showinfo("Проверка", "✅ " + message)
            else:
                messagebox.showwarning("Проверка", "❌ " + message)
        else:
            messagebox.showwarning("Проверка", "Сначала подключитесь к базе данных")

    # === Выполнение запроса ===
    def execute_query(self):
        if not self.db or not self.db.connection:
            messagebox.showwarning("Выполнение", "⚠ Сначала подключитесь к базе данных")
            return

        query = self.text_query.get("0.0", "end").strip()
        if not query:
            messagebox.showwarning("Выполнение", "⚠ Введите SQL-запрос")
            return

        # Проверяем запрос перед выполнением
        if self.db:
            is_valid, message = self.db.validate_query(query)
            if not is_valid:
                if not messagebox.askyesno("Предупреждение",
                                           f"Запрос может быть некорректным:\n{message}\n\nВыполнить anyway?"):
                    return

        # Добавляем в историю
        self.add_to_history(query)

        # Замеряем время выполнения
        start_time = time.time()

        # Выполняем запрос (теперь правильно)
        result = self.db.execute_query(query)

        execution_time = time.time() - start_time

        # Определяем количество затронутых строк
        rows_affected = 0
        if isinstance(result, list):
            rows_affected = len(result)
        elif isinstance(result, str) and "Затронуто строк:" in result:
            try:
                # Извлекаем количество строк из сообщения
                parts = result.split("Затронуто строк:")
                if len(parts) > 1:
                    rows_affected = int(parts[1].strip().split()[0])
            except:
                pass

        # Логируем в монитор
        try:
            monitor = get_query_monitor(self)
            status = "Успех" if not isinstance(result, str) or not result.startswith("Ошибка") else "Ошибка"
            monitor.log_query(query, execution_time, rows_affected, status)
        except Exception as e:
            print(f"Ошибка логирования: {e}")

        # Создаем или показываем окно результатов
        if self.results_window is None or not self.results_window.winfo_exists():
            self.results_window = ResultsWindow(self, "Результаты запроса")
        else:
            self.results_window.lift()

        if isinstance(result, str):
            self.results_window.display_message(result)
        elif isinstance(result, list):
            if result:
                self.results_window.display_results(result)
                self.last_result = result
            else:
                self.results_window.display_message("Нет данных для отображения")
        else:
            self.results_window.display_message("Неизвестный формат результата")

    # === Показ истории запросов ===
    def show_history(self):
        if not self.query_history:
            messagebox.showinfo("История", "История запросов пуста")
            return

        history_window = ctk.CTkToplevel(self)
        history_window.title("История запросов")
        history_window.geometry("600x400")

        listbox = ctk.CTkTextbox(history_window, wrap="word")
        listbox.pack(fill="both", expand=True, padx=10, pady=10)

        for i, query in enumerate(reversed(self.query_history), 1):
            listbox.insert("0.0", f"{i}. {query}\n\n")

        clear_btn = ctk.CTkButton(history_window, text="Очистить историю",
                                  command=lambda: self.clear_history(history_window))
        clear_btn.pack(pady=10)

    # === Очистка истории ===
    def clear_history(self, window):
        self.query_history = []
        self.save_history()
        window.destroy()
        messagebox.showinfo("История", "История очищена")

    def open_query_monitor(self):
        """Открытие монитора запросов"""
        get_query_monitor(self)

    def open_data_importer(self):
        """Открытие импортера данных"""
        if not self.db:
            messagebox.showwarning("Ошибка", "Сначала подключитесь к базе данных")
            return

        DataImporter(self)

    def open_backup_manager(self):
        """Открытие менеджера бэкапов"""
        if not self.db:
            messagebox.showwarning("Ошибка", "Сначала подключитесь к базе данных")
            return

        get_backup_manager(self)

    def open_schema_comparator(self):
        """Открытие компаратора схем"""
        if not self.db:
            messagebox.showwarning("Ошибка", "Сначала подключитесь к базе данных")
            return

        get_schema_comparator(self)

    def open_table_editor(self):
        """Открытие редактора таблиц"""
        if not self.db:
            messagebox.showwarning("Ошибка", "Сначала подключитесь к базе данных")
            return

        get_table_editor(self)

    def open_task_scheduler(self):
        """Открытие планировщика задач"""
        get_task_scheduler(self)

    def open_multi_table_editor(self):
        """Открытие многотабличного редактора"""
        get_multi_table_editor(self)

    def open_cloud_integration(self):
        """Открытие интеграции с облачными сервисами"""
        get_cloud_integration(self)

# === Диалог для выбора таблицы ===
class TableSelectDialog:
    def __init__(self, parent, tables):
        self.parent = parent
        self.tables = tables
        self.selection = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Выберите таблицу")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.dialog.wait_window()

    def create_widgets(self):
        ctk.CTkLabel(self.dialog, text="Выберите таблицу:").pack(pady=10)

        self.combo = ctk.CTkComboBox(self.dialog, values=self.tables)
        self.combo.pack(pady=10)
        if self.tables:
            self.combo.set(self.tables[0])

        btn_frame = ctk.CTkFrame(self.dialog)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="OK", command=self.ok).pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Отмена", command=self.cancel).pack(side="left", padx=5)

    def ok(self):
        self.selection = self.combo.get()
        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

    def get_selection(self):
        return self.selection
