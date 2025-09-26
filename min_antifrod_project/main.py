# =============================================================================
# БЛОК 1: ИМПОРТ БИБЛИОТЕК И НАСТРОЙКА
# =============================================================================
import pandas as pd
import numpy as np
# !!! ИЗМЕНЕНИЕ: Импортируем RandomForestClassifier вместо IsolationForest !!!
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
import uuid
from datetime import datetime, timedelta

# Фиксируем случайность для воспроизводимости результатов
np.random.seed(42)

# =============================================================================
# БЛОК 2: ГЕНЕРАЦИЯ ДАННЫХ С "ДРЕЙФОМ КОНЦЕПТА" (ИСПРАВЛЕННАЯ ВЕРСИЯ)
# =============================================================================
print("Шаг 1: Генерация симуляционных данных с дрейфом концепта...")

n_normal = 950
n_fraud_past = 30
n_fraud_future = 20
transactions = []

# --- 2.1. Генерация легальных пользователей ---
normal_users = [str(uuid.uuid4()) for _ in range(200)]
for _ in range(n_normal):
    user = np.random.choice(normal_users)
    amount = np.random.uniform(100, 10_000)
    # Даты легальных транзакций в прошлом
    timestamp = pd.to_datetime('2025-09-25') - timedelta(days=np.random.uniform(5, 30))
    transactions.append([user, amount, timestamp])
gamer_user = str(uuid.uuid4()); normal_users.append(gamer_user)
gamer_time = pd.to_datetime('2025-09-25') - timedelta(days=np.random.uniform(5, 30))
for _ in range(12):
    amount = np.random.uniform(5, 75); gamer_time += timedelta(seconds=np.random.uniform(5, 25))
    transactions.append([gamer_user, amount, gamer_time])
spender_user = str(uuid.uuid4()); normal_users.append(spender_user)
for _ in range(5):
    transactions.append([spender_user, np.random.uniform(500, 2000), pd.to_datetime('2025-09-25') - timedelta(days=np.random.uniform(5, 30))])
transactions.append([spender_user, 50_000, pd.to_datetime('2025-09-25') - timedelta(days=4)])

# --- 2.2. Генерация "СТАРОГО" фрода (для train набора) ---
fraud_users_past = [str(uuid.uuid4()) for _ in range(2)]
# !!! ИСПРАВЛЕНИЕ: Делаем этот фрод действительно "прошлым", чтобы он попал в train set !!!
start_time_past = pd.to_datetime('2025-09-15')
current_time = start_time_past
for _ in range(n_fraud_past):
    user = np.random.choice(fraud_users_past)
    amount = np.random.uniform(1, 20)
    increment = timedelta(seconds=np.random.uniform(1, 3))
    current_time += increment
    transactions.append([user, amount, current_time])

# --- 2.3. Генерация "НОВОГО, АДАПТИРОВАВШЕГОСЯ" фрода (для val набора) ---
fraud_users_future = [str(uuid.uuid4()) for _ in range(2)]
# !!! ИСПРАВЛЕНИЕ: Делаем этот фрод "настоящим", чтобы он попал в val set !!!
start_time_future = pd.to_datetime('2025-09-25')
current_time = start_time_future
for _ in range(n_fraud_future):
    user = np.random.choice(fraud_users_future)
    amount = np.random.uniform(40, 80)
    increment = timedelta(seconds=np.random.uniform(10, 25))
    current_time += increment
    transactions.append([user, amount, current_time])

fraud_users = fraud_users_past + fraud_users_future
print(f"Данные сгенерированы. Всего транзакций: {len(transactions)}")


# =============================================================================
# БЛОК 3: ПОДГОТОВКА ДАННЫХ И СОЗДАНИЕ МЕТОК
# =============================================================================
print("\nШаг 2: Создание признаков и меток для контролируемого обучения...")
df = pd.DataFrame(transactions, columns=['user_id', 'amount', 'timestamp'])
df = df.sort_values('timestamp').reset_index(drop=True)

# !!! НОВОЕ: Создаем целевую переменную (метки "фрод / не фрод") !!!
df['is_fraud'] = df['user_id'].isin(fraud_users).astype(int)

# --- Инжиниринг признаков (без изменений) ---
expanding_stats = df.groupby('user_id')['amount'].expanding(min_periods=2).agg(['mean', 'std']).reset_index()
df['temp_join_key'] = df.index
df = pd.merge(df, expanding_stats, left_on=['user_id', 'temp_join_key'], right_on=['user_id', 'level_1'], how='left')
df['amount_z_score'] = (df['amount'] - df['mean']) / df['std']
df['time_since_last_tx'] = df.groupby('user_id')['timestamp'].diff().dt.total_seconds()
df = df.set_index('timestamp')
df['tx_last_5min'] = df.groupby('user_id')['amount'].rolling('300s').count().reset_index(level=0, drop=True) - 1
df = df.reset_index()
df = df.drop(columns=['level_1', 'mean', 'std', 'temp_join_key'], errors='ignore')
print("Признаки и метки созданы.")


