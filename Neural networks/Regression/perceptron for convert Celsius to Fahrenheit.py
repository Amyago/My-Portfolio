# Импорт необходимых библиотек
import numpy as np
import matplotlib.pyplot as plt
from tensorflow import keras
from tensorflow.keras.layers import Dense

# Обучающая выборка
c = np.array([-40, -10, 0, 8, 15, 22, 38]) # градусы Цельсия
f = np.array([-40, 14, 32, 46, 59, 72, 100]) # градусы Фаренгейта

# Создание нейронной сети
model = keras.Sequential()
model.add(Dense(units=1, input_shape=(1,), activation='linear'))

# Компилирование НС
model.compile(loss='mean_squared_error', optimizer=keras.optimizers.Adam(0.1))

# Обучение НС
history = model.fit(c, f, epochs=500, verbose = False)

# Построение графика критерия качества
plt.plot(history.history['loss'])
plt.grid(True)
plt.show()

# Прогнозирование значения
print(model.predict([100]))

# Вывод весов НС
print(model.get_weights())
