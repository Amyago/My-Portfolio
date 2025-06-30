import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d
from scipy.signal import medfilt
from sklearn.linear_model import LinearRegression

# Функция для чтения данных
def read_data(filename):
    df = pd.read_csv(filename, sep=';', header=None)
    heater = df.iloc[:, 1]  # heater activation column
    time = df.iloc[:, 3]    # time t in ms
    resistance = df.iloc[:, 4]  # resistance R in ohms
    return heater, time, resistance
  
# Функция для интерполяции временных аномалий
def interpolate_time(time):
    time_diff = np.diff(time)
    time_interp = np.copy(time)
    anomaly_indices = np.where(time_diff <= 0)[0]
    if len(anomaly_indices) > 0:
        valid_indices = np.where(time_diff > 0)[0]
        valid_time = time[valid_indices]
        interp_func = interp1d(valid_indices, valid_time, kind='linear', fill_value="extrapolate")
        for idx in anomaly_indices:
            if idx < len(time_interp):
                time_interp[idx] = interp_func(idx)
    return time_interp
  
# Функция для удаления краткосрочных спадов на основе скользящей медианы
def remove_dips(time, resistance, window_size=51, threshold_factor=100):
    """
    Удаление краткосрочных спадов сопротивления путём сравнения со скользящей медианой.
    Любое значение, которое ниже медианы в 'threshold_factor' раз, будет заменено.
    Параметры:
    time: array-like, временные значения
    resistance: array-like, значения сопротивления
    window_size: int, размер окна для медианного фильтра (должен быть нечётным)
    threshold_factor: float, коэффициент для определения спада
    Возвращает:
    filtered_resistance: array-like, сопротивление с удалёнными спадами
    """
    # Применение скользящей медианы
    median_filtered = medfilt(resistance, kernel_size=window_size)
    # Определить спады как точки, где сопротивление значительно ниже медианы
    dips_indices = resistance < (median_filtered / threshold_factor)
    # Выполнение интерполяции для замены спадов
    filtered_resistance = np.copy(resistance)
    filtered_resistance[dips_indices] = np.interp(time[dips_indices], time[~dips_indices], resistance[~dips_indices])
    return filtered_resistance
  
# Функция для разделения данных на циклы
def split_into_cycles(heater, time, resistance, cycle_duration=15000, window_size=51, threshold_factor=100):
    cycle_starts = np.where(np.diff(heater) == 1)[0]
    cycles = []
    for start in cycle_starts:
        end = start + int(cycle_duration / np.mean(np.diff(time)))  # приблизительное число точек за 15 секунд
        cycle_time = time[start:end] - time[start]  # переход к началу каждого цикла
        cycle_resistance = resistance[start:end]
        # Удаление спадов из сопротивления
        filtered_resistance = remove_dips(cycle_time, cycle_resistance, window_size, threshold_factor)
        if len(cycle_time) == len(filtered_resistance):  # убеждаемся, что длина совпадает
            cycles.append((cycle_time, filtered_resistance))
    # Пропуск первых 10 циклов
    return cycles[10:]
  
# Функция усреднения всех циклов для одной концентрации
def average_cycles(cycles, num_points=1000):
    common_time = np.linspace(0, 15000, num_points)
    interpolated_resistances = []
    for cycle_time, cycle_resistance in cycles:
        interp_func = interp1d(cycle_time, cycle_resistance, kind='nearest', fill_value="extrapolate")
        interpolated_resistance = interp_func(common_time)
        interpolated_resistances.append(interpolated_resistance)
    average_resistance = np.mean(interpolated_resistances, axis=0)
    return common_time, average_resistance
  
# Функция для построения графиков циклов и усредненных значений
def plot_cycles_and_averages(cycles, avg_time, avg_resistance, color, label):
    for cycle_time, cycle_resistance in cycles:
        plt.plot(cycle_time, cycle_resistance, color=color, alpha=0.3)
    plt.plot(avg_time, avg_resistance, color='black', linewidth=2)
    plt.plot([], [], color=color, label=label)
  