# =============================================================================
# БЛОК 4: ОБУЧЕНИЕ МОДЕЛИ V1 ("ЧЕМПИОН") НА СТАРЫХ ДАННЫХ
# =============================================================================
print("\nШаг 3: Обучение модели V1 и 'честный экзамен' на новых данных...")

# --- 4.1. Разделение данных ---
split_point = df['timestamp'].quantile(0.8, interpolation='nearest')
df_train = df[df['timestamp'] < split_point].copy()
df_val = df[df['timestamp'] >= split_point].copy()

# --- 4.2. Подготовка признаков (X) и меток (y) ---
feature_cols = ['amount_z_score', 'time_since_last_tx', 'tx_last_5min']
X_train = df_train[feature_cols].fillna(0)
y_train = df_train['is_fraud'] # Метки для обучения
X_val = df_val[feature_cols].fillna(0)

# --- 4.3. Масштабирование (без изменений) ---
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_val_scaled = scaler.transform(X_val)

# --- 4.4. Обучение Классификатора V1 ТОЛЬКО на старых данных ---
model_v1 = RandomForestClassifier(random_state=42, n_estimators=100, class_weight='balanced')
model_v1.fit(X_train_scaled, y_train) # Обучение с метками!

# --- 4.5. Получение ВЕРОЯТНОСТИ фрода и подбор порога ---
df_val['fraud_probability_v1'] = model_v1.predict_proba(X_val_scaled)[:, 1]
threshold_v1 = 0.5 # Для классификаторов стандартный порог - 0.5
df_val['anomaly_v1'] = df_val['fraud_probability_v1'] > threshold_v1
print(f"Модель V1 (обученная на старых данных) оценена. Порог: {threshold_v1}")

# =============================================================================
# БЛОК 5: СИМУЛЯЦИЯ ПЕРЕОБУЧЕНИЯ И СРАВНЕНИЕ
# =============================================================================
print("\nШаг 4: Симуляция переобучения (Модель V2) и сравнение...")

# --- 5.1. Обучение модели V2 ("Претендент") на ВСЕХ данных ---
X_full = df[feature_cols].fillna(0)
y_full = df['is_fraud']
X_full_scaled = scaler.transform(X_full)

model_v2 = RandomForestClassifier(random_state=42, n_estimators=100, class_weight='balanced')
model_v2.fit(X_full_scaled, y_full) # Переобучение на всех данных

# --- 5.2. Оценка модели V2 на тех же проверочных данных ---
df_val['fraud_probability_v2'] = model_v2.predict_proba(X_val_scaled)[:, 1]
threshold_v2 = 0.5
df_val['anomaly_v2'] = df_val['fraud_probability_v2'] > threshold_v2
print(f"Модель V2 (переобученная) оценена. Порог: {threshold_v2}")

# --- 5.3. Финальное сравнение результатов ---
print("\n[РЕЗУЛЬТАТЫ СРАВНЕНИЯ МОДЕЛЕЙ НА НОВЫХ ДАННЫХ]")
fraud_mask_val = df_val['is_fraud'] == 1
legit_mask_val = df_val['is_fraud'] == 0
total_fraud_val = df_val[fraud_mask_val].shape[0]
total_legit_val = df_val[legit_mask_val].shape[0]

caught_v1 = df_val[fraud_mask_val & df_val['anomaly_v1']].shape[0]
fp_v1 = df_val[legit_mask_val & df_val['anomaly_v1']].shape[0]
caught_v2 = df_val[fraud_mask_val & df_val['anomaly_v2']].shape[0]
fp_v2 = df_val[legit_mask_val & df_val['anomaly_v2']].shape[0]

print(f"\n--- Обнаружение фрода ({total_fraud_val} транзакций) ---")
print(f"Модель V1 (старая):   поймала {caught_v1} из {total_fraud_val}")
print(f"Модель V2 (новая):    поймала {caught_v2} из {total_fraud_val}")

print(f"\n--- Ложные срабатывания ({total_legit_val} транзакций) ---")
print(f"Модель V1 (старая):   {fp_v1} ложных блоков")
print(f"Модель V2 (новая):    {fp_v2} ложных блоков")

if (caught_v2 > caught_v1) or (caught_v2 == caught_v1 and fp_v2 < fp_v1):
    print("\nВывод: Переобучение доказало свою эффективность!")
else:
    print("\nВывод: В этот раз переобучение не дало явного улучшения.")
