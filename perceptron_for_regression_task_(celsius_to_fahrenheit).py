# -*- coding: utf-8 -*-
"""perceptron for regression task (Celsius to Fahrenheit).ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1AKf--Fgl8GKpcpiQpEJ24Y4hQwraYyNO

Импорт необходимых библиотек
"""

import numpy as np
import matplotlib.pyplot as plt
from tensorflow import keras
from tensorflow.keras.layers import Dense

"""Обучающая выборка"""

c = np.array([-40, -10, 0, 8, 15, 22, 38])
f = np.array([-40, 14, 32, 46, 59, 72, 100])

model = keras.Sequential()
model.add(Dense(units=1, input_shape=(1,), activation='linear'))

model.compile(loss='mean_squared_error', optimizer=keras.optimizers.Adam(0.1))

history = model.fit(c, f, epochs=500, verbose = False)

plt.plot(history.history['loss'])
plt.grid(True)
plt.show()

print(model.predict([100]))

print(model.get_weights())