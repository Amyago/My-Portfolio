import customtkinter as ctk
from tkinter import filedialog, messagebox
import json
import os
import sqlite3
import psycopg2
from datetime import datetime
import pandas as pd
import threading


class CloudIntegration(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Интеграция с облачными сервисами")
        self.geometry("900x700")
        self.parent = parent

        # Подключения к различным СУБД
        self.connections = {
            'mysql': None,
            'postgresql': None,
            'sqlite': None
        }

        self.create_widgets()
        self.load_connections()

    def create_widgets(self):
        # === Заголовок ===
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Интеграция с облачными сервисами",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        # === Панель подключений ===
        connections_frame = ctk.CTkFrame(self)
        connections_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(connections_frame, text="Подключения к базам данных:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # MySQL подключение
        mysql_frame = ctk.CTkFrame(connections_frame)
        mysql_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(mysql_frame, text="MySQL:", width=80).pack(side="left", padx=5)
        self.mysql_status = ctk.CTkLabel(mysql_frame, text="Не подключено", text_color="red")
        self.mysql_status.pack(side="left", padx=5)

        ctk.CTkButton(mysql_frame, text="Настроить",
                      command=self.setup_mysql,
                      width=80).pack(side="right", padx=2)

        ctk.CTkButton(mysql_frame, text="Подключить",
                      command=self.connect_mysql,
                      width=80,
                      fg_color="green").pack(side="right", padx=2)

        # PostgreSQL подключение
        postgresql_frame = ctk.CTkFrame(connections_frame)
        postgresql_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(postgresql_frame, text="PostgreSQL:", width=80).pack(side="left", padx=5)
        self.postgresql_status = ctk.CTkLabel(postgresql_frame, text="Не подключено", text_color="red")
        self.postgresql_status.pack(side="left", padx=5)

        ctk.CTkButton(postgresql_frame, text="Настроить",
                      command=self.setup_postgresql,
                      width=80).pack(side="right", padx=2)

        ctk.CTkButton(postgresql_frame, text="Подключить",
                      command=self.connect_postgresql,
                      width=80,
                      fg_color="green").pack(side="right", padx=2)

        # SQLite подключение
        sqlite_frame = ctk.CTkFrame(connections_frame)
        sqlite_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(sqlite_frame, text="SQLite:", width=80).pack(side="left", padx=5)
        self.sqlite_status = ctk.CTkLabel(sqlite_frame, text="Не подключено", text_color="red")
        self.sqlite_status.pack(side="left", padx=5)

        ctk.CTkButton(sqlite_frame, text="Настроить",
                      command=self.setup_sqlite,
                      width=80).pack(side="right", padx=2)

        ctk.CTkButton(sqlite_frame, text="Подключить",
                      command=self.connect_sqlite,
                      width=80,
                      fg_color="green").pack(side="right", padx=2)

        # === Синхронизация ===
        sync_frame = ctk.CTkFrame(self)
        sync_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(sync_frame, text="Синхронизация между базами:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Выбор исходной и целевой базы
        db_selection_frame = ctk.CTkFrame(sync_frame)
        db_selection_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(db_selection_frame, text="Из:").pack(side="left", padx=5)
        self.source_db_var = ctk.StringVar(value="mysql")
        ctk.CTkComboBox(db_selection_frame, values=["mysql", "postgresql", "sqlite"],
                        variable=self.source_db_var,
                        width=120).pack(side="left", padx=5)

        ctk.CTkLabel(db_selection_frame, text="В:").pack(side="left", padx=5)
        self.target_db_var = ctk.StringVar(value="sqlite")
        ctk.CTkComboBox(db_selection_frame, values=["mysql", "postgresql", "sqlite"],
                        variable=self.target_db_var,
                        width=120).pack(side="left", padx=5)

        # Выбор таблиц для синхронизации
        table_selection_frame = ctk.CTkFrame(sync_frame)
        table_selection_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(table_selection_frame, text="Таблицы:").pack(side="left", padx=5)
        self.tables_entry = ctk.CTkEntry(table_selection_frame, placeholder_text="table1,table2 или * для всех")
        self.tables_entry.pack(side="left", padx=5, fill="x", expand=True)
        self.tables_entry.insert(0, "*")

        # Кнопки синхронизации
        sync_buttons_frame = ctk.CTkFrame(sync_frame)
        sync_buttons_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(sync_buttons_frame, text="Синхронизировать",
                      command=self.start_sync,
                      fg_color="green",
                      font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        ctk.CTkButton(sync_buttons_frame, text="Синхронизировать в фоне",
                      command=self.start_background_sync).pack(side="left", padx=5)

        # === Прогресс синхронизации ===
        progress_frame = ctk.CTkFrame(self)
        progress_frame.pack(fill="x", padx=10, pady=5)

        self.progress_label = ctk.CTkLabel(progress_frame, text="Готов к синхронизации")
        self.progress_label.pack(padx=10, pady=5)

        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)

        # === Лог операций ===
        log_frame = ctk.CTkFrame(self)
        log_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(log_frame, text="Лог операций:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        self.log_text = ctk.CTkTextbox(log_frame, height=200)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=5)

        # Кнопки управления
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(control_frame, text="Очистить лог",
                      command=self.clear_log).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="Экспорт лога",
                      command=self.export_log).pack(side="left", padx=5)

        ctk.CTkButton(control_frame, text="Закрыть",
                      command=self.destroy).pack(side="right", padx=5)

    def log_message(self, message):
        """Добавление сообщения в лог"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert("0.0", log_entry)
        self.log_text.see("0.0")

    def setup_mysql(self):
        """Настройка MySQL подключения"""
        dialog = DatabaseConfigDialog(self, "MySQL", "mysql")
        config = dialog.get_config()
        if config:
            self.save_connection_config("mysql", config)
            self.log_message("Конфигурация MySQL сохранена")

    def setup_postgresql(self):
        """Настройка PostgreSQL подключения"""
        dialog = DatabaseConfigDialog(self, "PostgreSQL", "postgresql")
        config = dialog.get_config()
        if config:
            self.save_connection_config("postgresql", config)
            self.log_message("Конфигурация PostgreSQL сохранена")

    def setup_sqlite(self):
        """Настройка SQLite подключения"""
        file_path = filedialog.askopenfilename(
            title="Выберите SQLite файл",
            filetypes=[("SQLite файлы", "*.db *.sqlite *.sqlite3"), ("Все файлы", "*.*")]
        )
        if file_path:
            config = {"database": file_path}
            self.save_connection_config("sqlite", config)
            self.log_message(f"Конфигурация SQLite сохранена: {file_path}")

    def connect_mysql(self):
        """Подключение к MySQL"""
        try:
            config = self.load_connection_config("mysql")
            if not config:
                messagebox.showwarning("Ошибка", "Сначала настройте подключение")
                return

            # Импортируем pymysql только при необходимости
            import pymysql

            connection = pymysql.connect(
                host=config.get("host", "localhost"),
                user=config.get("user", "root"),
                password=config.get("password", ""),
                database=config.get("database", ""),
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )

            self.connections['mysql'] = connection
            self.mysql_status.configure(text="Подключено", text_color="green")
            self.log_message("Подключение к MySQL установлено")

        except Exception as e:
            self.log_message(f"Ошибка подключения к MySQL: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка подключения к MySQL:\n{str(e)}")

    def connect_postgresql(self):
        """Подключение к PostgreSQL"""
        try:
            config = self.load_connection_config("postgresql")
            if not config:
                messagebox.showwarning("Ошибка", "Сначала настройте подключение")
                return

            connection = psycopg2.connect(
                host=config.get("host", "localhost"),
                user=config.get("user", "postgres"),
                password=config.get("password", ""),
                database=config.get("database", "postgres"),
                port=config.get("port", 5432)
            )

            self.connections['postgresql'] = connection
            self.postgresql_status.configure(text="Подключено", text_color="green")
            self.log_message("Подключение к PostgreSQL установлено")

        except Exception as e:
            self.log_message(f"Ошибка подключения к PostgreSQL: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка подключения к PostgreSQL:\n{str(e)}")

    def connect_sqlite(self):
        """Подключение к SQLite"""
        try:
            config = self.load_connection_config("sqlite")
            if not config or "database" not in config:
                messagebox.showwarning("Ошибка", "Сначала настройте подключение")
                return

            connection = sqlite3.connect(config["database"])
            connection.row_factory = sqlite3.Row  # Для доступа по именам колонок

            self.connections['sqlite'] = connection
            self.sqlite_status.configure(text="Подключено", text_color="green")
            self.log_message("Подключение к SQLite установлено")

        except Exception as e:
            self.log_message(f"Ошибка подключения к SQLite: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка подключения к SQLite:\n{str(e)}")

    def save_connection_config(self, db_type, config):
        """Сохранение конфигурации подключения"""
        configs = self.load_all_configs()
        configs[db_type] = config

        with open("db_configs.json", "w", encoding="utf-8") as f:
            json.dump(configs, f, ensure_ascii=False, indent=2)

    def load_connection_config(self, db_type):
        """Загрузка конфигурации подключения"""
        configs = self.load_all_configs()
        return configs.get(db_type)

    def load_all_configs(self):
        """Загрузка всех конфигураций"""
        if os.path.exists("db_configs.json"):
            try:
                with open("db_configs.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def load_connections(self):
        """Загрузка сохраненных подключений"""
        configs = self.load_all_configs()
        for db_type in configs:
            if db_type == "mysql":
                self.mysql_status.configure(text="Настроено", text_color="orange")
            elif db_type == "postgresql":
                self.postgresql_status.configure(text="Настроено", text_color="orange")
            elif db_type == "sqlite":
                self.sqlite_status.configure(text="Настроено", text_color="orange")

    def start_sync(self):
        """Запуск синхронизации"""
        try:
            source_db = self.source_db_var.get()
            target_db = self.target_db_var.get()
            tables_input = self.tables_entry.get().strip()

            if source_db == target_db:
                messagebox.showwarning("Ошибка", "Исходная и целевая базы должны быть разными")
                return

            if not self.connections[source_db]:
                messagebox.showwarning("Ошибка", f"Подключитесь к {source_db}")
                return

            if not self.connections[target_db]:
                messagebox.showwarning("Ошибка", f"Подключитесь к {target_db}")
                return

            # Определяем таблицы для синхронизации
            if tables_input == "*":
                tables = self.get_all_tables(source_db)
            else:
                tables = [table.strip() for table in tables_input.split(",")]

            if not tables:
                messagebox.showwarning("Ошибка", "Нет таблиц для синхронизации")
                return

            # Запускаем синхронизацию
            self.sync_databases(source_db, target_db, tables)

        except Exception as e:
            self.log_message(f"Ошибка синхронизации: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка синхронизации:\n{str(e)}")

    def start_background_sync(self):
        """Запуск синхронизации в фоне"""
        thread = threading.Thread(target=self.start_sync, daemon=True)
        thread.start()
        self.log_message("Синхронизация запущена в фоновом режиме")

    def get_all_tables(self, db_type):
        """Получение списка всех таблиц"""
        try:
            connection = self.connections[db_type]
            if not connection:
                return []

            if db_type == "mysql":
                cursor = connection.cursor()
                cursor.execute("SHOW TABLES")
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()
                return tables
            elif db_type == "postgresql":
                cursor = connection.cursor()
                cursor.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'")
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()
                return tables
            elif db_type == "sqlite":
                cursor = connection.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                cursor.close()
                return tables

        except Exception as e:
            self.log_message(f"Ошибка получения списка таблиц: {str(e)}")
            return []

    def sync_databases(self, source_db, target_db, tables):
        """Синхронизация баз данных"""
        try:
            self.progress_bar.set(0)
            self.progress_label.configure(text="Начало синхронизации...")

            total_tables = len(tables)
            for i, table in enumerate(tables):
                self.progress_label.configure(text=f"Синхронизация таблицы: {table}")
                progress = (i + 1) / total_tables
                self.progress_bar.set(progress)

                # Получаем данные из исходной таблицы
                data = self.get_table_data(source_db, table)
                if data is not None:
                    # Создаем/обновляем таблицу в целевой базе
                    self.create_or_update_table(target_db, table, data)
                    self.log_message(f"Таблица {table} синхронизирована")
                else:
                    self.log_message(f"Ошибка синхронизации таблицы {table}")

                # Обновляем интерфейс
                self.update_idletasks()

            self.progress_bar.set(1.0)
            self.progress_label.configure(text="Синхронизация завершена")
            self.log_message("Синхронизация завершена успешно")
            messagebox.showinfo("Успех", "Синхронизация завершена")

        except Exception as e:
            self.log_message(f"Ошибка синхронизации: {str(e)}")
            messagebox.showerror("Ошибка", f"Ошибка синхронизации:\n{str(e)}")

    def get_table_data(self, db_type, table_name):
        """Получение данных из таблицы"""
        try:
            connection = self.connections[db_type]
            if not connection:
                return None

            if db_type == "mysql":
                cursor = connection.cursor()
                cursor.execute(f"SELECT * FROM `{table_name}`")
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                cursor.close()

                # Преобразуем в список словарей
                data = [dict(zip(columns, row)) for row in rows]
                return {"columns": columns, "data": data}

            elif db_type == "postgresql":
                cursor = connection.cursor()
                cursor.execute(f'SELECT * FROM "{table_name}"')
                columns = [desc[0] for desc in cursor.description]
                rows = cursor.fetchall()
                cursor.close()

                # Преобразуем в список словарей
                data = [dict(zip(columns, row)) for row in rows]
                return {"columns": columns, "data": data}

            elif db_type == "sqlite":
                cursor = connection.cursor()
                cursor.execute(f'SELECT * FROM "{table_name}"')
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()
                cursor.close()

                # Преобразуем в список словарей
                data = [dict(zip(columns, row)) for row in rows]
                return {"columns": columns, "data": data}

        except Exception as e:
            self.log_message(f"Ошибка получения данных из {table_name}: {str(e)}")
            return None

    def create_or_update_table(self, db_type, table_name, table_data):
        """Создание или обновление таблицы"""
        try:
            connection = self.connections[db_type]
            if not connection:
                return

            columns = table_data["columns"]
            data = table_data["data"]

            if db_type == "mysql":
                cursor = connection.cursor()

                # Удаляем существующую таблицу
                try:
                    cursor.execute(f"DROP TABLE IF EXISTS `{table_name}`")
                except:
                    pass

                # Создаем таблицу (упрощенная схема)
                if data:
                    sample_row = data[0]
                    column_definitions = []
                    for col in columns:
                        value = sample_row[col]
                        if isinstance(value, int):
                            col_type = "INT"
                        elif isinstance(value, float):
                            col_type = "DOUBLE"
                        elif isinstance(value, bool):
                            col_type = "BOOLEAN"
                        else:
                            col_type = "TEXT"
                        column_definitions.append(f"`{col}` {col_type}")

                    create_sql = f"CREATE TABLE `{table_name}` ({', '.join(column_definitions)})"
                    cursor.execute(create_sql)

                    # Вставляем данные
                    if data:
                        placeholders = ", ".join(["%s"] * len(columns))
                        columns_str = ", ".join([f"`{col}`" for col in columns])
                        insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders})"

                        for row in data:
                            values = [row[col] for col in columns]
                            cursor.execute(insert_sql, values)

                connection.commit()
                cursor.close()

            elif db_type == "postgresql":
                cursor = connection.cursor()

                # Удаляем существующую таблицу
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                except:
                    pass

                # Создаем таблицу
                if data:
                    sample_row = data[0]
                    column_definitions = []
                    for col in columns:
                        value = sample_row[col]
                        if isinstance(value, int):
                            col_type = "INTEGER"
                        elif isinstance(value, float):
                            col_type = "DOUBLE PRECISION"
                        elif isinstance(value, bool):
                            col_type = "BOOLEAN"
                        else:
                            col_type = "TEXT"
                        column_definitions.append(f'"{col}" {col_type}')

                    create_sql = f'CREATE TABLE "{table_name}" ({", ".join(column_definitions)})'
                    cursor.execute(create_sql)

                    # Вставляем данные
                    if data:
                        placeholders = ", ".join([f"${i + 1}" for i in range(len(columns))])
                        columns_str = ", ".join([f'"{col}"' for col in columns])
                        insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'

                        for row in data:
                            values = [row[col] for col in columns]
                            cursor.execute(insert_sql, values)

                connection.commit()
                cursor.close()

            elif db_type == "sqlite":
                cursor = connection.cursor()

                # Удаляем существующую таблицу
                try:
                    cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                except:
                    pass

                # Создаем таблицу
                if data:
                    sample_row = data[0]
                    column_definitions = []
                    for col in columns:
                        value = sample_row[col]
                        if isinstance(value, int):
                            col_type = "INTEGER"
                        elif isinstance(value, float):
                            col_type = "REAL"
                        elif isinstance(value, bool):
                            col_type = "INTEGER"
                        else:
                            col_type = "TEXT"
                        column_definitions.append(f'"{col}" {col_type}')

                    create_sql = f'CREATE TABLE "{table_name}" ({", ".join(column_definitions)})'
                    cursor.execute(create_sql)

                    # Вставляем данные
                    if data:
                        placeholders = ", ".join(["?"] * len(columns))
                        columns_str = ", ".join([f'"{col}"' for col in columns])
                        insert_sql = f'INSERT INTO "{table_name}" ({columns_str}) VALUES ({placeholders})'

                        for row in data:
                            values = [row[col] for col in columns]
                            cursor.execute(insert_sql, values)

                connection.commit()
                cursor.close()

        except Exception as e:
            self.log_message(f"Ошибка создания таблицы {table_name}: {str(e)}")

    def clear_log(self):
        """Очистка лога"""
        self.log_text.delete("0.0", "end")

    def export_log(self):
        """Экспорт лога"""
        file_path = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Текстовые файлы", "*.txt"), ("Все файлы", "*.*")],
            title="Экспорт лога"
        )

        if file_path:
            try:
                log_content = self.log_text.get("0.0", "end")
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(log_content)
                messagebox.showinfo("Успех", f"Лог экспортирован в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка экспорта лога:\n{str(e)}")


class DatabaseConfigDialog:
    def __init__(self, parent, db_name, db_type):
        self.parent = parent
        self.db_name = db_name
        self.db_type = db_type
        self.config = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(f"Настройка {db_name}")
        self.dialog.geometry("400x300")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Загружаем существующую конфигурацию
        existing_config = parent.load_connection_config(db_type)

        self.create_widgets(existing_config)
        self.dialog.wait_window()

    def create_widgets(self, existing_config=None):
        ctk.CTkLabel(self.dialog, text=f"Настройка подключения к {self.db_name}",
                     font=ctk.CTkFont(weight="bold")).pack(pady=10)

        # Хост
        host_frame = ctk.CTkFrame(self.dialog)
        host_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(host_frame, text="Хост:").pack(side="left", padx=5)
        self.host_entry = ctk.CTkEntry(host_frame)
        self.host_entry.pack(side="left", padx=5, fill="x", expand=True)
        if existing_config and "host" in existing_config:
            self.host_entry.insert(0, existing_config["host"])
        else:
            self.host_entry.insert(0, "localhost")

        # Пользователь
        user_frame = ctk.CTkFrame(self.dialog)
        user_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(user_frame, text="Пользователь:").pack(side="left", padx=5)
        self.user_entry = ctk.CTkEntry(user_frame)
        self.user_entry.pack(side="left", padx=5, fill="x", expand=True)
        if existing_config and "user" in existing_config:
            self.user_entry.insert(0, existing_config["user"])
        else:
            self.user_entry.insert(0, "root" if self.db_type == "mysql" else "postgres")

        # Пароль
        password_frame = ctk.CTkFrame(self.dialog)
        password_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(password_frame, text="Пароль:").pack(side="left", padx=5)
        self.password_entry = ctk.CTkEntry(password_frame, show="*")
        self.password_entry.pack(side="left", padx=5, fill="x", expand=True)
        if existing_config and "password" in existing_config:
            self.password_entry.insert(0, existing_config["password"])

        # База данных
        database_frame = ctk.CTkFrame(self.dialog)
        database_frame.pack(fill="x", padx=10, pady=2)

        ctk.CTkLabel(database_frame, text="База данных:").pack(side="left", padx=5)
        self.database_entry = ctk.CTkEntry(database_frame)
        self.database_entry.pack(side="left", padx=5, fill="x", expand=True)
        if existing_config and "database" in existing_config:
            self.database_entry.insert(0, existing_config["database"])

        # Порт (только для PostgreSQL)
        if self.db_type == "postgresql":
            port_frame = ctk.CTkFrame(self.dialog)
            port_frame.pack(fill="x", padx=10, pady=2)

            ctk.CTkLabel(port_frame, text="Порт:").pack(side="left", padx=5)
            self.port_entry = ctk.CTkEntry(port_frame, width=100)
            self.port_entry.pack(side="left", padx=5)
            if existing_config and "port" in existing_config:
                self.port_entry.insert(0, str(existing_config["port"]))
            else:
                self.port_entry.insert(0, "5432")

        # Кнопки
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Сохранить",
                      command=self.save_config,
                      fg_color="green").pack(side="left", padx=5)

        ctk.CTkButton(button_frame, text="Отмена",
                      command=self.cancel).pack(side="left", padx=5)

    def save_config(self):
        """Сохранение конфигурации"""
        config = {
            "host": self.host_entry.get().strip(),
            "user": self.user_entry.get().strip(),
            "password": self.password_entry.get(),
            "database": self.database_entry.get().strip()
        }

        if self.db_type == "postgresql":
            config["port"] = int(self.port_entry.get().strip() or 5432)

        self.config = config
        self.dialog.destroy()

    def cancel(self):
        """Отмена"""
        self.dialog.destroy()

    def get_config(self):
        """Получение конфигурации"""
        return self.config


# Глобальный экземпляр интеграции
cloud_integration = None


def get_cloud_integration(parent):
    """Получение или создание глобального экземпляра интеграции"""
    global cloud_integration
    if cloud_integration is None or not cloud_integration.winfo_exists():
        cloud_integration = CloudIntegration(parent)
    else:
        cloud_integration.lift()
    return cloud_integration