# чтение данных по CO
heater_000_CO, time_000_CO, resistance_000_CO = read_data('Air_33_CO_000.txt')
heater_001_CO, time_001_CO, resistance_001_CO = read_data('Air_33_CO_001.txt')
heater_002_CO, time_002_CO, resistance_002_CO = read_data('Air_33_CO_002.txt')
heater_005_CO, time_005_CO, resistance_005_CO = read_data('Air_33_CO_005.txt')
heater_010_CO, time_010_CO, resistance_010_CO = read_data('Air_33_CO_010.txt')
heater_020_CO, time_020_CO, resistance_020_CO = read_data('Air_33_CO_020.txt')
heater_050_CO, time_050_CO, resistance_050_CO = read_data('Air_33_CO_050.txt')
heater_100_CO, time_100_CO, resistance_100_CO = read_data('Air_33_CO_100.txt')

# чтение данных по H2
heater_000_H2, time_000_H2, resistance_000_H2 = read_data('Air_33_H2_000.txt')
heater_001_H2, time_001_H2, resistance_001_H2 = read_data('Air_33_H2_001.txt')
heater_002_H2, time_002_H2, resistance_002_H2 = read_data('Air_33_H2_002.txt')
heater_005_H2, time_005_H2, resistance_005_H2 = read_data('Air_33_H2_005.txt')
heater_010_H2, time_010_H2, resistance_010_H2 = read_data('Air_33_H2_010.txt')
heater_020_H2, time_020_H2, resistance_020_H2 = read_data('Air_33_H2_020.txt')
heater_050_H2, time_050_H2, resistance_050_H2 = read_data('Air_33_H2_050.txt')
heater_100_H2, time_100_H2, resistance_100_H2 = read_data('Air_33_H2_100.txt')

# чтение данных по CH4
heater_0000_CH4, time_0000_CH4, resistance_0000_CH4 = read_data('Air_33_CH4_0000.txt')
heater_0050_CH4, time_0050_CH4, resistance_0050_CH4 = read_data('Air_33_CH4_0050.txt')
heater_0100_CH4, time_0100_CH4, resistance_0100_CH4 = read_data('Air_33_CH4_0100.txt')
heater_0200_CH4, time_0200_CH4, resistance_0200_CH4 = read_data('Air_33_CH4_0200.txt')
heater_0500_CH4, time_0500_CH4, resistance_0500_CH4 = read_data('Air_33_CH4_0500.txt')
heater_1000_CH4, time_1000_CH4, resistance_1000_CH4 = read_data('Air_33_CH4_1000.txt')
heater_2000_CH4, time_2000_CH4, resistance_2000_CH4 = read_data('Air_33_CH4_2000.txt')

time_interp_000_CO = interpolate_time(time_000_CO)  # интерполяция времени для CO
time_interp_001_CO = interpolate_time(time_001_CO)
time_interp_002_CO = interpolate_time(time_002_CO)
time_interp_005_CO = interpolate_time(time_005_CO)
time_interp_010_CO = interpolate_time(time_010_CO)
time_interp_020_CO = interpolate_time(time_020_CO)
time_interp_050_CO = interpolate_time(time_050_CO)
time_interp_100_CO = interpolate_time(time_100_CO)

time_interp_000_H2 = interpolate_time(time_000_H2)  # интерполяция времени для H2
time_interp_001_H2 = interpolate_time(time_001_H2)
time_interp_002_H2 = interpolate_time(time_002_H2)
time_interp_005_H2 = interpolate_time(time_005_H2)
time_interp_010_H2 = interpolate_time(time_010_H2)
time_interp_020_H2 = interpolate_time(time_020_H2)
time_interp_050_H2 = interpolate_time(time_050_H2)
time_interp_100_H2 = interpolate_time(time_100_H2)

time_interp_0000_CH4 = interpolate_time(time_0000_CH4) # интерполяция времени для CH4
time_interp_0050_CH4 = interpolate_time(time_0050_CH4)
time_interp_0100_CH4 = interpolate_time(time_0100_CH4)
time_interp_0200_CH4 = interpolate_time(time_0200_CH4)
time_interp_0500_CH4 = interpolate_time(time_0500_CH4)
time_interp_1000_CH4 = interpolate_time(time_1000_CH4)
time_interp_2000_CH4 = interpolate_time(time_2000_CH4)

