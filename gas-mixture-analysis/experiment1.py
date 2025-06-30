# Подключение необходимых библиотек
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.svm import SVC
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score
from scipy.special import expit
from mpl_toolkits.mplot3d import Axes3D
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
# Загрузка данных
data = pd.read_csv("data1.txt", sep='\s+', header=None)
data.columns = ["Time (seconds)", "Methane conc (ppm)", "Ethylene conc (ppm)", "TGS-2600(1)", "TGS-2600(2)", "TGS-2600(3)", "TGS-2600(4)", "TGS-2602(1)", "TGS-2602(2)", "TGS-2602(3)", "TGS-2602(4)", "TGS-2610(1)", "TGS-2610(2)", "TGS-2610(3)", "TGS-2610(4)", "TGS-2620(1)", "TGS-2620(2)", "TGS-2620(3)", "TGS-2620(4)"]
data = data.drop(columns=["TGS-2600(2)", "TGS-2600(3)", "TGS-2600(4)", "TGS-2602(1)", "TGS-2602(2)", "TGS-2602(3)", "TGS-2602(4)", "TGS-2610(1)", "TGS-2610(2)", "TGS-2610(3)", "TGS-2610(4)", "TGS-2620(1)", "TGS-2620(2)", "TGS-2620(3)", "TGS-2620(4)"])
# Создание переменной для определения того или иного класса
data['Methane_Present'] = data['Methane conc (ppm)'].apply(lambda x: 1 if x > 0 else 0)
data['Ethylene_Present'] = data['Ethylene conc (ppm)'].apply(lambda x: 1 if x > 0 else 0)
# 0 - воздух 
# 1 – воздух + метан 
# 2 - воздух + этилен
data['target'] = data.apply(lambda row: 1 if row['Methane_Present'] == 1 and row['Ethylene_Present'] == 0 else
                                 2 if row['Methane_Present'] == 0 and row['Ethylene_Present'] == 1 else 0, axis=1)
data = data.drop(columns=["Methane_Present", "Ethylene_Present"])
# Проведение стандартизации данных
scaler = StandardScaler()
data_scaled = scaler.fit_transform(data)
# Применение метода главных компонент (число компонент будет равное трем, так как график будет строиться в трехмерном пространстве)
pca = PCA(n_components=3) 
data_pca = pca.fit_transform(data_scaled)
# Разделяем данные на обучающую (первые 80% данных) и тестовую выборки (остальные 20%)
X_train, X_test, y_train, y_test = train_test_split(data_pca, data['target'], train_size=59975, random_state=42, shuffle=False)
# Проводим классификацию, используя метод опорных векторов
SVC_model = SVC(kernel='linear')
SVC_model.fit(X_train, y_train)
SVC_prediction = SVC_model.predict(X_test)
print("Точность (Accuracy):", accuracy_score(y_test, SVC_prediction))
print("Точность (Precision):", precision_score(y_test, SVC_prediction, average='macro'))
print("Полнота:", recall_score(y_test, SVC_prediction, average='macro'))
print("F1-мера:", f1_score(y_test, SVC_prediction, average='macro'))
# Определяем вероятность принадлежности к классу 0 (воздух)
dec = SVC_model.decision_function(X_test)
probs = expit(dec)
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(X_test[:, 0], X_test[:, 1], X_test[:, 2], c=probs[:, 0], cmap='coolwarm', alpha=0.5)
ax.set_xlabel('PC1')
ax.set_ylabel('PC2')
ax.set_zlabel('PC3', labelpad=-3)
fig.colorbar(sc)
plt.title('Вероятность принадлежности к классу 0')
plt.show()
# Определяем вероятность принадлежности к классу 1 (воздух + метан)
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(X_test[:, 0], X_test[:, 1], X_test[:, 2], c=probs[:, 1], cmap='coolwarm', alpha=0.5)
ax.set_xlabel('PC1')
ax.set_ylabel('PC2')
ax.set_zlabel('PC3', labelpad=-3)
fig.colorbar(sc)
plt.title('Вероятность принадлежности к классу 1')
plt.show()
# Определяем вероятность принадлежности к классу 2 (воздух + этилен)
fig = plt.figure(figsize=(10, 7))
ax = fig.add_subplot(111, projection='3d')
sc = ax.scatter(X_test[:, 0], X_test[:, 1], X_test[:, 2], c=probs[:, 2], cmap='coolwarm', alpha=0.5)
ax.set_xlabel('PC1')
ax.set_ylabel('PC2')
ax.set_zlabel('PC3', labelpad=-3)
fig.colorbar(sc)
plt.title('Вероятность принадлежности к классу 2')
plt.show()
