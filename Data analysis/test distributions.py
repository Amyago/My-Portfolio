import numpy as np
import scipy.stats as stats
import customtkinter as ctk
from tkinter import messagebox

# Функция для выполнения всех тестов
def perform_tests(data1, data2):
    results = {}

    # 1. Т-тест для независимых выборок
    t_stat, t_p = stats.ttest_ind(data1, data2)
    results['T-тест'] = (t_stat, t_p)

    # 2. Стандартизированная разность средних
    mean_diff = np.mean(data1) - np.mean(data2)
    pooled_std = np.sqrt((np.var(data1, ddof=1) + np.var(data2, ddof=1)) / 2)
    std_mean_diff = mean_diff / pooled_std
    results['Стандартизированная разность средних'] = std_mean_diff

    # 3. U-критерий Манна-Уитни
    u_stat, u_p = stats.mannwhitneyu(data1, data2, alternative='two-sided')
    results['U-критерий Манна-Уитни'] = (u_stat, u_p)

    # 4. Тест хи-квадрат (для категориальных данных)
    try:
        chi_stat, chi_p = stats.chisquare(data1, data2)
        results['Тест хи-квадрат'] = (chi_stat, chi_p)
    except:
        results['Тест хи-квадрат'] = 'Не удалось выполнить для непрерывных данных'

    # 5. Критерий Колмогорова-Смирнова
    ks_stat, ks_p = stats.ks_2samp(data1, data2)
    results['Критерий Колмогорова-Смирнова'] = (ks_stat, ks_p)

    # 6. F-тест (сравнение дисперсий)
    f_stat, f_p = stats.levene(data1, data2)
    results['F-тест'] = (f_stat, f_p)

    return results


# Функция для отображения результатов
def show_results(results):
    result_text = ""
    for test, result in results.items():
        if isinstance(result, tuple):
            result_text += f"{test}: Статистика = {result[0]:.4f}, p-значение = {result[1]:.4f}\n"
        else:
            result_text += f"{test}: {result}\n"
    messagebox.showinfo("Результаты тестов", result_text)


# Функция для запуска тестов при нажатии кнопки
def run_tests():
    try:
        data1 = list(map(float, entry_data1.get().split(',')))
        data2 = list(map(float, entry_data2.get().split(',')))

        results = perform_tests(np.array(data1), np.array(data2))
        show_results(results)
    except ValueError:
        messagebox.showerror("Ошибка", "Некорректный ввод данных. Пожалуйста, введите числа, разделенные запятыми.")


# Настройка интерфейса с использованием customtkinter
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

root = ctk.CTk()
root.title("Сравнение распределений")

label_data1 = ctk.CTkLabel(root, text="Введите данные 1 (через запятую):")
label_data1.pack(pady=10)

entry_data1 = ctk.CTkEntry(root, width=400)
entry_data1.pack(pady=10)

label_data2 = ctk.CTkLabel(root, text="Введите данные 2 (через запятую):")
label_data2.pack(pady=10)

entry_data2 = ctk.CTkEntry(root, width=400)
entry_data2.pack(pady=10)

button_run = ctk.CTkButton(root, text="Запустить тесты", command=run_tests)
button_run.pack(pady=20)

root.mainloop()