# Разделение данных на циклы и устранение аномалий
cycles_000_CO = split_into_cycles(heater_000_CO, time_interp_000_CO, resistance_000_CO)
cycles_001_CO = split_into_cycles(heater_001_CO, time_interp_001_CO, resistance_001_CO)
cycles_002_CO = split_into_cycles(heater_002_CO, time_interp_002_CO, resistance_002_CO)
cycles_005_CO = split_into_cycles(heater_005_CO, time_interp_005_CO, resistance_005_CO)
cycles_010_CO = split_into_cycles(heater_010_CO, time_interp_010_CO, resistance_010_CO)
cycles_020_CO = split_into_cycles(heater_020_CO, time_interp_020_CO, resistance_020_CO)
cycles_050_CO = split_into_cycles(heater_050_CO, time_interp_050_CO, resistance_050_CO)
cycles_100_CO = split_into_cycles(heater_100_CO, time_interp_100_CO, resistance_100_CO)

cycles_000_H2 = split_into_cycles(heater_000_H2, time_interp_000_H2, resistance_000_H2)
cycles_001_H2 = split_into_cycles(heater_001_H2, time_interp_001_H2, resistance_001_H2)
cycles_002_H2 = split_into_cycles(heater_002_H2, time_interp_002_H2, resistance_002_H2)
cycles_005_H2 = split_into_cycles(heater_005_H2, time_interp_005_H2, resistance_005_H2)
cycles_010_H2 = split_into_cycles(heater_010_H2, time_interp_010_H2, resistance_010_H2)
cycles_020_H2 = split_into_cycles(heater_020_H2, time_interp_020_H2, resistance_020_H2)
cycles_050_H2 = split_into_cycles(heater_050_H2, time_interp_050_H2, resistance_050_H2)
cycles_100_H2 = split_into_cycles(heater_100_H2, time_interp_100_H2, resistance_100_H2)

cycles_0000_CH4 = split_into_cycles(heater_0000_CH4, time_interp_0000_CH4, resistance_0000_CH4)
cycles_0050_CH4 = split_into_cycles(heater_0050_CH4, time_interp_0050_CH4, resistance_0050_CH4)
cycles_0100_CH4 = split_into_cycles(heater_0100_CH4, time_interp_0100_CH4, resistance_0100_CH4)
cycles_0200_CH4 = split_into_cycles(heater_0200_CH4, time_interp_0200_CH4, resistance_0200_CH4)
cycles_0500_CH4 = split_into_cycles(heater_0500_CH4, time_interp_0500_CH4, resistance_0500_CH4)
cycles_1000_CH4 = split_into_cycles(heater_1000_CH4, time_interp_1000_CH4, resistance_1000_CH4)
cycles_2000_CH4 = split_into_cycles(heater_2000_CH4, time_interp_2000_CH4, resistance_2000_CH4)

# усреднение циклов
avg_time_000_CO, avg_resistance_000_CO = average_cycles(cycles_000_CO)
avg_time_001_CO, avg_resistance_001_CO = average_cycles(cycles_001_CO)
avg_time_002_CO, avg_resistance_002_CO = average_cycles(cycles_002_CO)
avg_time_005_CO, avg_resistance_005_CO = average_cycles(cycles_005_CO)
avg_time_010_CO, avg_resistance_010_CO = average_cycles(cycles_010_CO)
avg_time_020_CO, avg_resistance_020_CO = average_cycles(cycles_020_CO)
avg_time_050_CO, avg_resistance_050_CO = average_cycles(cycles_050_CO)
avg_time_100_CO, avg_resistance_100_CO = average_cycles(cycles_100_CO)

avg_time_000_H2, avg_resistance_000_H2 = average_cycles(cycles_000_H2)
avg_time_001_H2, avg_resistance_001_H2 = average_cycles(cycles_001_H2)
avg_time_002_H2, avg_resistance_002_H2 = average_cycles(cycles_002_H2)
avg_time_005_H2, avg_resistance_005_H2 = average_cycles(cycles_005_H2)
avg_time_010_H2, avg_resistance_010_H2 = average_cycles(cycles_010_H2)
avg_time_020_H2, avg_resistance_020_H2 = average_cycles(cycles_020_H2)
avg_time_050_H2, avg_resistance_050_H2 = average_cycles(cycles_050_H2)
avg_time_100_H2, avg_resistance_100_H2 = average_cycles(cycles_100_H2)

