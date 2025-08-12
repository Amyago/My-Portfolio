import customtkinter as ctk
from tkinter import ttk
import pandas as pd
from datetime import datetime
import json
import os


class QueryMonitor(ctk.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Мониторинг запросов")
        self.geometry("900x600")
        self.parent = parent

        # Статистика запросов
        self.query_stats = []
        self.load_stats()

        self.create_widgets()
        self.update_display()

    def create_widgets(self):
        # === Заголовок ===
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Мониторинг выполнения запросов",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        # Кнопки управления
        button_frame = ctk.CTkFrame(header_frame)
        button_frame.pack(side="right")

        ctk.CTkButton(button_frame, text="Обновить",
                      command=self.update_display).pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Очистить",
                      command=self.clear_stats, fg_color="red").pack(side="left", padx=5)
        ctk.CTkButton(button_frame, text="Экспорт",
                      command=self.export_stats).pack(side="left", padx=5)

        # === Статистика ===
        stats_frame = ctk.CTkFrame(self)
        stats_frame.pack(fill="x", padx=10, pady=5)

        self.stats_label = ctk.CTkLabel(stats_frame, text="",
                                        font=ctk.CTkFont(weight="bold"))
        self.stats_label.pack(padx=10, pady=5)

        # === Таблица запросов ===
        ctk.CTkLabel(self, text="История запросов:",
                     font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))

        # Создаем фрейм для таблицы
        table_frame = ctk.CTkFrame(self)
        table_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Создаем Treeview для отображения таблицы
        self.tree_stats = ttk.Treeview(table_frame)
        self.tree_stats.pack(fill="both", expand=True, padx=5, pady=5)

        # Добавляем скроллбары
        vsb = ttk.Scrollbar(table_frame, orient="vertical", command=self.tree_stats.yview)
        vsb.pack(side='right', fill='y')
        self.tree_stats.configure(yscrollcommand=vsb.set)

        hsb = ttk.Scrollbar(table_frame, orient="horizontal", command=self.tree_stats.xview)
        hsb.pack(side='bottom', fill='x')
        self.tree_stats.configure(xscrollcommand=hsb.set)

        # Настройка колонок
        self.setup_tree_columns()

    def setup_tree_columns(self):
        """Настройка колонок таблицы"""
        self.tree_stats["columns"] = ("timestamp", "query", "execution_time", "rows_affected", "status")
        self.tree_stats["show"] = "headings"

        self.tree_stats.heading("timestamp", text="Время")
        self.tree_stats.heading("query", text="Запрос")
        self.tree_stats.heading("execution_time", text="Время выполнения (ms)")
        self.tree_stats.heading("rows_affected", text="Строк затронуто")
        self.tree_stats.heading("status", text="Статус")

        self.tree_stats.column("timestamp", width=150)
        self.tree_stats.column("query", width=300)
        self.tree_stats.column("execution_time", width=120)
        self.tree_stats.column("rows_affected", width=100)
        self.tree_stats.column("status", width=100)

    def log_query(self, query, execution_time, rows_affected, status="Успех"):
        """Логирование выполненного запроса"""
        stat_entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'query': query.strip()[:100] + "..." if len(query.strip()) > 100 else query.strip(),
            'execution_time': round(execution_time * 1000, 2),  # В миллисекундах
            'rows_affected': rows_affected,
            'status': status
        }

        self.query_stats.append(stat_entry)
        # Ограничиваем историю 1000 записями
        if len(self.query_stats) > 1000:
            self.query_stats.pop(0)

        self.save_stats()
        self.update_display()

    def load_stats(self):
        """Загрузка статистики из файла"""
        if os.path.exists("query_stats.json"):
            try:
                with open("query_stats.json", "r", encoding="utf-8") as f:
                    self.query_stats = json.load(f)
            except Exception as e:
                print(f"Ошибка загрузки статистики: {e}")
                self.query_stats = []

    def save_stats(self):
        """Сохранение статистики в файл"""
        try:
            with open("query_stats.json", "w", encoding="utf-8") as f:
                json.dump(self.query_stats, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения статистики: {e}")

    def update_display(self):
        """Обновление отображения статистики"""
        # Очищаем таблицу
        for item in self.tree_stats.get_children():
            self.tree_stats.delete(item)

        # Обновляем статистику
        self.update_stats_label()

        # Добавляем данные в таблицу (в обратном порядке - новые сверху)
        for stat in reversed(self.query_stats[-100:]):  # Показываем последние 100
            self.tree_stats.insert("", "end", values=(
                stat['timestamp'],
                stat['query'],
                stat['execution_time'],
                stat['rows_affected'],
                stat['status']
            ))

    def update_stats_label(self):
        """Обновление сводной статистики"""
        if not self.query_stats:
            self.stats_label.configure(text="Нет данных для отображения")
            return

        total_queries = len(self.query_stats)
        avg_time = sum(stat['execution_time'] for stat in self.query_stats) / total_queries
        total_rows = sum(stat['rows_affected'] for stat in self.query_stats)
        successful = sum(1 for stat in self.query_stats if stat['status'] == "Успех")
        failed = total_queries - successful

        stats_text = (f"Всего запросов: {total_queries} | "
                      f"Среднее время: {avg_time:.2f}ms | "
                      f"Строк обработано: {total_rows} | "
                      f"Успешно: {successful} | "
                      f"Ошибок: {failed}")

        self.stats_label.configure(text=stats_text)

    def clear_stats(self):
        """Очистка статистики"""
        self.query_stats = []
        self.save_stats()
        self.update_display()

    def export_stats(self):
        """Экспорт статистики в CSV"""
        if not self.query_stats:
            from tkinter import messagebox
            messagebox.showwarning("Экспорт", "Нет данных для экспорта")
            return

        from tkinter import filedialog
        file_path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("CSV files", "*.csv"), ("Excel files", "*.xlsx"), ("All files", "*.*")]
        )

        if not file_path:
            return

        try:
            df = pd.DataFrame(self.query_stats)

            if file_path.endswith('.csv'):
                df.to_csv(file_path, index=False, encoding='utf-8-sig')
            elif file_path.endswith('.xlsx'):
                df.to_excel(file_path, index=False)

            from tkinter import messagebox
            messagebox.showinfo("Экспорт", f"Статистика успешно экспортирована в {file_path}")
        except Exception as e:
            from tkinter import messagebox
            messagebox.showerror("Ошибка", f"Ошибка экспорта: {str(e)}")


# Глобальный экземпляр монитора
query_monitor = None


def get_query_monitor(parent):
    """Получение или создание глобального экземпляра монитора"""
    global query_monitor
    if query_monitor is None or not query_monitor.winfo_exists():
        query_monitor = QueryMonitor(parent)
    else:
        query_monitor.lift()
    return query_monitor
