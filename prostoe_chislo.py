x = int(input('Введите число от 0 до 100000: '))

def Prostoe_chislo(a, i, d):
    while i<=a:
        if a%i == 0:
            d+=1
            return Prostoe_chislo(a/i, i, d)
        else:
            i+=1
    if d<=1:
        return(True)
    else:
        return(False)
print(Prostoe_chislo(x, 2, 0))