avg_time_0000_CH4, avg_resistance_0000_CH4 = average_cycles(cycles_0000_CH4)
avg_time_0050_CH4, avg_resistance_0050_CH4 = average_cycles(cycles_0050_CH4)
avg_time_0100_CH4, avg_resistance_0100_CH4 = average_cycles(cycles_0100_CH4)
avg_time_0200_CH4, avg_resistance_0200_CH4 = average_cycles(cycles_0200_CH4)
avg_time_0500_CH4, avg_resistance_0500_CH4 = average_cycles(cycles_0500_CH4)
avg_time_1000_CH4, avg_resistance_1000_CH4 = average_cycles(cycles_1000_CH4)
avg_time_2000_CH4, avg_resistance_2000_CH4 = average_cycles(cycles_2000_CH4)

# построение графиков
plt.figure(figsize=(20, 12))
plot_cycles_and_averages(cycles_000_H2, avg_time_000_H2, avg_resistance_000_H2, 'green', '0 ppm (Air)')
plot_cycles_and_averages(cycles_001_H2, avg_time_001_H2, avg_resistance_001_H2, 'red', '1 ppm')
plot_cycles_and_averages(cycles_002_H2, avg_time_002_H2, avg_resistance_002_H2, 'blue', '2 ppm')
plot_cycles_and_averages(cycles_005_H2, avg_time_005_H2, avg_resistance_005_H2, 'cyan', '5 ppm')
plot_cycles_and_averages(cycles_010_H2, avg_time_010_H2, avg_resistance_010_H2, 'magenta', '10 ppm')
plot_cycles_and_averages(cycles_020_H2, avg_time_020_H2, avg_resistance_020_H2, 'yellow', '20 ppm')
plot_cycles_and_averages(cycles_050_H2, avg_time_050_H2, avg_resistance_050_H2, '#FF4F00', '50 ppm')
plot_cycles_and_averages(cycles_100_H2, avg_time_100_H2, avg_resistance_100_H2, '#808080', '100 ppm')
plt.yscale('log')
plt.title('Совмещенные R(t|c) и усредненная кривая ⟨R(t|c)⟩ для различных концентраций водорода')
plt.xlabel('Время (с)')
plt.ylabel('Сопротивление (Ом)')
plt.legend(loc='lower right')
plt.grid(True)
plt.show()
plt.figure(figsize=(20, 12))
plot_cycles_and_averages(cycles_000_CO, avg_time_000_CO, avg_resistance_000_CO, 'green', '0 ppm (Air)')
plot_cycles_and_averages(cycles_001_CO, avg_time_001_CO, avg_resistance_001_CO, 'red', '1 ppm')
plot_cycles_and_averages(cycles_002_CO, avg_time_002_CO, avg_resistance_002_CO, 'blue', '2 ppm')
plot_cycles_and_averages(cycles_005_CO, avg_time_005_CO, avg_resistance_005_CO, 'cyan', '5 ppm')
plot_cycles_and_averages(cycles_010_CO, avg_time_010_CO, avg_resistance_010_CO, 'magenta', '10 ppm')
plot_cycles_and_averages(cycles_020_CO, avg_time_020_CO, avg_resistance_020_CO, 'yellow', '20 ppm')
plot_cycles_and_averages(cycles_050_CO, avg_time_050_CO, avg_resistance_050_CO, '#FF4F00', '50 ppm')
plot_cycles_and_averages(cycles_100_CO, avg_time_100_CO, avg_resistance_100_CO, '#808080', '100 ppm')
plt.yscale('log')
plt.title('Совмещенные R(t|c) и усредненная кривая ⟨R(t|c)⟩ для различных концентраций угарного газа')
plt.xlabel('Время (с)')
plt.ylabel('Сопротивление (Ом)')
plt.legend(loc='lower right')
plt.grid(True)
plt.show()
plt.figure(figsize=(20, 12))
plot_cycles_and_averages(cycles_0000_CH4, avg_time_0000_CH4, avg_resistance_0000_CH4, 'green', '0 ppm (Air)')
plot_cycles_and_averages(cycles_0050_CH4, avg_time_0050_CH4, avg_resistance_0050_CH4, 'red', '50 ppm')
plot_cycles_and_averages(cycles_0100_CH4, avg_time_0100_CH4, avg_resistance_0100_CH4, 'blue', '100 ppm')
plot_cycles_and_averages(cycles_0200_CH4, avg_time_0200_CH4, avg_resistance_0200_CH4, 'cyan', '200 ppm')
plot_cycles_and_averages(cycles_0500_CH4, avg_time_0500_CH4, avg_resistance_0500_CH4, 'magenta', '500 ppm')
plot_cycles_and_averages(cycles_1000_CH4, avg_time_1000_CH4, avg_resistance_1000_CH4, 'yellow', '1000 ppm')
plot_cycles_and_averages(cycles_2000_CH4, avg_time_2000_CH4, avg_resistance_2000_CH4, '#FF4F00', '2000 ppm')
plt.yscale('log')
plt.title('Совмещенные R(t|c) и усредненная кривая ⟨R(t|c)⟩ для различных концентраций метана')
plt.xlabel('Время (с)')
plt.ylabel('Сопротивление (Ом)')
plt.legend(loc='lower right')
plt.grid(True)
plt.show()
common_time = avg_time_000_CO
concentrations_nonzero = [1, 2, 5, 10, 20, 50, 100]
concentrations_CH4 = [50, 100, 200, 500, 1000, 2000]
# Новый цикл, объединяющий все три газа
models = []
min_total_rmse = float('inf')
best_time = None
step = 10  # Шаг для ускорения вычислений
for idx in range(0, len(common_time), step):
    t = common_time[idx]
    # Данные для CO
    R_values_CO = [
        avg_resistance_001_CO[idx], avg_resistance_002_CO[idx],
        avg_resistance_005_CO[idx], avg_resistance_010_CO[idx],
        avg_resistance_020_CO[idx], avg_resistance_050_CO[idx],
        avg_resistance_100_CO[idx]
    ]

    # Данные для H₂
    R_values_H2 = [
        avg_resistance_001_H2[idx], avg_resistance_002_H2[idx],
        avg_resistance_005_H2[idx], avg_resistance_010_H2[idx],
        avg_resistance_020_H2[idx], avg_resistance_050_H2[idx],
        avg_resistance_100_H2[idx]
    ]
  
    # Данные для CH₄
    R_values_CH4 = [
        avg_resistance_0050_CH4[idx], avg_resistance_0100_CH4[idx],
        avg_resistance_0200_CH4[idx], avg_resistance_0500_CH4[idx],
        avg_resistance_1000_CH4[idx], avg_resistance_2000_CH4[idx]
    ]
  
    # Проверка на нулевые значения
    if 0 in R_values_CO or 0 in R_values_H2 or 0 in R_values_CH4:
        continue
    # Модель для CO
    log_R_CO = np.log(R_values_CO).reshape(-1, 1)
    log_conc_CO = np.log(concentrations_nonzero)
    model_CO = LinearRegression().fit(log_R_CO, log_conc_CO)
    a_CO = np.exp(model_CO.intercept_)
    b_CO = model_CO.coef_[0]
    rmse_CO = np.sqrt(np.mean(
        (np.exp(model_CO.predict(log_R_CO)) - concentrations_nonzero) ** 2
    ))

    # Модель для H₂
    log_R_H2 = np.log(R_values_H2).reshape(-1, 1)
    log_conc_H2 = np.log(concentrations_nonzero)
    model_H2 = LinearRegression().fit(log_R_H2, log_conc_H2)
    a_H2 = np.exp(model_H2.intercept_)
    b_H2 = model_H2.coef_[0]
    rmse_H2 = np.sqrt(np.mean(
        (np.exp(model_H2.predict(log_R_H2)) - concentrations_nonzero) ** 2
    ))
  
    # Модель для CH₄
    log_R_CH4 = np.log(R_values_CH4).reshape(-1, 1)
    log_conc_CH4 = np.log(concentrations_CH4)
    model_CH4 = LinearRegression().fit(log_R_CH4, log_conc_CH4)
    a_CH4 = np.exp(model_CH4.intercept_)
    b_CH4 = model_CH4.coef_[0]
    rmse_CH4 = np.sqrt(np.mean(
        (np.exp(model_CH4.predict(log_R_CH4)) - concentrations_CH4) ** 2
    ))
    # Общая ошибка как среднее трёх RMSE
    total_rmse = (rmse_CO + rmse_H2 + rmse_CH4) / 3
    # Сохранение модели
    models.append({
        'time': t,
        'a_CO': a_CO, 'b_CO': b_CO,
        'a_H2': a_H2, 'b_H2': b_H2,
        'a_CH4': a_CH4, 'b_CH4': b_CH4,
        'total_rmse': total_rmse
    })
    # Обновление оптимального времени
    if total_rmse < min_total_rmse:
        min_total_rmse = total_rmse
        best_time = t
