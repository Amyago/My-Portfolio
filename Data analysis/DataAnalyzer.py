import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns
from scipy import stats
import joblib
import json
import os
import datetime
import warnings
import csv
import shutil
from statsmodels.stats.outliers_influence import variance_inflation_factor
warnings.filterwarnings('ignore')

class DataAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Advanced Data Analyzer")
        self.root.geometry("1200x800")

        self.analyzer = AdvancedDataAnalyzer()
        self.setup_gui()

    def setup_gui(self):
        # Создаем главное меню
        self.menu_bar = tk.Menu(self.root)
        self.root.config(menu=self.menu_bar)
        # Меню File
        self.file_menu = tk.Menu(self.menu_bar, tearoff=0)
        self.menu_bar.add_cascade(label="File", menu=self.file_menu)
        self.file_menu.add_command(label="Load Data", command=self.load_data)
        self.file_menu.add_command(label="Save Results", command=self.save_results)
        self.file_menu.add_separator()
        self.file_menu.add_command(label="Exit", command=self.root.quit)
        # Создаем notebook для вкладок
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=5)
        # Создаем вкладки
        self.setup_data_tab()
        self.setup_preprocessing_tab()
        self.setup_visualization_tab()
        self.setup_analysis_tab()
        # Статус бар
        self.status_var = tk.StringVar()
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var)
        self.status_bar.pack(side='bottom', fill='x')

    def setup_data_tab(self):
        self.data_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.data_tab, text="Data Overview")
        # Создаем Text widget для вывода информации
        self.data_info = tk.Text(self.data_tab)
        self.data_info.pack(fill='both', expand=True)

    def setup_preprocessing_tab(self):
        self.prep_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.prep_tab, text="Preprocessing")

        # Фрейм для опций предобработки
        options_frame = ttk.LabelFrame(self.prep_tab, text="Preprocessing Options")
        options_frame.pack(fill='x', padx=5, pady=5)

        # Опции масштабирования
        ttk.Label(options_frame, text="Scaling Method:").grid(row=0, column=0, padx=5, pady=5)
        self.scaling_var = tk.StringVar(value="standard")
        scaling_options = ttk.OptionMenu(options_frame, self.scaling_var, "standard", "robust", "minmax")
        scaling_options.grid(row=0, column=1, padx=5, pady=5)

        # Опции обработки пропусков
        ttk.Label(options_frame, text="Missing Values:").grid(row=1, column=0, padx=5, pady=5)
        self.imputer_var = tk.StringVar(value="mean")
        imputer_options = ttk.OptionMenu(options_frame, self.imputer_var,"mean", "median", "knn")
        imputer_options.grid(row=1, column=1, padx=5, pady=5)
        # Кнопка применения предобработки
        ttk.Button(options_frame, text="Apply Preprocessing",
                   command=self.apply_preprocessing).grid(row=2, column=0,
                                                          columnspan=2, pady=10)

    def setup_visualization_tab(self):
        self.vis_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.vis_tab, text="Visualization")
        # Фрейм для опций визуализации
        vis_options = ttk.LabelFrame(self.vis_tab, text="Visualization Options")
        vis_options.pack(fill='x', padx=5, pady=5)
        # Выбор типа графика
        ttk.Label(vis_options, text="Plot Type:").grid(row=0, column=0, padx=5, pady=5)
        self.plot_type_var = tk.StringVar(value="histogram")
        plot_options = ttk.OptionMenu(vis_options, self.plot_type_var,
                                    "histogram", "scatter", "box", "correlation")
        plot_options.grid(row=0, column=1, padx=5, pady=5)
        # Кнопка создания графика
        ttk.Button(vis_options, text="Create Plot",
                    command=self.create_plot).grid(row=1, column=0, columnspan=2, pady=10)
        # Фрейм для графика
        self.plot_frame = ttk.Frame(self.vis_tab)
        self.plot_frame.pack(fill='both', expand=True)

    def setup_analysis_tab(self):
        self.analysis_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.analysis_tab, text="Statistical Analysis")
        # Опции анализа
        analysis_options = ttk.LabelFrame(self.analysis_tab, text="Analysis Options")
        analysis_options.pack(fill='x', padx=5, pady=5)

        # Выбор типа анализа
        ttk.Label(analysis_options, text="Analysis Type:").grid(row=0, column=0, padx=5, pady=5)
        self.analysis_type_var = tk.StringVar(value="descriptive")
        analysis_options_menu = ttk.OptionMenu(analysis_options, self.analysis_type_var,"descriptive", "hypothesis_testing", "correlation")
        analysis_options_menu.grid(row=0, column=1, padx=5, pady=5)
        # Кнопка выполнения анализа
        ttk.Button(analysis_options, text="Run Analysis", command=self.run_analysis).grid(row=1, column=0, columnspan=2, pady=10)
        # Текстовое поле для результатов
        self.analysis_text = tk.Text(self.analysis_tab)
        self.analysis_text.pack(fill='both', expand=True)

    def load_data(self):
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv"),
                           ("Excel files", "*.xlsx"),
                           ("JSON files", "*.json")])

            if file_path:
                self.analyzer.load_data(file_path)
                self.update_data_info()
                self.status_var.set("Data loaded successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error loading data: {str(e)}")

    def update_data_info(self):
        if self.analyzer.data is not None:
            self.data_info.delete(1.0, tk.END)
            info_text = f"Dataset Shape: {self.analyzer.data.shape}\n\n"
            info_text += "Data Types:\n{}\n\n".format(
                self.analyzer.data.dtypes.to_string())
            info_text += "Summary Statistics:\n{}\n\n".format(
                self.analyzer.data.describe().to_string())
            self.data_info.insert(tk.END, info_text)

    def apply_preprocessing(self):
        try:
            if self.analyzer.data is not None:
                self.analyzer.preprocess_data(
                    scaling_method=self.scaling_var.get(),
                    imputer_method=self.imputer_var.get()
                )
                messagebox.showinfo("Success", "Preprocessing completed")
                self.status_var.set("Preprocessing completed successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Preprocessing error: {str(e)}")

    def create_plot(self):
        try:
            if self.analyzer.processed_data is not None:
                # Очищаем предыдущий контент plot_frame
                for widget in self.plot_frame.winfo_children():
                    widget.destroy()

                plot_type = self.plot_type_var.get()
                figures = self.analyzer.create_visualization(plot_type)

                if figures:
                    if plot_type in ['histogram', 'box']:
                        canvas = tk.Canvas(self.plot_frame)
                        scrollbar = ttk.Scrollbar(self.plot_frame, orient="vertical", command=canvas.yview)
                        scrollable_frame = ttk.Frame(canvas)

                        scrollable_frame.bind(
                            "<Configure>",
                            lambda e: canvas.configure(
                                scrollregion=canvas.bbox("all")
                            )
                        )

                        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
                        canvas.configure(yscrollcommand=scrollbar.set)

                        for fig in figures:
                            canvas_widget = FigureCanvasTkAgg(fig, master=scrollable_frame)
                            canvas_widget.draw()
                            canvas_widget.get_tk_widget().pack(pady=10)
                            plt.close(fig)  # Важно закрывать figure после добавления на canvas

                        canvas.pack(side="left", fill="both", expand=True)
                        scrollbar.pack(side="right", fill="y")

                        self.status_var.set(f"Created {plot_type} plot(s) with scrolling")

                    else:  # Для scatter и correlation plot
                        for fig in figures:
                            canvas = FigureCanvasTkAgg(fig, master=self.plot_frame)
                            canvas.draw()
                            canvas.get_tk_widget().pack(fill='both', expand=True)
                            plt.close(fig)
                        self.status_var.set(f"Created {plot_type} plot(s)")
                else:
                    self.status_var.set("No plots to display.")

            else:
                messagebox.showerror("Error", "Please apply preprocessing first.")
        except Exception as e:
            messagebox.showerror("Error", f"Visualization error: {str(e)}")

    def run_analysis(self):
        try:
            if self.analyzer.data is not None:
                analysis_type = self.analysis_type_var.get()
                results = self.analyzer.run_statistical_analysis(analysis_type)

                self.analysis_text.delete(1.0, tk.END)
                self.analysis_text.insert(tk.END, results)

                self.status_var.set(f"Completed {analysis_type} analysis")
        except Exception as e:
            messagebox.showerror("Error", f"Analysis error: {str(e)}")

    def save_results(self):
        try:
            if self.analyzer.data is not None:
                save_path = filedialog.asksaveasfilename(
                    defaultextension=".zip",
                    filetypes=[("ZIP files", "*.zip")]
                )
                if save_path:
                    self.analyzer.save_results(save_path)
                    self.status_var.set("Results saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Error saving results: {str(e)}")

