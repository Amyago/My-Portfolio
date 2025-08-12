import customtkinter as ctk
from tkinter import messagebox, ttk
import json


class TableEditor(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Редактор таблиц")
        self.geometry("900x700")
        self.parent = parent
        self.current_table = None
        self.table_columns = []

        self.create_widgets()
        self.load_tables()

    def create_widgets(self):
        # === Заголовок ===
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Редактор структуры таблиц",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        # === Выбор таблицы ===
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(table_frame, text="Таблица:").pack(side="left", padx=5)
        self.table_combo = ctk.CTkComboBox(table_frame, values=[], command=self.on_table_select)
        self.table_combo.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(table_frame, text="Обновить",
                      command=self.load_tables).pack(side="left", padx=5)

        ctk.CTkButton(table_frame, text="Создать таблицу",
                      command=self.create_new_table,
                      fg_color="green").pack(side="left", padx=5)

        # === Структура таблицы ===
        structure_frame = ctk.CTkFrame(self)
        structure_frame.pack(fill="both", expand=True, padx=10, pady=5)

        ctk.CTkLabel(structure_frame, text="Структура таблицы:",
                     font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=10, pady=5)

        # Создаем таблицу для отображения колонок
        self.columns_tree = ttk.Treeview(structure_frame)
        self.columns_tree.pack(fill="both", expand=True, padx=10, pady=5)

        # Добавляем скроллбары
        vsb = ttk.Scrollbar(structure_frame, orient="vertical", command=self.columns_tree.yview)
        vsb.pack(side='right', fill='y')
        self.columns_tree.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(structure_frame, orient="horizontal", command=self.columns_tree.xview)
        hsb.pack(side='bottom', fill='x')
        self.columns_tree.configure(xscrollcommand=hsb.set)

        # Настройка колонок
        self.columns_tree["columns"] = ("name", "type", "null", "key", "default", "extra")
        self.columns_tree["show"] = "headings"

        self.columns_tree.heading("name", text="Имя")
        self.columns_tree.heading("type", text="Тип")
        self.columns_tree.heading("null", text="NULL")
        self.columns_tree.heading("key", text="Ключ")
        self.columns_tree.heading("default", text="По умолчанию")
        self.columns_tree.heading("extra", text="Дополнительно")

        self.columns_tree.column("name", width=150)
        self.columns_tree.column("type", width=120)
        self.columns_tree.column("null", width=60)
        self.columns_tree.column("key", width=80)
        self.columns_tree.column("default", width=120)
        self.columns_tree.column("extra", width=100)

        # Привязываем событие двойного клика
        self.columns_tree.bind("<Double-1>", self.edit_column)

        # === Кнопки управления колонками ===
        column_buttons_frame = ctk.CTkFrame(self)
        column_buttons_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkButton(column_buttons_frame, text="Добавить колонку",
                      command=self.add_column,
                      fg_color="green").pack(side="left", padx=5)

        ctk.CTkButton(column_buttons_frame, text="Редактировать",
                      command=self.edit_selected_column).pack(side="left", padx=5)

        ctk.CTkButton(column_buttons_frame, text="Удалить колонку",
                      command=self.delete_column,
                      fg_color="red").pack(side="left", padx=5)

        # === Кнопки управления таблицей ===
        table_buttons_frame = ctk.CTkFrame(self)
        table_buttons_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkButton(table_buttons_frame, text="Сохранить изменения",
                      command=self.save_changes,
                      fg_color="green",
                      font=ctk.CTkFont(weight="bold")).pack(side="left", padx=5)

        ctk.CTkButton(table_buttons_frame, text="Отменить",
                      command=self.cancel_changes).pack(side="left", padx=5)

        ctk.CTkButton(table_buttons_frame, text="Удалить таблицу",
                      command=self.drop_table,
                      fg_color="red").pack(side="right", padx=5)

    def load_tables(self):
        """Загрузка списка таблиц"""
        if hasattr(self.parent, 'tables') and self.parent.tables:
            self.table_combo.configure(values=self.parent.tables)
            if self.parent.tables and not self.current_table:
                self.table_combo.set(self.parent.tables[0])
                self.on_table_select(self.parent.tables[0])

    def on_table_select(self, selection):
        """Обработка выбора таблицы"""
        self.current_table = selection
        self.load_table_structure(selection)

    def load_table_structure(self, table_name):
        """Загрузка структуры таблицы"""
        if not self.parent.db:
            return

        try:
            # Очищаем предыдущие данные
            for item in self.columns_tree.get_children():
                self.columns_tree.delete(item)

            # Получаем структуру таблицы
            result = self.parent.db.execute_query(f"DESCRIBE `{table_name}`")

            if isinstance(result, list):
                self.table_columns = []
                for row in result:
                    column_info = {
                        'name': row.get('Field', ''),
                        'type': row.get('Type', ''),
                        'null': row.get('Null', ''),
                        'key': row.get('Key', ''),
                        'default': row.get('Default', None),
                        'extra': row.get('Extra', '')
                    }
                    self.table_columns.append(column_info)

                    # Добавляем в таблицу
                    self.columns_tree.insert("", "end", values=(
                        column_info['name'],
                        column_info['type'],
                        column_info['null'],
                        column_info['key'],
                        str(column_info['default']) if column_info['default'] is not None else '',
                        column_info['extra']
                    ))

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки структуры таблицы:\n{str(e)}")

    def create_new_table(self):
        """Создание новой таблицы"""
        dialog = CreateTableDialog(self)
        table_name = dialog.get_result()

        if table_name:
            try:
                # Создаем пустую таблицу
                sql = f"CREATE TABLE `{table_name}` (id INT AUTO_INCREMENT PRIMARY KEY)"
                result = self.parent.db.execute_query(sql)

                if isinstance(result, str) and result.startswith("Ошибка"):
                    messagebox.showerror("Ошибка", result)
                else:
                    messagebox.showinfo("Успех", f"Таблица '{table_name}' создана")
                    # Обновляем список таблиц
                    self.parent.update_table_list()
                    self.load_tables()
                    # Выбираем новую таблицу
                    self.table_combo.set(table_name)
                    self.on_table_select(table_name)

            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка создания таблицы:\n{str(e)}")

    def add_column(self):
        """Добавление новой колонки"""
        if not self.current_table:
            messagebox.showwarning("Ошибка", "Выберите таблицу")
            return

        dialog = ColumnEditorDialog(self, "Добавить колонку")
        column_data = dialog.get_result()

        if column_data:
            self.table_columns.append(column_data)
            self.refresh_columns_display()

    def edit_selected_column(self):
        """Редактирование выбранной колонки"""
        selected = self.columns_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите колонку для редактирования")
            return

        item = selected[0]
        item_index = self.columns_tree.index(item)

        if 0 <= item_index < len(self.table_columns):
            dialog = ColumnEditorDialog(self, "Редактировать колонку", self.table_columns[item_index])
            column_data = dialog.get_result()

            if column_data:
                self.table_columns[item_index] = column_data
                self.refresh_columns_display()

    def edit_column(self, event):
        """Редактирование колонки по двойному клику"""
        self.edit_selected_column()

    def delete_column(self):
        """Удаление выбранной колонки"""
        selected = self.columns_tree.selection()
        if not selected:
            messagebox.showwarning("Ошибка", "Выберите колонку для удаления")
            return

        if not messagebox.askyesno("Подтверждение", "Удалить выбранную колонку?"):
            return

        item = selected[0]
        item_index = self.columns_tree.index(item)

        if 0 <= item_index < len(self.table_columns):
            del self.table_columns[item_index]
            self.refresh_columns_display()

    def refresh_columns_display(self):
        """Обновление отображения колонок"""
        # Очищаем таблицу
        for item in self.columns_tree.get_children():
            self.columns_tree.delete(item)

        # Добавляем обновленные данные
        for column in self.table_columns:
            self.columns_tree.insert("", "end", values=(
                column['name'],
                column['type'],
                column['null'],
                column['key'],
                str(column['default']) if column['default'] is not None else '',
                column['extra']
            ))

    def save_changes(self):
        """Сохранение изменений"""
        if not self.current_table or not self.table_columns:
            messagebox.showwarning("Ошибка", "Нет изменений для сохранения")
            return

        try:
            # Генерируем SQL для изменения структуры таблицы
            changes = self.generate_alter_statements()

            if not changes:
                messagebox.showinfo("Информация", "Нет изменений для применения")
                return

            # Выполняем изменения
            success_count = 0
            error_count = 0

            for sql in changes:
                result = self.parent.db.execute_query(sql)
                if isinstance(result, str) and result.startswith("Ошибка"):
                    error_count += 1
                    print(f"Ошибка выполнения: {sql} - {result}")
                else:
                    success_count += 1

            if error_count == 0:
                messagebox.showinfo("Успех", f"Изменения успешно применены ({success_count} операций)")
                # Перезагружаем структуру
                self.load_table_structure(self.current_table)
                # Обновляем список таблиц в основном окне
                self.parent.update_table_list()
            else:
                messagebox.showwarning("Частичный успех",
                                       f"Применено {success_count} из {success_count + error_count} изменений")

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка сохранения изменений:\n{str(e)}")

    def generate_alter_statements(self):
        """Генерация SQL-заявлений ALTER TABLE"""
        statements = []

        if not self.current_table:
            return statements

        # Получаем оригинальную структуру таблицы
        original_result = self.parent.db.execute_query(f"DESCRIBE `{self.current_table}`")
        original_columns = []

        if isinstance(original_result, list):
            for row in original_result:
                original_columns.append({
                    'name': row.get('Field', ''),
                    'type': row.get('Type', ''),
                    'null': row.get('Null', ''),
                    'key': row.get('Key', ''),
                    'default': row.get('Default', None),
                    'extra': row.get('Extra', '')
                })

        # Создаем словари для быстрого поиска
        original_dict = {col['name']: col for col in original_columns}
        current_dict = {col['name']: col for col in self.table_columns}

        # Находим новые колонки
        new_columns = set(current_dict.keys()) - set(original_dict.keys())
        for col_name in new_columns:
            col = current_dict[col_name]
            sql = self.generate_add_column_sql(col)
            statements.append(sql)

        # Находим удаленные колонки
        removed_columns = set(original_dict.keys()) - set(current_dict.keys())
        for col_name in removed_columns:
            sql = f"ALTER TABLE `{self.current_table}` DROP COLUMN `{col_name}`"
            statements.append(sql)

        # Находим измененные колонки
        common_columns = set(original_dict.keys()) & set(current_dict.keys())
        for col_name in common_columns:
            orig_col = original_dict[col_name]
            curr_col = current_dict[col_name]

            # Сравниваем свойства
            if (orig_col['type'] != curr_col['type'] or
                    orig_col['null'] != curr_col['null'] or
                    orig_col['default'] != curr_col['default'] or
                    orig_col['extra'] != curr_col['extra']):
                sql = self.generate_modify_column_sql(curr_col)
                statements.append(sql)

        return statements

    def generate_add_column_sql(self, column):
        """Генерация SQL для добавления колонки"""
        sql = f"ALTER TABLE `{self.current_table}` ADD COLUMN `{column['name']}` {column['type']}"

        if column['null'] == 'NO':
            sql += " NOT NULL"
        else:
            sql += " NULL"

        if column['default'] is not None:
            if isinstance(column['default'], str):
                sql += f" DEFAULT '{column['default']}'"
            else:
                sql += f" DEFAULT {column['default']}"

        if column['extra']:
            sql += f" {column['extra']}"

        return sql

    def generate_modify_column_sql(self, column):
        """Генерация SQL для изменения колонки"""
        sql = f"ALTER TABLE `{self.current_table}` MODIFY COLUMN `{column['name']}` {column['type']}"

        if column['null'] == 'NO':
            sql += " NOT NULL"
        else:
            sql += " NULL"

        if column['default'] is not None:
            if isinstance(column['default'], str):
                sql += f" DEFAULT '{column['default']}'"
            else:
                sql += f" DEFAULT {column['default']}"

        if column['extra']:
            sql += f" {column['extra']}"

        return sql

    def cancel_changes(self):
        """Отмена изменений"""
        if self.current_table:
            self.load_table_structure(self.current_table)
            messagebox.showinfo("Информация", "Изменения отменены")

    def drop_table(self):
        """Удаление таблицы"""
        if not self.current_table:
            messagebox.showwarning("Ошибка", "Выберите таблицу")
            return

        if not messagebox.askyesno("Подтверждение",
                                   f"Удалить таблицу '{self.current_table}'?\n"
                                   "Это действие нельзя отменить!"):
            return

        try:
            sql = f"DROP TABLE `{self.current_table}`"
            result = self.parent.db.execute_query(sql)

            if isinstance(result, str) and result.startswith("Ошибка"):
                messagebox.showerror("Ошибка", result)
            else:
                messagebox.showinfo("Успех", f"Таблица '{self.current_table}' удалена")
                # Обновляем список таблиц
                self.parent.update_table_list()
                self.load_tables()
                # Очищаем отображение
                self.current_table = None
                for item in self.columns_tree.get_children():
                    self.columns_tree.delete(item)
                self.table_columns = []

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка удаления таблицы:\n{str(e)}")


class CreateTableDialog:
    def __init__(self, parent):
        self.parent = parent
        self.result = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Создать таблицу")
        self.dialog.geometry("400x150")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.dialog.wait_window()

    def create_widgets(self):
        ctk.CTkLabel(self.dialog, text="Имя новой таблицы:").pack(pady=10)

        self.name_entry = ctk.CTkEntry(self.dialog, width=300)
        self.name_entry.pack(pady=5)
        self.name_entry.focus()

        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(pady=10)

        ctk.CTkButton(button_frame, text="Создать",
                      command=self.ok,
                      fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Отмена",
                      command=self.cancel).pack(side="left", padx=5)

        # Привязываем Enter
        self.name_entry.bind("<Return>", lambda e: self.ok())

    def ok(self):
        table_name = self.name_entry.get().strip()
        if table_name:
            self.result = table_name
            self.dialog.destroy()
        else:
            messagebox.showwarning("Ошибка", "Введите имя таблицы")

    def cancel(self):
        self.dialog.destroy()

    def get_result(self):
        return self.result


class ColumnEditorDialog:
    def __init__(self, parent, title, column_data=None):
        self.parent = parent
        self.result = None
        self.column_data = column_data or {
            'name': '',
            'type': 'VARCHAR(255)',
            'null': 'YES',
            'key': '',
            'default': None,
            'extra': ''
        }

        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("500x400")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.dialog.wait_window()

    def create_widgets(self):
        # Имя колонки
        ctk.CTkLabel(self.dialog, text="Имя колонки:").pack(anchor="w", padx=10, pady=(10, 5))
        self.name_entry = ctk.CTkEntry(self.dialog, width=400)
        self.name_entry.pack(padx=10)
        self.name_entry.insert(0, self.column_data['name'])

        # Тип данных
        ctk.CTkLabel(self.dialog, text="Тип данных:").pack(anchor="w", padx=10, pady=(10, 5))
        self.type_combo = ctk.CTkComboBox(self.dialog, values=[
            "INT", "VARCHAR(255)", "TEXT", "DATE", "DATETIME", "BOOLEAN",
            "DECIMAL(10,2)", "FLOAT", "DOUBLE", "TINYINT", "BIGINT",
            "CHAR(10)", "VARCHAR(100)", "VARCHAR(500)", "LONGTEXT"
        ])
        self.type_combo.pack(padx=10, fill="x")
        self.type_combo.set(self.column_data['type'])

        # NULL
        self.null_var = ctk.BooleanVar(value=self.column_data['null'] == 'YES')
        ctk.CTkCheckBox(self.dialog, text="Может быть NULL",
                        variable=self.null_var).pack(anchor="w", padx=10, pady=5)

        # Значение по умолчанию
        ctk.CTkLabel(self.dialog, text="Значение по умолчанию:").pack(anchor="w", padx=10, pady=(10, 5))
        self.default_entry = ctk.CTkEntry(self.dialog, width=400)
        self.default_entry.pack(padx=10)
        if self.column_data['default'] is not None:
            self.default_entry.insert(0, str(self.column_data['default']))

        # Дополнительно (AUTO_INCREMENT, UNIQUE и т.д.)
        ctk.CTkLabel(self.dialog, text="Дополнительно:").pack(anchor="w", padx=10, pady=(10, 5))
        self.extra_entry = ctk.CTkEntry(self.dialog, width=400)
        self.extra_entry.pack(padx=10)
        self.extra_entry.insert(0, self.column_data['extra'])

        # Кнопки
        button_frame = ctk.CTkFrame(self.dialog)
        button_frame.pack(pady=20)

        ctk.CTkButton(button_frame, text="Сохранить",
                      command=self.ok,
                      fg_color="green").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Отмена",
                      command=self.cancel).pack(side="left", padx=5)

    def ok(self):
        name = self.name_entry.get().strip()
        if not name:
            messagebox.showwarning("Ошибка", "Введите имя колонки")
            return

        # Получаем значения
        default_value = self.default_entry.get().strip()
        if not default_value:
            default_value = None

        self.result = {
            'name': name,
            'type': self.type_combo.get(),
            'null': 'YES' if self.null_var.get() else 'NO',
            'key': '',  # Ключи управляются отдельно
            'default': default_value,
            'extra': self.extra_entry.get().strip()
        }

        self.dialog.destroy()

    def cancel(self):
        self.dialog.destroy()

    def get_result(self):
        return self.result


# Глобальный экземпляр редактора таблиц
table_editor = None


def get_table_editor(parent):
    """Получение или создание глобального экземпляра редактора таблиц"""
    global table_editor
    if table_editor is None or not table_editor.winfo_exists():
        table_editor = TableEditor(parent)
    else:
        table_editor.lift()
    return table_editor
