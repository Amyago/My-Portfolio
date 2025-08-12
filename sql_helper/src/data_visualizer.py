import customtkinter as ctk
from tkinter import filedialog, messagebox
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import numpy as np
from datetime import datetime
import os

# Устанавливаем тему matplotlib
plt.style.use('dark_background' if ctk.get_appearance_mode() == "Dark" else "default")


class DataVisualizer(ctk.CTkToplevel):
    def __init__(self, parent, data=None):
        super().__init__(parent)
        self.title("Визуализация данных")
        self.geometry("1000x700")
        self.parent = parent
        self.data = data
        self.current_figure = None
        self.df = None

        self.create_widgets()

        # Если данные переданы, загружаем их
        if data:
            self.load_data(data)

    def create_widgets(self):
        # === Заголовок ===
        header_frame = ctk.CTkFrame(self)
        header_frame.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(header_frame, text="Визуализация данных",
                     font=ctk.CTkFont(size=16, weight="bold")).pack(side="left", padx=10)

        # === Панель управления ===
        control_frame = ctk.CTkFrame(self)
        control_frame.pack(fill="x", padx=10, pady=5)

        # Выбор типа графика
        chart_type_frame = ctk.CTkFrame(control_frame)
        chart_type_frame.pack(side="left", padx=5, pady=5)

        ctk.CTkLabel(chart_type_frame, text="Тип графика:").pack(side="left", padx=5)
        self.chart_type_var = ctk.StringVar(value="bar")
        self.chart_type_combo = ctk.CTkComboBox(
            chart_type_frame,
            values=["bar", "line", "pie", "scatter", "histogram"],
            variable=self.chart_type_var,
            command=self.on_chart_type_change
        )
        self.chart_type_combo.pack(side="left", padx=5)

        # Выбор колонок
        columns_frame = ctk.CTkFrame(control_frame)
        columns_frame.pack(side="left", padx=5, pady=5)

        ctk.CTkLabel(columns_frame, text="X:").pack(side="left", padx=5)
        self.x_column_combo = ctk.CTkComboBox(columns_frame, values=[], width=120)
        self.x_column_combo.pack(side="left", padx=5)

        ctk.CTkLabel(columns_frame, text="Y:").pack(side="left", padx=5)
        self.y_column_combo = ctk.CTkComboBox(columns_frame, values=[], width=120)
        self.y_column_combo.pack(side="left", padx=5)

        # Кнопки управления
        button_frame = ctk.CTkFrame(control_frame)
        button_frame.pack(side="right", padx=5, pady=5)

        ctk.CTkButton(button_frame, text="Построить",
                      command=self.create_chart,
                      fg_color="green").pack(side="left", padx=5)

        ctk.CTkButton(button_frame, text="Экспорт",
                      command=self.export_chart).pack(side="left", padx=5)

        # === Область графика ===
        self.chart_frame = ctk.CTkFrame(self)
        self.chart_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Создаем область для графика
        self.chart_container = ctk.CTkFrame(self.chart_frame)
        self.chart_container.pack(fill="both", expand=True, padx=10, pady=10)

        # Добавляем надпись по умолчанию
        self.default_label = ctk.CTkLabel(
            self.chart_container,
            text="Выберите данные и тип графика для визуализации",
            font=ctk.CTkFont(size=14)
        )
        self.default_label.pack(expand=True)

        # === Информация о данных ===
        self.info_frame = ctk.CTkFrame(self)
        self.info_frame.pack(fill="x", padx=10, pady=5)

        self.data_info_label = ctk.CTkLabel(self.info_frame, text="Данные не загружены")
        self.data_info_label.pack(padx=10, pady=5)

    def load_data(self, data):
        """Загрузка данных для визуализации"""
        try:
            if isinstance(data, list):
                # Преобразуем список словарей в DataFrame
                self.df = pd.DataFrame(data)
            elif isinstance(data, pd.DataFrame):
                self.df = data.copy()
            else:
                raise ValueError("Неподдерживаемый формат данных")

            # Обновляем информацию о данных
            rows, cols = self.df.shape
            self.data_info_label.configure(
                text=f"Загружено данных: {rows} строк, {cols} колонок"
            )

            # Обновляем списки колонок
            columns = list(self.df.columns)
            self.x_column_combo.configure(values=columns)
            self.y_column_combo.configure(values=columns)

            if columns:
                self.x_column_combo.set(columns[0])
                if len(columns) > 1:
                    self.y_column_combo.set(columns[1])
                else:
                    self.y_column_combo.set(columns[0])

            # Скрываем надпись по умолчанию
            self.default_label.pack_forget()

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка загрузки данных:\n{str(e)}")

    def on_chart_type_change(self, choice):
        """Обработка изменения типа графика"""
        # Для круговой диаграммы нужна только одна колонка
        if choice == "pie":
            self.y_column_combo.configure(state="disabled")
        else:
            self.y_column_combo.configure(state="normal")

    def create_chart(self):
        """Создание графика"""
        if self.df is None or self.df.empty:
            messagebox.showwarning("Ошибка", "Нет данных для визуализации")
            return

        try:
            # Очищаем предыдущий график
            self.clear_chart()

            chart_type = self.chart_type_var.get()
            x_column = self.x_column_combo.get()

            if not x_column:
                messagebox.showwarning("Ошибка", "Выберите колонку для оси X")
                return

            # Создаем фигуру matplotlib
            fig, ax = plt.subplots(figsize=(10, 6))
            self.current_figure = fig

            # Создаем график в зависимости от типа
            if chart_type == "bar":
                self.create_bar_chart(ax, x_column)
            elif chart_type == "line":
                self.create_line_chart(ax, x_column)
            elif chart_type == "pie":
                self.create_pie_chart(ax, x_column)
            elif chart_type == "scatter":
                self.create_scatter_chart(ax, x_column)
            elif chart_type == "histogram":
                self.create_histogram(ax, x_column)

            # Настраиваем внешний вид
            ax.tick_params(axis='x', rotation=45)
            fig.tight_layout()

            # Отображаем график в tkinter
            canvas = FigureCanvasTkAgg(fig, self.chart_container)
            canvas.draw()
            canvas.get_tk_widget().pack(fill="both", expand=True)

        except Exception as e:
            messagebox.showerror("Ошибка", f"Ошибка создания графика:\n{str(e)}")
            self.clear_chart()

    def create_bar_chart(self, ax, x_column):
        """Создание столбчатой диаграммы"""
        y_column = self.y_column_combo.get()

        if not y_column:
            messagebox.showwarning("Ошибка", "Выберите колонку для оси Y")
            return

        # Преобразуем данные в числовые
        x_data = self.df[x_column]
        y_data = pd.to_numeric(self.df[y_column], errors='coerce').dropna()

        if len(y_data) == 0:
            raise ValueError("Нет числовых данных для оси Y")

        # Если x_data не числовые, используем индексы
        if not pd.api.types.is_numeric_dtype(x_data):
            x_indices = range(len(y_data))
            ax.bar(x_indices, y_data)
            # Устанавливаем метки
            if len(x_data) == len(y_data):
                ax.set_xticks(x_indices)
                ax.set_xticklabels(x_data.iloc[:len(y_data)], rotation=45)
        else:
            x_numeric = pd.to_numeric(x_data, errors='coerce').dropna()
            if len(x_numeric) == len(y_data):
                ax.bar(x_numeric, y_data)
            else:
                ax.bar(range(len(y_data)), y_data)

        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        ax.set_title(f"Столбчатая диаграмма: {x_column} vs {y_column}")

    def create_line_chart(self, ax, x_column):
        """Создание линейного графика"""
        y_column = self.y_column_combo.get()

        if not y_column:
            messagebox.showwarning("Ошибка", "Выберите колонку для оси Y")
            return

        # Преобразуем данные в числовые
        x_data = self.df[x_column]
        y_data = pd.to_numeric(self.df[y_column], errors='coerce').dropna()

        if len(y_data) == 0:
            raise ValueError("Нет числовых данных для оси Y")

        # Если x_data не числовые, используем индексы
        if not pd.api.types.is_numeric_dtype(x_data):
            ax.plot(range(len(y_data)), y_data, marker='o')
            ax.set_xlabel("Индекс")
        else:
            x_numeric = pd.to_numeric(x_data, errors='coerce').dropna()
            if len(x_numeric) >= len(y_data):
                ax.plot(x_numeric.iloc[:len(y_data)], y_data, marker='o')
                ax.set_xlabel(x_column)
            else:
                ax.plot(range(len(y_data)), y_data, marker='o')
                ax.set_xlabel("Индекс")

        ax.set_ylabel(y_column)
        ax.set_title(f"Линейный график: {x_column} vs {y_column}")
        ax.grid(True, alpha=0.3)

    def create_pie_chart(self, ax, x_column):
        """Создание круговой диаграммы"""
        # Подсчитываем количество уникальных значений
        value_counts = self.df[x_column].value_counts()

        if len(value_counts) > 10:
            # Берем только топ-10
            top_values = value_counts.head(10)
            other_count = value_counts.iloc[10:].sum()
            if other_count > 0:
                top_values['Другие'] = other_count
        else:
            top_values = value_counts

        # Создаем круговую диаграмму
        wedges, texts, autotexts = ax.pie(
            top_values.values,
            labels=top_values.index,
            autopct='%1.1f%%',
            startangle=90
        )

        ax.set_title(f"Круговая диаграмма: {x_column}")

        # Улучшаем внешний вид текста
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontsize(8)

    def create_scatter_chart(self, ax, x_column):
        """Создание точечной диаграммы"""
        y_column = self.y_column_combo.get()

        if not y_column:
            messagebox.showwarning("Ошибка", "Выберите колонку для оси Y")
            return

        # Преобразуем данные в числовые
        x_data = pd.to_numeric(self.df[x_column], errors='coerce')
        y_data = pd.to_numeric(self.df[y_column], errors='coerce')

        # Удаляем NaN значения
        mask = ~(x_data.isna() | y_data.isna())
        x_clean = x_data[mask]
        y_clean = y_data[mask]

        if len(x_clean) == 0:
            raise ValueError("Нет числовых данных для графика")

        # Создаем точечную диаграмму
        ax.scatter(x_clean, y_clean, alpha=0.6)
        ax.set_xlabel(x_column)
        ax.set_ylabel(y_column)
        ax.set_title(f"Точечная диаграмма: {x_column} vs {y_column}")
        ax.grid(True, alpha=0.3)

    def create_histogram(self, ax, x_column):
        """Создание гистограммы"""
        # Преобразуем данные в числовые
        data = pd.to_numeric(self.df[x_column], errors='coerce').dropna()

        if len(data) == 0:
            raise ValueError("Нет числовых данных для гистограммы")

        # Создаем гистограмму
        ax.hist(data, bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax.set_xlabel(x_column)
        ax.set_ylabel("Частота")
        ax.set_title(f"Гистограмма: {x_column}")
        ax.grid(True, alpha=0.3)

    def clear_chart(self):
        """Очистка области графика"""
        # Удаляем все виджеты из контейнера
        for widget in self.chart_container.winfo_children():
            widget.destroy()

        # Если есть текущая фигура, очищаем её
        if self.current_figure:
            plt.close(self.current_figure)
            self.current_figure = None

        # Восстанавливаем надпись по умолчанию
        self.default_label = ctk.CTkLabel(
            self.chart_container,
            text="Выберите данные и тип графика для визуализации",
            font=ctk.CTkFont(size=14)
        )
        self.default_label.pack(expand=True)

    def export_chart(self):
        """Экспорт графика в изображение"""
        if not self.current_figure:
            messagebox.showwarning("Ошибка", "Нет графика для экспорта")
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[
                ("PNG файлы", "*.png"),
                ("JPEG файлы", "*.jpg"),
                ("PDF файлы", "*.pdf"),
                ("SVG файлы", "*.svg"),
                ("Все файлы", "*.*")
            ],
            title="Сохранить график"
        )

        if file_path:
            try:
                # Сохраняем график
                self.current_figure.savefig(
                    file_path,
                    dpi=300,
                    bbox_inches='tight',
                    facecolor='white' if ctk.get_appearance_mode() == "Light" else 'black'
                )
                messagebox.showinfo("Успех", f"График сохранен в:\n{file_path}")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка сохранения графика:\n{str(e)}")


# Глобальный экземпляр визуализатора
data_visualizer = None


def get_data_visualizer(parent, data=None):
    """Получение или создание глобального экземпляра визуализатора"""
    global data_visualizer
    if data_visualizer is None or not data_visualizer.winfo_exists():
        data_visualizer = DataVisualizer(parent, data)
    else:
        # Если переданы новые данные, загружаем их
        if data:
            data_visualizer.load_data(data)
        data_visualizer.lift()
    return data_visualizer
