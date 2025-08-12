import customtkinter as ctk
from tkinter import filedialog, messagebox
import pandas as pd
import sqlite3
from datetime import datetime
import os


class DataImporter(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Импорт данных")
        self.geometry("800x700")
        self.parent = parent
        self.df = None
        self.file_path = None

        self.create_widgets()

    def create_widgets(self):
        # === Заголовок ===
        ctk.CTkLabel(self, text="Импорт данных в таблицу",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)

        # === Выбор файла ===
        file_frame = ctk.CTkFrame(self)
        file_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(file_frame, text="Файл данных:").pack(side="left", padx=5)
        self.file_entry = ctk.CTkEntry(file_frame, width=400)
        self.file_entry.pack(side="left", padx=5, fill="x", expand=True)

        ctk.CTkButton(file_frame, text="Обзор...",
                      command=self.browse_file).pack(side="left", padx=5)

        # === Информация о файле ===
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=10, pady=5)

        self.file_info_label = ctk.CTkLabel(self.info_frame, text="Файл не выбран")
        self.file_info_label.pack(padx=10, pady=10)

        # === Предварительный просмотр ===
        ctk.CTkLabel(self, text="Предварительный просмотр:",
                     font=ctk.CTkFont(weight="bold")).pack(pady=(10, 5))

        # Создаем фрейм для таблицы предпросмотра
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Создаем Treeview для предварительного просмотра
        self.tree_preview = ctk.CTkScrollableFrame(preview_frame)
        self.tree_preview.pack(fill="both", expand=True, padx=5, pady=5)

        # === Настройки импорта ===
        settings_frame = ctk.CTkFrame(self)
        settings_frame.pack(fill="x", padx=10, pady=5)

        # Выбор таблицы
        table_select_frame = ctk.CTkFrame(settings_frame)
        table_select_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkLabel(table_select_frame, text="Целевая таблица:").pack(side="left", padx=5)
        self.table_combo = ctk.CTkComboBox(table_select_frame, values=[""])
        self.table_combo.pack(side="left", padx=5)

        ctk.CTkButton(table_select_frame, text="Обновить список",
                      command=self.refresh_tables).pack(side="left", padx=5)

        # Создание новой таблицы
        new_table_frame = ctk.CTkFrame(settings_frame)
        new_table_frame.pack(fill="x", padx=5, pady=5)

        self.create_table_var = ctk.BooleanVar()
        self.create_table_check = ctk.CTkCheckBox(
            new_table_frame,
            text="Создать новую таблицу",
            variable=self.create_table_var,
            command=self.toggle_create_table
        )
        self.create_table_check.pack(side="left", padx=5)

        self.table_name_entry = ctk.CTkEntry(new_table_frame, placeholder_text="Имя новой таблицы")
        self.table_name_entry.pack(side="left", padx=5)
        self.table_name_entry.pack_forget()  # Скрываем по умолчанию

        # Опции импорта
        options_frame = ctk.CTkFrame(settings_frame)
        options_frame.pack(fill="x", padx=5, pady=5)

        self.header_var = ctk.BooleanVar(value=True)
        ctk.CTkCheckBox(options_frame, text="Первая строка содержит заголовки",
                        variable=self.header_var).pack(side="left", padx=5)

        # === Кнопки управления ===
        button_frame = ctk.CTkFrame(self)
        button_frame.pack(fill="x", padx=10, pady=10)

        self.btn_import = ctk.CTkButton(button_frame, text="Импортировать данные",
                                        command=self.import_data,
                                        fg_color="green",
                                        state="disabled")
        self.btn_import.pack(side="left", padx=5)

        ctk.CTkButton(button_frame, text="Закрыть",
                      command=self.destroy).pack(side="right", padx=5)

    def browse_file(self):
        """Выбор файла для импорта"""
        file_path = filedialog.askopenfilename(
            title="Выберите файл для импорта",
            filetypes=[
                ("Все поддерживаемые файлы", "*.csv;*.xlsx;*.xls"),
                ("CSV файлы", "*.csv"),
                ("Excel файлы", "*.xlsx;*.xls"),
                ("Все файлы", "*.*")
            ]
        )

        if file_path:
            self.file_entry.delete(0, "end")
            self.file_entry.insert(0, file_path)
            self.load_file(file_path)

    def load_file(self, file_path):
        """Загрузка файла и отображение предпросмотра"""
        try:
            self.file_path = file_path

            # Определяем тип файла и загружаем данные
            if file_path.lower().endswith('.csv'):
                self.df = pd.read_csv(file_path)
            elif file_path.lower().endswith(('.xlsx', '.xls')):
                self.df = pd.read_excel(file_path)
            else:
                raise ValueError("Неподдерживаемый формат файла")

            # Отображаем информацию о файле
            rows, cols = self.df.shape
            file_size = os.path.getsize(file_path)
            file_size_str = self.format_file_size(file_size)

            info_text = f"Файл: {os.path.basename(file_path)}\n"
            info_text += f"Размер: {file_size_str}\n"
            info_text += f"Строк: {rows}, Колонок: {cols}"

            self.file_info_label.configure(text=info_text)

            # Отображаем предварительный просмотр
            self.show_preview()

            # Активируем кнопку импорта
            self.btn_import.configure(state="normal")

            # Обновляем список таблиц
            self.refresh_tables()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки файла:\n{str(e)}")
            self.btn_import.configure(state="disabled")

    def format_file_size(self, size_bytes):
        """Форматирование размера файла"""
        if size_bytes < 1024:
            return f"{size_bytes} байт"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} КБ"
        else:
            return f"{size_bytes / (1024 * 1024):.1f} МБ"

    def show_preview(self):
        """Отображение предварительного просмотра данных"""
        # Очищаем предыдущий предпросмотр
        for widget in self.tree_preview.winfo_children():
            widget.destroy()

        if self.df is None or self.df.empty:
            ctk.CTkLabel(self.tree_preview, text="Нет данных для отображения").pack(padx=10, pady=10)
            return

        # Создаем таблицу для предпросмотра (первые 10 строк)
        preview_df = self.df.head(10)

        # Создаем заголовки
        header_frame = ctk.CTkFrame(self.tree_preview)
        header_frame.pack(fill="x", padx=2, pady=1)

        for col in preview_df.columns:
            ctk.CTkLabel(header_frame, text=str(col),
                         font=ctk.CTkFont(weight="bold"),
                         width=120).pack(side="left", padx=2, pady=2)

        # Создаем строки данных
        for index, row in preview_df.iterrows():
            row_frame = ctk.CTkFrame(self.tree_preview)
            row_frame.pack(fill="x", padx=2, pady=1)

            for value in row:
                ctk.CTkLabel(row_frame, text=str(value)[:30],
                             width=120).pack(side="left", padx=2, pady=2)

    def refresh_tables(self):
        """Обновление списка таблиц"""
        if hasattr(self.parent, 'tables') and self.parent.tables:
            self.table_combo.configure(values=self.parent.tables)
            if self.parent.tables:
                self.table_combo.set(self.parent.tables[0])

    def toggle_create_table(self):
        """Переключение режима создания таблицы"""
        if self.create_table_var.get():
            self.table_combo.pack_forget()
            self.table_name_entry.pack(side="left", padx=5)
        else:
            self.table_name_entry.pack_forget()
            self.table_combo.pack(side="left", padx=5)

    def import_data(self):
        """Импорт данных в базу"""
        if not self.parent.db or not self.parent.db.connection:
            messagebox.showwarning("Ошибка", "Нет подключения к базе данных")
            return

        if self.df is None:
            messagebox.showwarning("Ошибка", "Нет данных для импорта")
            return

        try:
            # Определяем целевую таблицу
            if self.create_table_var.get():
                table_name = self.table_name_entry.get().strip()
                if not table_name:
                    messagebox.showwarning("Ошибка", "Введите имя новой таблицы")
                    return
                # Создаем таблицу
                self.create_table_from_dataframe(table_name)
            else:
                table_name = self.table_combo.get()
                if not table_name:
                    messagebox.showwarning("Ошибка", "Выберите целевую таблицу")
                    return

            # Импортируем данные
            rows_imported = self.insert_data_to_table(table_name)

            messagebox.showinfo("Успех",
                                f"Данные успешно импортированы!\n"
                                f"Импортировано строк: {rows_imported}")

            # Обновляем список таблиц в основном окне
            self.parent.update_table_list()

            # Закрываем окно импорта
            self.destroy()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка импорта данных:\n{str(e)}")

    def create_table_from_dataframe(self, table_name):
        """Создание таблицы на основе структуры DataFrame"""
        if self.df is None:
            return

        # Определяем типы данных для колонок
        column_definitions = []

        for column in self.df.columns:
            # Определяем тип данных
            sample_value = self.df[column].dropna().iloc[0] if not self.df[column].dropna().empty else None

            if sample_value is not None:
                if isinstance(sample_value, (int, float)):
                    if isinstance(sample_value, int):
                        col_type = "INT"
                    else:
                        col_type = "DOUBLE"
                elif isinstance(sample_value, bool):
                    col_type = "BOOLEAN"
                else:
                    # Для строк определяем максимальную длину
                    max_length = self.df[column].astype(str).str.len().max()
                    if max_length > 255:
                        col_type = "TEXT"
                    else:
                        col_type = f"VARCHAR({max(max_length, 50)})"
            else:
                col_type = "VARCHAR(255)"

            column_definitions.append(f"`{column}` {col_type}")

        # Создаем SQL-запрос для создания таблицы
        columns_sql = ",\n    ".join(column_definitions)
        create_sql = f"CREATE TABLE `{table_name}` (\n    {columns_sql}\n)"

        # Выполняем создание таблицы
        result = self.parent.db.execute_query(create_sql)
        if isinstance(result, str) and result.startswith("Ошибка"):
            raise Exception(result)

    def insert_data_to_table(self, table_name):
        """Вставка данных в таблицу"""
        if self.df is None:
            return 0

        # Подготавливаем данные для вставки
        rows_imported = 0

        # Преобразуем DataFrame в список словарей
        data_dicts = self.df.to_dict('records')

        # Создаем курсор для пакетной вставки
        try:
            with self.parent.db.connection.cursor() as cursor:
                for record in data_dicts:
                    # Подготавливаем значения
                    columns = list(record.keys())
                    values = []
                    placeholders = []

                    for col in columns:
                        value = record[col]
                        if pd.isna(value):
                            values.append(None)
                            placeholders.append("NULL")
                        elif isinstance(value, str):
                            values.append(value)
                            placeholders.append("%s")
                        elif isinstance(value, (int, float)):
                            values.append(value)
                            placeholders.append("%s")
                        elif isinstance(value, bool):
                            values.append(int(value))
                            placeholders.append("%s")
                        else:
                            values.append(str(value))
                            placeholders.append("%s")

                    # Создаем SQL-запрос
                    columns_str = ", ".join([f"`{col}`" for col in columns])
                    placeholders_str = ", ".join(placeholders)
                    insert_sql = f"INSERT INTO `{table_name}` ({columns_str}) VALUES ({placeholders_str})"

                    # Выполняем вставку
                    cursor.execute(insert_sql, values)
                    rows_imported += 1

                # Коммитим изменения
                self.parent.db.connection.commit()

        except Exception as e:
            self.parent.db.connection.rollback()
            raise Exception(f"Ошибка вставки данных: {str(e)}")

        return rows_imported