# Визуализация
times = [model['time'] for model in models]
total_rmses = [model['total_rmse'] for model in models]

# Квантили и оптимальное время
quantiles = np.array([0.0, 0.005, 0.01, 0.015, 0.02, 0.025])
quantile_values = np.quantile(total_rmses, quantiles)
min_total_rmse = min(total_rmses)
best_time = times[total_rmses.index(min_total_rmse)]
plt.figure(figsize=(12, 6))
plt.plot(times, total_rmses, label='Общая RMSE (CO + H₂ + CH₄)', color='blue')
plt.scatter(best_time, min_total_rmse, color='red', s=100, label='Оптимальный момент')
plt.xlabel('Время (мс)')
plt.ylabel('RMSE')
plt.title('Зависимость общей ошибки от времени для CO, H₂ и CH₄')
plt.legend()
plt.grid(True)
plt.show()
print(f"Оптимальный момент времени: {best_time} мс (Общая RMSE: {min_total_rmse:.4f})")

def classify_gas(test_cycle_time, test_cycle_resistance, models, common_time):
    # Словарь для хранения RSD для каждого газа
    rsd_dict = {'CO': 0, 'H2': 0, 'CH4': 0}
    # Для каждого газа рассчитываем RSD
    for gas in ['CO', 'H2', 'CH4']:
        predicted_phis = []
        for t in common_time:
            # Находим ближайшую модель по времени
            closest_model = min(models, key=lambda x: abs(x['time'] - t))
            # Получаем параметры a и b для текущего газа
            a_key = f'a_{gas}'
            b_key = f'b_{gas}'
            a = closest_model.get(a_key, 0)
            b = closest_model.get(b_key, 0)
            # Интерполяция R(t) для тестового цикла
            R = np.interp(t, test_cycle_time, test_cycle_resistance)
            # Предсказание концентрации
            if b != 0 and a != 0 and R > 0:
                C = (R / a) ** (1 / b)
                predicted_phis.append(C)
            else:
                predicted_phis.append(0)  # обработка нулевых значений
        # Рассчитываем RSD
        mean_phi = np.mean(predicted_phis)
        std_phi = np.std(predicted_phis)
        rsd = (std_phi / mean_phi) * 100 if mean_phi != 0 else 0
        rsd_dict[gas] = rsd
    # Находим газ с минимальным RSD
    best_gas = min(rsd_dict, key=rsd_dict.get)
    # Если RSD для выбранного газа меньше порога, классифицируем его
    if rsd_dict[best_gas] < 0.5:
        return best_gas
    else:
        return "Other gas"
# Пример тестового цикла (например, для 0 ppm H₂)
test_cycle = cycles_000_H2[0]  # Используйте цикл из данных H₂ 0 ppm
classification = classify_gas(
    test_cycle[0],  # Время тестового цикла
    test_cycle[1],  # Сопротивление тестового цикла
    models,         # Список обученных моделей
    common_time     # Общий временной массив
)
print(f"Классификация тестового цикла: {classification}")