def run():
    root = tk.Tk()
    app = DataAnalyzerGUI(root)
    root.mainloop()

class AdvancedDataAnalyzer:
    def __init__(self):
        self.data = None
        self.processed_data = None
        self.results_history = []

    def load_data(self, file_path):
        """Расширенная загрузка данных с валидацией"""
        try:
            # Определение формата файла
            file_ext = file_path.split('.')[-1].lower()

            if file_ext == 'csv':
                # Автоматическое определение разделителя
                with open(file_path, 'r') as f:
                    dialect = csv.Sniffer().sniff(f.read(1024))
                    f.seek(0) # Возвращаем указатель в начало файла
                self.data = pd.read_csv(file_path, delimiter=dialect.delimiter)
            elif file_ext in ['xls', 'xlsx']:
                self.data = pd.read_excel(file_path)
            elif file_ext == 'json':
                self.data = pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_ext}")

            # Валидация данных
            self._validate_data()

            return True
        except Exception as e:
            raise Exception(f"Error loading data: {str(e)}")

    def _validate_data(self):
        """Валидация загруженных данных"""
        if self.data.empty:
            raise ValueError("Dataset is empty")

        # Проверка на дубликаты
        duplicates = self.data.duplicated().sum()
        if duplicates > 0:
            warnings.warn(f"Found {duplicates} duplicate rows")

        # Проверка на пропущенные значения
        missing = self.data.isnull().sum()
        if missing.any():
            warnings.warn(f"Found columns with missing values:\n{missing[missing > 0]}")

        # Проверка типов данных
        for column in self.data.columns:
            try:
                pd.to_numeric(self.data[column])
            except:
                continue

    def preprocess_data(self, scaling_method='standard', imputer_method='mean'):
        """Расширенная предобработка данных"""
        try:
            self.processed_data = self.data.copy()

            # Обработка пропущенных значений
            if imputer_method == 'knn':
                from sklearn.impute import KNNImputer
                imputer = KNNImputer(n_neighbors=5)
            else:
                from sklearn.impute import SimpleImputer
                imputer = SimpleImputer(
                    strategy=imputer_method,
                    add_indicator=True
                )

            # Разделение на числовые и категориальные признаки
            numeric_features = self.processed_data.select_dtypes(
                include=['int64', 'float64']).columns
            categorical_features = self.processed_data.select_dtypes(
                include=['object']).columns

            # Обработка числовых признаков
            if numeric_features.any():
                self.processed_data[numeric_features] = imputer.fit_transform(
                    self.processed_data[numeric_features])

                # Масштабирование
                if scaling_method == 'standard':
                    from sklearn.preprocessing import StandardScaler
                    scaler = StandardScaler()
                elif scaling_method == 'robust':
                    from sklearn.preprocessing import RobustScaler
                    scaler = RobustScaler()
                elif scaling_method == 'minmax':
                    from sklearn.preprocessing import MinMaxScaler
                    scaler = MinMaxScaler()

                self.processed_data[numeric_features] = scaler.fit_transform(
                    self.processed_data[numeric_features])

            # Обработка категориальных признаков
            for feature in categorical_features:
                # Создание dummy-переменных
                dummies = pd.get_dummies(
                    self.processed_data[feature],
                    prefix=feature,
                    drop_first=True
                )
                self.processed_data = pd.concat(
                    [self.processed_data, dummies], axis=1)
                self.processed_data.drop(feature, axis=1, inplace=True)

            # Удаление мультиколлинеарности
            correlation_matrix = self.processed_data.corr()
            high_corr_features = np.where(np.abs(correlation_matrix) > 0.95)
            high_corr_features = [(correlation_matrix.index[x],
                                   correlation_matrix.columns[y])
                                  for x, y in zip(*high_corr_features)
                                  if x != y and x < y]

            if high_corr_features:
                features_to_drop = [pair[1] for pair in high_corr_features]
                self.processed_data.drop(features_to_drop, axis=1, inplace=True)
                warnings.warn(f"Removed highly correlated features: {features_to_drop}")

            return self.processed_data
        except Exception as e:
            raise Exception(f"Preprocessing error: {str(e)}")

    def create_visualization(self, plot_type):
        """Создание объекта Figure с визуализацией"""
        if self.processed_data is None:
            raise Exception("No preprocessed data available. Please run preprocessing first.")
        try:
            sns.set()  # Устанавливает стиль по умолчанию для графиков

            numeric_cols = self.processed_data.select_dtypes(include=['int64', 'float64']).columns
            figures = []

            if plot_type == 'histogram':
                for column in numeric_cols:
                    fig = plt.figure(figsize=(10, 6))
                    sns.histplot(data=self.processed_data, x=column, kde=True)
                    plt.title(f'Distribution of {column}')
                    plt.tight_layout()
                    figures.append(fig)

            elif plot_type == 'scatter':
                numeric_cols_scatter = numeric_cols[:2]
                if len(numeric_cols_scatter) >= 2:
                    fig = plt.figure(figsize=(10, 6))
                    sns.scatterplot(data=self.processed_data, x=numeric_cols_scatter[0], y=numeric_cols_scatter[1])
                    plt.title(f'Scatter Plot: {numeric_cols_scatter[0]} vs {numeric_cols_scatter[1]}')
                    plt.tight_layout()
                    figures.append(fig)

            elif plot_type == 'correlation':
                fig = plt.figure(figsize=(10, 8))
                correlation_matrix = self.processed_data.corr()
                sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0)
                plt.title('Correlation Matrix')
                plt.tight_layout()
                figures.append(fig)

            elif plot_type == 'box':
                for column in numeric_cols:
                    fig = plt.figure(figsize=(8, 6))
                    plt.boxplot(self.processed_data[column].dropna())  # Используем plt.boxplot напрямую
                    plt.title(f'Box Plot of {column}')
                    plt.ylabel(column)
                    plt.tight_layout()
                    figures.append(fig)

            return figures

        except Exception as e:
            raise Exception(f"Visualization error: {str(e)}")

    def run_statistical_analysis(self, analysis_type):
        """Расширенный статистический анализ"""
        try:
            results = []
            numeric_data = self.processed_data.select_dtypes(
                include=['int64', 'float64'])

            if analysis_type == 'descriptive':
                results.append("Descriptive Statistics:")
                results.append(numeric_data.describe().to_string())

                # Дополнительные статистики
                results.append("\nSkewness:")
                results.append(numeric_data.skew().to_string())

                results.append("\nKurtosis:")
                results.append(numeric_data.kurtosis().to_string())

            elif analysis_type == 'hypothesis_testing':
                results.append("Normality Tests (Shapiro-Wilk):")
                for column in numeric_data.columns:
                    statistic, p_value = stats.shapiro(numeric_data[column])
                    results.append(f"\n{column}:")
                    results.append(f"Statistic: {statistic:.4f}")
                    results.append(f"P-value: {p_value:.4f}")

                # Добавление других статистических тестов
                if len(numeric_data.columns) >= 2:
                    results.append("\nCorrelation Tests (Pearson):")
                    cols = numeric_data.columns
                    for i in range(len(cols)):
                        for j in range(i + 1, len(cols)):
                            corr, p_value = stats.pearsonr(
                                numeric_data[cols[i]],
                                numeric_data[cols[j]]
                            )
                            results.append(f"\n{cols[i]} vs {cols[j]}:")
                            results.append(f"Correlation: {corr:.4f}")
                            results.append(f"P-value: {p_value:.4f}")

            elif analysis_type == 'correlation':
                results.append("Correlation Analysis:")
                correlation_matrix = numeric_data.corr()
                results.append(correlation_matrix.to_string())

                # Добавление теста на мультиколлинеарность
                vif_data = pd.DataFrame()
                for column in numeric_data.columns:
                    vif_data[column] = [variance_inflation_factor(
                        numeric_data.values,
                        numeric_data.columns.get_loc(column)
                    )]
                results.append("\nVariance Inflation Factors:")
                results.append(vif_data.to_string())

            return "\n".join(results)
        except Exception as e:
            raise Exception(f"Analysis error: {str(e)}")

    def save_results(self, save_path):
        """Сохранение результатов анализа"""
        try:
            # Создание временной директории
            temp_dir = "temp_results"
            os.makedirs(temp_dir, exist_ok=True)

            # Сохранение данных
            self.data.to_csv(f"{temp_dir}/original_data.csv")
            if self.processed_data is not None:
                self.processed_data.to_csv(f"{temp_dir}/processed_data.csv")

            # Создание отчета
            report = {
                "analysis_date": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "data_shape": self.data.shape,
                "preprocessing_steps": self.results_history
            }

            with open(f"{temp_dir}/analysis_report.json", "w") as f:
                json.dump(report, f, indent=4)

            # Создание архива
            shutil.make_archive(save_path.replace('.zip', ''), 'zip', temp_dir)

            # Очистка временной директории
            shutil.rmtree(temp_dir)

            return True
        except Exception as e:
            raise Exception(f"Error saving results: {str(e)}")

if __name__ == "__main__":
    run()
