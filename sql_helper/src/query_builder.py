import customtkinter as ctk
from tkinter import messagebox


class QueryBuilder(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Конструктор запросов")
        self.geometry("700x600")
        self.parent = parent

        # Переменные для хранения состояния
        self.selected_table = None
        self.selected_columns = []
        self.where_conditions = []
        self.order_by_column = None
        self.order_direction = "ASC"
        self.limit_value = ""
        self.column_vars = {}  # Инициализируем здесь

        self.create_widgets()
        self.load_tables()

    def create_widgets(self):
        # === Заголовок ===
        ctk.CTkLabel(self, text="Визуальный конструктор запросов",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # === Выбор таблицы ===
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(table_frame, text="Таблица:").pack(side="left", padx=5)
        self.table_combo = ctk.CTkComboBox(table_frame, values=[], command=self.on_table_select)
        self.table_combo.pack(side="left", padx=5)

        # === Выбор колонок ===
        ctk.CTkLabel(self, text="Колонки:", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        self.columns_frame = ctk.CTkScrollableFrame(self, height=150)
        self.columns_frame.pack(fill="x", padx=10, pady=5)

        # === Условия WHERE ===
        ctk.CTkLabel(self, text="Условия WHERE:", font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        self.where_frame = ctk.CTkFrame(self)
        self.where_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(self.where_frame, text="Добавить условие",
                      command=self.add_where_condition).pack(pady=5)

        self.where_conditions_frame = ctk.CTkScrollableFrame(self.where_frame, height=100)
        self.where_conditions_frame.pack(fill="x", padx=5, pady=5)

        # === Сортировка ===
        sort_frame = ctk.CTkFrame(self)
        sort_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(sort_frame, text="Сортировка:").pack(side="left", padx=5)
        self.sort_column_combo = ctk.CTkComboBox(sort_frame, values=[""])
        self.sort_column_combo.pack(side="left", padx=5)

        self.sort_direction = ctk.CTkComboBox(sort_frame, values=["ASC", "DESC"])
        self.sort_direction.pack(side="left", padx=5)
        self.sort_direction.set("ASC")

        # === Лимит ===
        limit_frame = ctk.CTkFrame(self)
        limit_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(limit_frame, text="Лимит:").pack(side="left", padx=5)
        self.limit_entry = ctk.CTkEntry(limit_frame, width=100)
        self.limit_entry.pack(side="left", padx=5)

        # === Кнопки управления ===
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(button_frame, text="Сгенерировать SQL",
                      command=self.generate_sql, fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Выполнить",
                      command=self.execute_query, fg_color="blue").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Закрыть",
                      command=self.destroy).pack(side="right", padx=5)

    def load_tables(self):
        """Загрузка списка таблиц"""
        if hasattr(self.parent, 'tables') and self.parent.tables:
            self.table_combo.configure(values=self.parent.tables)
            if self.parent.tables:
                self.table_combo.set(self.parent.tables[0])
                self.on_table_select(self.parent.tables[0])

    def on_table_select(self, selection):
        """Обработка выбора таблицы"""
        self.selected_table = selection
        self.load_columns_for_table(selection)

    def load_columns_for_table(self, table_name):
        """Загрузка колонок для выбранной таблицы"""
        # Очищаем предыдущие чекбоксы
        for widget in self.columns_frame.winfo_children():
            widget.destroy()

        # Очищаем сортировку
        self.sort_column_combo.configure(values=[""])
        self.sort_column_combo.set("")

        # Очищаем словарь переменных
        self.column_vars = {}

        if not self.parent.db:
            messagebox.showerror("Ошибка", "Нет подключения к базе данных")
            return

        try:
            # Получаем структуру таблицы
            query = f"DESCRIBE `{table_name}`"
            print(f"Выполняем запрос: {query}")  # Для отладки

            result = self.parent.db.execute_query(query)
            print(f"Результат: {result}")  # Для отладки

            if isinstance(result, str):
                messagebox.showerror("Ошибка", f"Ошибка выполнения запроса: {result}")
                return

            if isinstance(result, list) and result:
                # Для MySQL результат будет списком словарей с ключами 'Field', 'Type', 'Null', 'Key', 'Default', 'Extra'
                columns = []
                for row in result:
                    if 'Field' in row:
                        columns.append(row['Field'])
                    elif list(row.keys()):
                        # Если ключи другие, берем первый
                        columns.append(list(row.values())[0])

                print(f"Найденные колонки: {columns}")  # Для отладки

                # Создаем чекбоксы для колонок
                for i, column in enumerate(columns):
                    var = ctk.BooleanVar()
                    checkbox = ctk.CTkCheckBox(
                        self.columns_frame,
                        text=column,
                        variable=var
                    )
                    checkbox.pack(anchor="w", padx=10, pady=2)
                    self.column_vars[column] = var

                # Обновляем выпадающий список для сортировки
                self.sort_column_combo.configure(values=[""] + columns)

            else:
                messagebox.showwarning("Предупреждение", "Не удалось получить структуру таблицы")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки колонок: {str(e)}")
            print(f"Подробная ошибка: {e}")  # Для отладки

    def add_where_condition(self):
        """Добавление условия WHERE"""
        condition_frame = ctk.CTkFrame(self.where_conditions_frame)
        condition_frame.pack(fill="x", padx=5, pady=2)

        # Получаем колонки для текущей таблицы
        columns = list(self.column_vars.keys()) if hasattr(self, 'column_vars') and self.column_vars else [""]

        column_combo = ctk.CTkComboBox(condition_frame, values=columns, width=150)
        column_combo.pack(side="left", padx=2)

        operator_combo = ctk.CTkComboBox(condition_frame, values=["=", "!=", ">", "<", ">=", "<=", "LIKE"], width=80)
        operator_combo.pack(side="left", padx=2)
        operator_combo.set("=")

        value_entry = ctk.CTkEntry(condition_frame, width=150)
        value_entry.pack(side="left", padx=2)

        # Кнопка удаления условия
        remove_btn = ctk.CTkButton(condition_frame, text="×", width=30,
                                   command=lambda: condition_frame.destroy(),
                                   fg_color="red", hover_color="darkred")
        remove_btn.pack(side="left", padx=2)

        # Сохраняем ссылки на виджеты для генерации SQL
        if not hasattr(self, 'where_widgets'):
            self.where_widgets = []
        self.where_widgets.append({
            'frame': condition_frame,
            'column': column_combo,
            'operator': operator_combo,
            'value': value_entry
        })

    def generate_sql(self):
        """Генерация SQL-запроса"""
        if not self.selected_table:
            messagebox.showwarning("Ошибка", "Выберите таблицу")
            return ""

        # Получаем выбранные колонки
        selected_columns = []
        if hasattr(self, 'column_vars') and self.column_vars:
            for column, var in self.column_vars.items():
                if var.get():
                    selected_columns.append(column)

        # Если не выбраны колонки, выбираем все
        if not selected_columns:
            columns_str = "*"
        else:
            columns_str = ", ".join([f"`{col}`" for col in selected_columns])

        # Базовый запрос
        sql = f"SELECT {columns_str} FROM `{self.selected_table}`"

        # Добавляем WHERE условия
        where_clauses = []
        if hasattr(self, 'where_widgets') and self.where_widgets:
            for widget_data in self.where_widgets:
                try:
                    column = widget_data['column'].get()
                    operator = widget_data['operator'].get()
                    value = widget_data['value'].get()

                    if column and value:
                        # Экранируем строковые значения
                        if operator == "LIKE" or not self.is_number(value):
                            where_clauses.append(f"`{column}` {operator} '{value}'")
                        else:
                            where_clauses.append(f"`{column}` {operator} {value}")
                except Exception as e:
                    print(f"Ошибка обработки условия WHERE: {e}")
                    continue

        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        # Добавляем ORDER BY
        sort_column = self.sort_column_combo.get()
        if sort_column:
            direction = self.sort_direction.get()
            sql += f" ORDER BY `{sort_column}` {direction}"

        # Добавляем LIMIT
        limit_value = self.limit_entry.get().strip()
        if limit_value and limit_value.isdigit():
            sql += f" LIMIT {limit_value}"

        print(f"Сгенерированный SQL: {sql}")  # Для отладки

        # Открываем в основном окне
        if hasattr(self.parent, 'text_query'):
            self.parent.text_query.delete("0.0", "end")
            self.parent.text_query.insert("0.0", sql)
            self.parent.highlight_sql()

        return sql

    def is_number(self, value):
        """Проверка, является ли значение числом"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def execute_query(self):
        """Выполнение сгенерированного запроса"""
        sql = self.generate_sql()
        if sql:
            # Передаем запрос в главное окно для выполнения
            try:
                self.parent.text_query.delete("0.0", "end")
                self.parent.text_query.insert("0.0", sql)
                self.parent.highlight_sql()
                self.parent.execute_query()
                self.destroy()
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка выполнения запроса: {str(e)}")
