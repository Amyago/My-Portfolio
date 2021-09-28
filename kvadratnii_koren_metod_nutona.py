x = float(input('Введите значение x: '))
x_0 = x
n = int(input('Введите число итераций: '))
def Metod_Nutona(a, b):
    i = 0
    a = x
    b = n
    while i<b and a>=0:
        a = 0.5*(a + x_0/a)
        i+=1
    return a
print('Корень из', x, 'при', n, 'итерациях методом Ньютона равен: ', Metod_Nutona(x, n))
