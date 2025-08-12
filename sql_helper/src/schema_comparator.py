import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
import json
import os
from datetime import datetime


class SchemaComparator(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Сравнение схем баз данных")
        self.geometry("1000x700")
        self.parent = parent

        # Данные для сравнения
        self.source_schema = None
        self.target_schema = None

        self.create_widgets()

    def create_widgets(self):
        # === Заголовок ===
        ctk.CTkLabel(self, text="Сравнение схем баз данных",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # === Панель выбора схем ===
        schema_frame = ctk.CTkFrame(self)
        schema_frame.pack(fill="x", padx=10, pady=5)

        # Исходная схема
        source_frame = ctk.CTkFrame(schema_frame)
        source_frame.pack(side="left", fill="both", expand=True, padx=5)

        ctk.CTkLabel(source_frame, text="Исходная схема:",
                     font=ctk.CTkFont(weight="bold")).pack(pady=5)

        self.source_info = ctk.CTkLabel(source_frame, text="Не выбрана",
                                        text_color="red")
        self.source_info.pack(pady=5)

        source_btn_frame = ctk.CTkFrame(source_frame)
        source_btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(source_btn_frame, text="Текущая БД",
                      command=self.load_current_schema_source).pack(side="left", padx=2)
        ctk.CTkButton(source_btn_frame, text="Из файла",
                      command=lambda: self.load_schema_from_file("source")).pack(side="left", padx=2)

        # Целевая схема
        target_frame = ctk.CTkFrame(schema_frame)
        target_frame.pack(side="right", fill="both", expand=True, padx=5)

        ctk.CTkLabel(target_frame, text="Целевая схема:",
                     font=ctk.CTkFont(weight="bold")).pack(pady=5)

        self.target_info = ctk.CTkLabel(target_frame, text="Не выбрана",
                                        text_color="red")
        self.target_info.pack(pady=5)

        target_btn_frame = ctk.CTkFrame(target_frame)
        target_btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(target_btn_frame, text="Текущая БД",
                      command=self.load_current_schema_target).pack(side="left", padx=2)
        ctk.CTkButton(target_btn_frame, text="Из файла",
                      command=lambda: self.load_schema_from_file("target")).pack(side="left", padx=2)

        # === Кнопка сравнения ===
        compare_btn = ctk.CTkButton(self, text="Сравнить схемы",
                                    command=self.compare_schemas,
                                    font=ctk.CTkFont(size=14, weight="bold"),
                                    height=40)
        compare_btn.pack(pady=10)

        # === Результаты сравнения ===
        results_frame = ctk.CTkFrame(self)
        results_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(results_frame, text="Результаты сравнения:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Создаем вкладки для разных типов результатов
        self.tabview = ctk.CTkTabview(results_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=5)

        # Вкладка: Различия таблиц
        self.tab_differences = self.tabview.add("Различия таблиц")

        # Вкладка: Скрипты миграции
        self.tab_migration = self.tabview.add("Скрипты миграции")

        # Вкладка: Визуализация
        self.tab_visualization = self.tabview.add("Визуализация")

        # Вкладка: Статистика
        self.tab_statistics = self.tabview.add("Статистика")

        # Инициализируем содержимое вкладок
        self.init_differences_tab()
        self.init_migration_tab()
        self.init_visualization_tab()
        self.init_statistics_tab()

        # === Кнопки управления ===
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(button_frame, text="Экспорт отчета",
                      command=self.export_report).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Сохранить схему",
                      command=self.save_current_schema).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Закрыть",
                      command=self.destroy).pack(side="right", padx=5)

    def init_differences_tab(self):
        """Инициализация вкладки различий"""
        # Создаем фрейм для таблицы различий
        frame = ctk.CTkFrame(self.tab_differences)
        frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Создаем Treeview для отображения различий
        self.differences_tree = ttk.Treeview(frame)
        self.differences_tree.pack(fill="both", expand=True, padx=5, pady=5)

        # Добавляем скроллбары
        vsb = ttk.Scrollbar(frame, orient="vertical", command=self.differences_tree.yview)
        vsb.pack(side='right', fill='y')
        self.differences_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(frame, orient="horizontal", command=self.differences_tree.xview)
        hsb.pack(side='bottom', fill='x')
        self.differences_tree.configure(xscrollcommand=hsb.set)

        # Настройка колонок
        self.differences_tree["columns"] = ("table", "type", "source", "target", "status")
        self.differences_tree["show"] = "headings"

        self.differences_tree.heading("table", text="Таблица")
        self.differences_tree.heading("type", text="Тип")
        self.differences_tree.heading("source", text="Исходная")
        self.differences_tree.heading("target", text="Целевая")
        self.differences_tree.heading("status", text="Статус")

        self.differences_tree.column("table", width=150)
        self.differences_tree.column("type", width=100)
        self.differences_tree.column("source", width=200)
        self.differences_tree.column("target", width=200)
        self.differences_tree.column("status", width=100)

    def init_migration_tab(self):
        """Инициализация вкладки миграции"""
        # Создаем текстовое поле для скриптов миграции
        self.migration_text = ctk.CTkTextbox(self.tab_migration, wrap="none")
        self.migration_text.pack(fill="both", expand=True, padx=5, pady=5)

        # Кнопки управления
        migration_btn_frame = ctk.CTkFrame(self.tab_migration)
        migration_btn_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(migration_btn_frame, text="Копировать",
                      command=self.copy_migration_script).pack(side="left", padx=5)
        ctk.CTkButton(migration_btn_frame, text="Сохранить",
                      command=self.save_migration_script).pack(side="left", padx=5)

    def init_visualization_tab(self):
        """Инициализация вкладки визуализации"""
        # Создаем область для визуализации
        self.visualization_frame = ctk.CTkScrollableFrame(self.tab_visualization)
        self.visualization_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Добавляем пояснение
        ctk.CTkLabel(self.visualization_frame,
                     text="Визуализация различий схем баз данных",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

        ctk.CTkLabel(self.visualization_frame,
                     text="• Зеленый - совпадающие элементы\n"
                          "• Красный - отсутствующие элементы\n"
                          "• Желтый - измененные элементы\n"
                          "• Синий - новые элементы",
                     justify="left").pack(pady=5)

    def init_statistics_tab(self):
        """Инициализация вкладки статистики"""
        self.statistics_frame = ctk.CTkScrollableFrame(self.tab_statistics)
        self.statistics_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Добавляем заголовок
        ctk.CTkLabel(self.statistics_frame,
                     text="Статистика сравнения",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=10)

    def load_current_schema_source(self):
        """Загрузить текущую схему как исходную"""
        if not self.parent.db:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        try:
            schema = self.get_database_schema()
            self.source_schema = schema
            self.source_info.configure(text=f"Текущая БД ({len(schema)} таблиц)",
                                       text_color="green")
            messagebox.showinfo("Успех", "Исходная схема загружена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки схемы:\n{str(e)}")

    def load_current_schema_target(self):
        """Загрузить текущую схему как целевую"""
        if not self.parent.db:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        try:
            schema = self.get_database_schema()
            self.target_schema = schema
            self.target_info.configure(text=f"Текущая БД ({len(schema)} таблиц)",
                                       text_color="green")
            messagebox.showinfo("Успех", "Целевая схема загружена")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки схемы:\n{str(e)}")

    def load_schema_from_file(self, schema_type):
        """Загрузить схему из файла"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл схемы",
            filetypes=[
                ("JSON файлы", "*.json"),
                ("Все файлы", "*.*")
            ]
        )

        if not file_path:
            return

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                schema = json.load(f)

            if schema_type == "source":
                self.source_schema = schema
                tables_count = len(schema) if isinstance(schema, dict) else 0
                self.source_info.configure(text=f"Файл ({tables_count} таблиц)",
                                           text_color="green")
            else:
                self.target_schema = schema
                tables_count = len(schema) if isinstance(schema, dict) else 0
                self.target_info.configure(text=f"Файл ({tables_count} таблиц)",
                                           text_color="green")

            messagebox.showinfo("Успех", f"Схема загружена из файла:\n{os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки файла:\n{str(e)}")

    def get_database_schema(self):
        """Получить схему текущей базы данных"""
        if not self.parent.db or not self.parent.db.connection:
            raise Exception("Нет подключения к базе данных")

        schema = {}

        # Получаем список таблиц
        tables = self.parent.db.get_tables()

        # Для каждой таблицы получаем структуру
        for table in tables:
            try:
                # Получаем описание таблицы
                describe_result = self.parent.db.execute_query(f"DESCRIBE `{table}`")

                if isinstance(describe_result, list):
                    # Преобразуем в удобный формат
                    columns = []
                    for row in describe_result:
                        column_info = {
                            'name': row.get('Field', ''),
                            'type': row.get('Type', ''),
                            'null': row.get('Null', ''),
                            'key': row.get('Key', ''),
                            'default': row.get('Default', None),
                            'extra': row.get('Extra', '')
                        }
                        columns.append(column_info)

                    schema[table] = {
                        'columns': columns,
                        'timestamp': datetime.now().isoformat()
                    }

            except Exception as e:
                print(f"Ошибка получения структуры таблицы {table}: {e}")
                schema[table] = {'error': str(e)}

        return schema

    def compare_schemas(self):
        """Сравнить схемы баз данных"""
        if not self.source_schema:
            messagebox.showwarning("Ошибка", "Выберите исходную схему")
            return

        if not self.target_schema:
            messagebox.showwarning("Ошибка", "Выберите целевую схему")
            return

        try:
            # Выполняем сравнение
            differences = self.analyze_differences()

            # Отображаем результаты
            self.display_differences(differences)
            self.generate_migration_scripts(differences)
            self.display_visualization(differences)
            self.display_statistics(differences)

            # Переключаемся на вкладку различий
            self.tabview.set("Различия таблиц")

            messagebox.showinfo("Успех", "Сравнение схем завершено")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сравнения схем:\n{str(e)}")

    def analyze_differences(self):
        """Анализ различий между схемами"""
        differences = {
            'added_tables': [],  # Новые таблицы
            'removed_tables': [],  # Удаленные таблицы
            'modified_tables': [],  # Измененные таблицы
            'column_differences': []  # Различия в колонках
        }

        source_tables = set(self.source_schema.keys())
        target_tables = set(self.target_schema.keys())

        # Новые таблицы
        differences['added_tables'] = list(target_tables - source_tables)

        # Удаленные таблицы
        differences['removed_tables'] = list(source_tables - target_tables)

        # Общие таблицы
        common_tables = source_tables & target_tables

        for table in common_tables:
            source_table = self.source_schema[table]
            target_table = self.target_schema[table]

            # Проверяем колонки
            if 'columns' in source_table and 'columns' in target_table:
                source_columns = {col['name']: col for col in source_table['columns']}
                target_columns = {col['name']: col for col in target_table['columns']}

                source_col_names = set(source_columns.keys())
                target_col_names = set(target_columns.keys())

                # Новые колонки
                new_columns = target_col_names - source_col_names
                # Удаленные колонки
                removed_columns = source_col_names - target_col_names
                # Общие колонки
                common_columns = source_col_names & target_col_names

                modified_columns = []
                for col_name in common_columns:
                    source_col = source_columns[col_name]
                    target_col = target_columns[col_name]

                    # Сравниваем свойства колонки
                    if (source_col['type'] != target_col['type'] or
                            source_col['null'] != target_col['null'] or
                            source_col['default'] != target_col['default']):
                        modified_columns.append({
                            'table': table,
                            'column': col_name,
                            'source': source_col,
                            'target': target_col
                        })

                if new_columns or removed_columns or modified_columns:
                    differences['modified_tables'].append(table)
                    for col in new_columns:
                        differences['column_differences'].append({
                            'table': table,
                            'column': col,
                            'type': 'added',
                            'source': None,
                            'target': target_columns[col]
                        })
                    for col in removed_columns:
                        differences['column_differences'].append({
                            'table': table,
                            'column': col,
                            'type': 'removed',
                            'source': source_columns[col],
                            'target': None
                        })
                    differences['column_differences'].extend(modified_columns)

        return differences

    def display_differences(self, differences):
        """Отобразить различия в таблице"""
        # Очищаем предыдущие результаты
        for item in self.differences_tree.get_children():
            self.differences_tree.delete(item)

        # Отображаем новые таблицы
        for table in differences['added_tables']:
            self.differences_tree.insert("", "end", values=(table, "Таблица", "-", "Существует", "Новая"))

        # Отображаем удаленные таблицы
        for table in differences['removed_tables']:
            self.differences_tree.insert("", "end", values=(table, "Таблица", "Существует", "-", "Удалена"))

        # Отображаем различия в колонках
        for diff in differences['column_differences']:
            table = diff['table']
            column = diff['column']
            diff_type = diff['type']

            if diff_type == 'added':
                status = "Новая"
                source_val = "-"
                target_val = f"{diff['target']['type']}"
            elif diff_type == 'removed':
                status = "Удалена"
                source_val = f"{diff['source']['type']}"
                target_val = "-"
            else:  # modified
                status = "Изменена"
                source_val = f"{diff['source']['type']}"
                target_val = f"{diff['target']['type']}"

            self.differences_tree.insert("", "end",
                                         values=(f"{table}.{column}", "Колонка", source_val, target_val, status))

    def generate_migration_scripts(self, differences):
        """Генерация скриптов миграции"""
        scripts = []

        # Скрипт для новых таблиц
        if differences['added_tables']:
            scripts.append("-- Создание новых таблиц")
            for table in differences['added_tables']:
                scripts.append(f"-- TODO: Создать таблицу {table}")
            scripts.append("")

        # Скрипт для удаленных таблиц
        if differences['removed_tables']:
            scripts.append("-- Удаление таблиц")
            for table in differences['removed_tables']:
                scripts.append(f"DROP TABLE IF EXISTS `{table}`;")
            scripts.append("")

        # Скрипт для изменений в колонках
        if differences['column_differences']:
            scripts.append("-- Изменения в колонках")
            for diff in differences['column_differences']:
                table = diff['table']
                column = diff['column']
                diff_type = diff['type']

                if diff_type == 'added':
                    col_def = diff['target']
                    scripts.append(f"ALTER TABLE `{table}` ADD COLUMN `{column}` {col_def['type']}" +
                                   (f" DEFAULT {col_def['default']}" if col_def['default'] is not None else "") +
                                   (" NULL" if col_def['null'] == 'YES' else " NOT NULL") + ";")
                elif diff_type == 'removed':
                    scripts.append(f"ALTER TABLE `{table}` DROP COLUMN `{column}`;")
                else:  # modified
                    col_def = diff['target']
                    scripts.append(f"ALTER TABLE `{table}` MODIFY COLUMN `{column}` {col_def['type']}" +
                                   (f" DEFAULT {col_def['default']}" if col_def['default'] is not None else "") +
                                   (" NULL" if col_def['null'] == 'YES' else " NOT NULL") + ";")

        # Отображаем скрипты
        self.migration_text.delete("0.0", "end")
        self.migration_text.insert("0.0", "\n".join(scripts))

    def display_visualization(self, differences):
        """Отобразить визуализацию различий"""
        # Очищаем предыдущее содержимое
        for widget in self.visualization_frame.winfo_children():
            if not isinstance(widget, ctk.CTkLabel) or "Визуализация" not in widget.cget("text"):
                widget.destroy()

        # Добавляем статистику по категориям
        ctk.CTkLabel(self.visualization_frame,
                     text=f"📊 Статистика различий:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        ctk.CTkLabel(self.visualization_frame,
                     text=f"• Новых таблиц: {len(differences['added_tables'])}",
                     text_color="blue").pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.visualization_frame,
                     text=f"• Удаленных таблиц: {len(differences['removed_tables'])}",
                     text_color="red").pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.visualization_frame,
                     text=f"• Измененных таблиц: {len(differences['modified_tables'])}",
                     text_color="orange").pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.visualization_frame,
                     text=f"• Изменений в колонках: {len(differences['column_differences'])}",
                     text_color="yellow").pack(anchor="w", padx=20, pady=2)

        # Добавляем список изменений
        if differences['added_tables'] or differences['removed_tables'] or differences['column_differences']:
            ctk.CTkLabel(self.visualization_frame,
                         text=f"\n📋 Подробные изменения:",
                         font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

            # Новые таблицы
            if differences['added_tables']:
                ctk.CTkLabel(self.visualization_frame,
                             text="Новые таблицы:",
                             text_color="blue",
                             font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
                for table in differences['added_tables'][:5]:  # Показываем первые 5
                    ctk.CTkLabel(self.visualization_frame,
                                 text=f"  + {table}",
                                 text_color="blue").pack(anchor="w", padx=25, pady=1)
                if len(differences['added_tables']) > 5:
                    ctk.CTkLabel(self.visualization_frame,
                                 text=f"  ... и еще {len(differences['added_tables']) - 5}",
                                 text_color="gray").pack(anchor="w", padx=25, pady=1)

            # Удаленные таблицы
            if differences['removed_tables']:
                ctk.CTkLabel(self.visualization_frame,
                             text="Удаленные таблицы:",
                             text_color="red",
                             font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=15, pady=(5, 2))
                for table in differences['removed_tables'][:5]:
                    ctk.CTkLabel(self.visualization_frame,
                                 text=f"  - {table}",
                                 text_color="red").pack(anchor="w", padx=25, pady=1)
                if len(differences['removed_tables']) > 5:
                    ctk.CTkLabel(self.visualization_frame,
                                 text=f"  ... и еще {len(differences['removed_tables']) - 5}",
                                 text_color="gray").pack(anchor="w", padx=25, pady=1)

    def display_statistics(self, differences):
        """Отобразить статистику"""
        # Очищаем предыдущее содержимое
        for widget in self.statistics_frame.winfo_children():
            if not isinstance(widget, ctk.CTkLabel) or "Статистика" not in widget.cget("text"):
                widget.destroy()

        total_changes = (len(differences['added_tables']) +
                         len(differences['removed_tables']) +
                         len(differences['column_differences']))

        ctk.CTkLabel(self.statistics_frame,
                     text=f"📈 Общая статистика:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=5)

        ctk.CTkLabel(self.statistics_frame,
                     text=f"Всего изменений: {total_changes}").pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.statistics_frame,
                     text=f"Новых таблиц: {len(differences['added_tables'])}").pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.statistics_frame,
                     text=f"Удаленных таблиц: {len(differences['removed_tables'])}").pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.statistics_frame,
                     text=f"Измененных таблиц: {len(differences['modified_tables'])}").pack(anchor="w", padx=20, pady=2)

        ctk.CTkLabel(self.statistics_frame,
                     text=f"Изменений в колонках: {len(differences['column_differences'])}").pack(anchor="w", padx=20,
                                                                                                  pady=2)

        # Добавляем рекомендации
        ctk.CTkLabel(self.statistics_frame,
                     text=f"\n💡 Рекомендации:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=(10, 5))

        if total_changes == 0:
            ctk.CTkLabel(self.statistics_frame,
                         text="✓ Схемы идентичны",
                         text_color="green").pack(anchor="w", padx=20, pady=2)
        elif total_changes < 10:
            ctk.CTkLabel(self.statistics_frame,
                         text="ℹ Небольшие изменения - миграция безопасна",
                         text_color="blue").pack(anchor="w", padx=20, pady=2)
        else:
            ctk.CTkLabel(self.statistics_frame,
                         text="⚠ Значительные изменения - тщательно проверьте скрипты",
                         text_color="orange").pack(anchor="w", padx=20, pady=2)

    def copy_migration_script(self):
        """Копировать скрипт миграции в буфер обмена"""
        script = self.migration_text.get("0.0", "end").strip()
        if script:
            self.clipboard_clear()
            self.clipboard_append(script)
            messagebox.showinfo("Успех", "Скрипт скопирован в буфер обмена")
        else:
            messagebox.showwarning("Предупреждение", "Нет скрипта для копирования")

    def save_migration_script(self):
        """Сохранить скрипт миграции в файл"""
        script = self.migration_text.get("0.0", "end").strip()
        if not script:
            messagebox.showwarning("Предупреждение", "Нет скрипта для сохранения")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".sql",
            filetypes=[
                ("SQL файлы", "*.sql"),
                ("Текстовые файлы", "*.txt"),
                ("Все файлы", "*.*")
            ],
            title="Сохранить скрипт миграции"
        )

        if file_path:
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(script)
                messagebox.showinfo("Успех", f"Скрипт сохранен в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка сохранения файла:\n{str(e)}")

    def export_report(self):
        """Экспорт отчета сравнения"""
        if not self.source_schema or not self.target_schema:
            messagebox.showwarning("Ошибка", "Нет данных для экспорта")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[
                ("JSON файлы", "*.json"),
                ("Все файлы", "*.*")
            ],
            title="Экспорт отчета сравнения"
        )

        if file_path:
            try:
                report = {
                    'source_info': self.source_info.cget("text"),
                    'target_info': self.target_info.cget("text"),
                    'timestamp': datetime.now().isoformat(),
                    'source_schema': self.source_schema,
                    'target_schema': self.target_schema
                }

                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("Успех", f"Отчет экспортирован в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка экспорта отчета:\n{str(e)}")

    def save_current_schema(self):
        """Сохранить текущую схему в файл"""
        if not self.parent.db:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        try:
            schema = self.get_database_schema()

            file_path = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[
                    ("JSON файлы", "*.json"),
                    ("Все файлы", "*.*")
                ],
                title="Сохранить схему базы данных"
            )

            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(schema, f, ensure_ascii=False, indent=2)

                messagebox.showinfo("Успех", f"Схема сохранена в:\n{file_path}")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения схемы:\n{str(e)}")


# Глобальный экземпляр компаратора
schema_comparator = None


def get_schema_comparator(parent):
    """Получение или создание глобального экземпляра компаратора"""
    global schema_comparator
    if schema_comparator is None or not schema_comparator.winfo_exists():
        schema_comparator = SchemaComparator(parent)
    else:
        schema_comparator.lift()
    return schema_comparator
