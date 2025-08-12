import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import json
import os
from datetime import datetime


class MultiTableEditor(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Многотабличный редактор")
        self.geometry("1200x800")
        self.parent = parent

        # Хранилище для компонентов вкладок
        self.query_editors = {}  # Текстовые редакторы
        self.result_areas = {}  # Области результатов
        self.status_labels = {}  # Статусные строки
        self.tab_counter = 1

        self.create_widgets()
        self.create_new_tab()

    def create_widgets(self):
        # === Заголовок и управление сессиями ===
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Многотабличный редактор",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        # Кнопки управления сессиями
        session_frame = ctk.CTkFrame(header_frame)
        session_frame.pack(side="right")

        ctk.CTkButton(session_frame, text="Новая вкладка",
                      command=self.create_new_tab,
                      fg_color="green").pack(side="left", padx=2)

        ctk.CTkButton(session_frame, text="Сохранить сессию",
                      command=self.save_session).pack(side="left", padx=2)

        ctk.CTkButton(session_frame, text="Загрузить сессию",
                      command=self.load_session).pack(side="left", padx=2)

        # === Вкладки ===
        self.tab_control = ctk.CTkTabview(self)
        self.tab_control.pack(fill="both", expand=True, padx=10, pady=5)

    def create_new_tab(self, tab_name=None, query_data=None):
        """Создание новой вкладки"""
        if tab_name is None:
            tab_name = f"Запрос {self.tab_counter}"
            self.tab_counter += 1

        # Создаем вкладку
        tab = self.tab_control.add(tab_name)

        # Создаем содержимое вкладки
        self.create_tab_content(tab, tab_name, query_data)

        # Переключаемся на новую вкладку
        self.tab_control.set(tab_name)

        return tab_name

    def create_tab_content(self, tab, tab_name, query_data=None):
        """Создание содержимого вкладки"""
        # === Панель инструментов вкладки ===
        toolbar_frame = ctk.CTkFrame(tab)
        toolbar_frame.pack(fill="x", padx=5, pady=5)

        ctk.CTkButton(toolbar_frame, text="Выполнить",
                      command=lambda: self.execute_query(tab_name),
                      fg_color="green").pack(side="left", padx=2)

        ctk.CTkButton(toolbar_frame, text="Проверить",
                      command=lambda: self.validate_query(tab_name)).pack(side="left", padx=2)

        ctk.CTkButton(toolbar_frame, text="Очистить",
                      command=lambda: self.clear_query(tab_name)).pack(side="left", padx=2)

        ctk.CTkButton(toolbar_frame, text="Закрыть вкладку",
                      command=lambda: self.close_tab(tab_name),
                      fg_color="red").pack(side="right", padx=2)

        # === Область редактора SQL ===
        ctk.CTkLabel(tab, text="SQL запрос:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(10, 5))

        editor_frame = ctk.CTkFrame(tab)
        editor_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Текстовый редактор
        text_widget = ctk.CTkTextbox(editor_frame, height=150)
        text_widget.pack(fill="both", expand=True, padx=2, pady=2)

        # Если есть данные запроса, загружаем их
        if query_data and "query" in query_data:
            text_widget.delete("0.0", "end")
            text_widget.insert("0.0", query_data["query"])

        # Сохраняем ссылку на редактор
        self.query_editors[tab_name] = text_widget

        # === Область результатов ===
        ctk.CTkLabel(tab, text="Результаты:", font=ctk.CTkFont(weight="bold")).pack(anchor="w", padx=5, pady=(10, 5))

        results_frame = ctk.CTkFrame(tab)
        results_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Создаем Treeview для отображения результатов
        tree_widget = ttk.Treeview(results_frame)
        tree_widget.pack(fill="both", expand=True, padx=2, pady=2)

        # Добавляем скроллбары
        vsb = ttk.Scrollbar(results_frame, orient="vertical", command=tree_widget.yview)
        vsb.pack(side='right', fill='y')
        tree_widget.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(results_frame, orient="horizontal", command=tree_widget.xview)
        hsb.pack(side='bottom', fill='x')
        tree_widget.configure(xscrollcommand=hsb.set)

        # Сохраняем ссылку на область результатов
        self.result_areas[tab_name] = tree_widget

        # === Статусная строка ===
        status_frame = ctk.CTkFrame(tab)
        status_frame.pack(fill="x", padx=5, pady=2)

        status_label = ctk.CTkLabel(status_frame, text="Готов", font=ctk.CTkFont(size=12))
        status_label.pack(side="left", padx=5)

        # Сохраняем ссылку на статусную строку
        self.status_labels[tab_name] = status_label

    def execute_query(self, tab_name):
        """Выполнение запроса из вкладки"""
        if not self.parent.db:
            self.show_error("Нет подключения к базе данных")
            return

        # Получаем SQL запрос
        if tab_name not in self.query_editors:
            return

        query = self.query_editors[tab_name].get("0.0", "end").strip()
        if not query:
            self.show_warning("Введите SQL запрос")
            return

        try:
            # Выполняем запрос
            result = self.parent.db.execute_query(query)

            # Отображаем результаты
            self.display_results(tab_name, result)

            # Обновляем статус
            self.update_status(tab_name, "Запрос выполнен успешно")

        except Exception as e:
            self.show_error(f"Ошибка выполнения запроса:\n{str(e)}")
            self.update_status(tab_name, f"Ошибка: {str(e)}")

    def display_results(self, tab_name, result):
        """Отображение результатов в области результатов"""
        if tab_name not in self.result_areas:
            return

        tree_widget = self.result_areas[tab_name]

        # Очищаем предыдущие результаты
        for item in tree_widget.get_children():
            tree_widget.delete(item)

        # Отображаем результаты
        if isinstance(result, str):
            # Сообщение об ошибке или успехе
            tree_widget["columns"] = ("message",)
            tree_widget.heading("message", text="Сообщение")
            tree_widget.insert("", "end", values=(result,))
        elif isinstance(result, list) and result:
            # Таблица с данными
            if result:
                # Получаем колонки
                columns = list(result[0].keys()) if result else []

                # Настраиваем колонки
                tree_widget["columns"] = columns
                tree_widget["show"] = "headings"

                for col in columns:
                    tree_widget.heading(col, text=col)
                    tree_widget.column(col, width=100)

                # Добавляем данные
                for row in rows:
                    values = [str(row.get(col, "")) for col in columns]
                    tree_widget.insert("", "end", values=values)
        else:
            # Нет данных
            tree_widget["columns"] = ("message",)
            tree_widget.heading("message", text="Сообщение")
            tree_widget.insert("", "end", values=("Нет данных для отображения",))

    def validate_query(self, tab_name):
        """Проверка SQL запроса"""
        if not self.parent.db:
            self.show_error("Нет подключения к базе данных")
            return

        # Получаем SQL запрос
        if tab_name not in self.query_editors:
            return

        query = self.query_editors[tab_name].get("0.0", "end").strip()
        if not query:
            self.show_warning("Введите SQL запрос")
            return

        try:
            # Проверяем запрос
            is_valid, message = self.parent.db.validate_query(query)
            if is_valid:
                self.show_info("✅ Запрос корректен")
                self.update_status(tab_name, "Запрос корректен")
            else:
                self.show_warning(f"❌ {message}")
                self.update_status(tab_name, f"Ошибка: {message}")
        except Exception as e:
            self.show_error(f"Ошибка проверки запроса:\n{str(e)}")

    def clear_query(self, tab_name):
        """Очистка редактора запросов"""
        if tab_name in self.query_editors:
            self.query_editors[tab_name].delete("0.0", "end")
            self.update_status(tab_name, "Редактор очищен")

    def close_tab(self, tab_name):
        """Закрытие вкладки"""
        # Проверяем, что это не последняя вкладка
        if len(self.tab_control._tab_dict) <= 1:
            self.show_warning("Нельзя закрыть последнюю вкладку")
            return

        # Удаляем данные вкладки
        if tab_name in self.query_editors:
            del self.query_editors[tab_name]
        if tab_name in self.result_areas:
            del self.result_areas[tab_name]
        if tab_name in self.status_labels:
            del self.status_labels[tab_name]

        # Закрываем вкладку
        self.tab_control.delete(tab_name)

    def update_status(self, tab_name, message):
        """Обновление статусной строки"""
        if tab_name in self.status_labels:
            self.status_labels[tab_name].configure(text=message)

    def save_session(self):
        """Сохранение текущей сессии"""
        # Диалог ввода имени сессии
        dialog = ctk.CTkInputDialog(text="Введите имя сессии:", title="Сохранить сессию")
        session_name = dialog.get_input()

        if not session_name:
            return

        try:
            # Собираем данные всех вкладок
            session_data = {
                "name": session_name,
                "created_at": datetime.now().isoformat(),
                "tabs": []
            }

            # Сохраняем данные каждой вкладки
            for tab_name in self.tab_control.tab_names:
                if tab_name in self.query_editors:
                    tab_data = {
                        "name": tab_name,
                        "query": self.query_editors[tab_name].get("0.0", "end").strip()
                    }
                    session_data["tabs"].append(tab_data)

            # Загружаем существующие сессии
            sessions = self.load_sessions_from_file()
            sessions[session_name] = session_data

            # Сохраняем сессии в файл
            with open("editor_sessions.json", "w", encoding="utf-8") as f:
                json.dump(sessions, f, ensure_ascii=False, indent=2)

            self.show_info(f"Сессия '{session_name}' сохранена")

        except Exception as e:
            self.show_error(f"Ошибка сохранения сессии:\n{str(e)}")

    def load_session(self):
        """Загрузка сессии"""
        sessions = self.load_sessions_from_file()
        if not sessions:
            self.show_info("Нет сохраненных сессий")
            return

        # Создаем диалог выбора сессии
        session_names = list(sessions.keys())
        dialog = SessionSelectDialog(self, session_names)
        selected_session = dialog.get_selection()

        if not selected_session:
            return

        try:
            session_data = sessions[selected_session]

            # Закрываем все текущие вкладки
            tab_names = list(self.tab_control.tab_names)
            for tab_name in tab_names:
                self.close_tab(tab_name)

            # Создаем вкладки из сессии
            for tab_data in session_data["tabs"]:
                self.create_new_tab(tab_data["name"], tab_data)

            self.show_info(f"Сессия '{selected_session}' загружена")

        except Exception as e:
            self.show_error(f"Ошибка загрузки сессии:\n{str(e)}")

    def load_sessions_from_file(self):
        """Загрузка сессий из файла"""
        if os.path.exists("editor_sessions.json"):
            try:
                with open("editor_sessions.json", "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки сессий: {e}")
                return {}
        return {}

    def show_error(self, message):
        """Показать сообщение об ошибке"""
        messagebox.showerror("Ошибка", message)

    def show_warning(self, message):
        """Показать предупреждение"""
        messagebox.showwarning("Предупреждение", message)

    def show_info(self, message):
        """Показать информационное сообщение"""
        messagebox.showinfo("Информация", message)


class SessionSelectDialog:
    def __init__(self, parent, sessions):
        self.parent = parent
        self.sessions = sessions
        self.selection = None
        self.dialog = ctk.CTkToplevel(parent)
        self.dialog.title("Выберите сессию")
        self.dialog.geometry("300x200")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        self.create_widgets()
        self.dialog.wait_window()

    def create_widgets(self):
        ctk.CTkLabel(self.dialog, text="Выберите сессию:").pack(pady=10)

        self.combo = ctk.CTkComboBox(self.dialog, values=self.sessions)
        self.combo.pack(pady=10)
        if self.sessions:
            self.combo.set(self.sessions[0])

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


# Глобальный экземпляр редактора
multi_table_editor = None


def get_multi_table_editor(parent):
    """Получение или создание глобального экземпляра редактора"""
    global multi_table_editor
    if multi_table_editor is None or not multi_table_editor.winfo_exists():
        multi_table_editor = MultiTableEditor(parent)
    else:
        multi_table_editor.lift()
    return multi_table_editor
