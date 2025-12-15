import numpy
import matplotlib.pyplot as plt
from scipy.integrate import odeint
import json

#данные ступеней
stages = [{'stage_mass': 38051, 'fuel_mass': 97000, 'f_tract': 2964000, 'burn_time': 90},
          {'stage_mass': 15325, 'fuel_mass': 20123, 'f_tract': 703000, 'burn_time': 90}]

temp = 288 #15 градусов цельсия + 273 (кельвины)
m_rocket = 195988 #масса ракеты (кг)
p0 = 101325 #давление на земле (Па)
M = 0.029 #молярная масса воздуха (кг/моль)
R = 8.31 #универсальная газовая постоянная (Дж/(моль*К))
C = 0.66 #коэффициент обтекаемости
S = 9.42 #площадь поперечного сечения (м^2)
G = 6.674e-11 #гравитационная постоянная (Н*м^2/кг^2)
M_k = 5.29e22 #масса Кербина (кг)
R_k = 600000 #радиус Кербина (м)

def corner(altitude): #вычисление угла гравитационного поворота
    if altitude < 70000:
        return 90 * (1 - altitude / 70000)
    return 0

def odeint_func(data, time, k, f_tract): #k - расход топлива ступени, f_tract - сила тяги ступени
    x, x_speed, y, y_speed, m = data #распаковка данных

    global temp
    if temp > 160: temp = 288 - (y // 100) * 0.6 #расчет температуры (-0.6 градусов каждые 100 метров)

    speed = x_speed ** 2 + y_speed ** 2 #квадрат скорости
    alpha = corner(y) #угол поворота

    g = (G * M_k) / ((R_k + y) ** 2) #ускорение свободного падения
    p = (p0 * numpy.exp((-M * g * y) / (R * temp)) * M) / (R * temp) #плотность атмосферы
    
    f_res = 0.5 * C * p * speed * S #сила сопротивления
    f_grav = g * m #сила тяжести

    x_acc = ((f_tract - f_res) * numpy.cos(numpy.radians(alpha))) / m #ускорение по оси х
    y_acc = ((f_tract - f_res) * numpy.sin(numpy.radians(alpha)) - f_grav) / m #ускорение по оси у
    acc = (x_acc ** 2 + y_acc ** 2) ** 0.5 #ускорение

    #производные
    dx = x_speed 
    dx_speed = x_acc
    dy = y_speed
    dy_speed = y_acc
    dm = -k

    return [dx, dx_speed, dy, dy_speed, dm]

start_data = [0, 0, 0, 0, m_rocket] #начальные данные для первой ступени

k_first = stages[0]['fuel_mass'] / stages[0]['burn_time'] #расход топлива первой ступени
f_tract_first = stages[0]['f_tract'] #сила тяги первой ступени
time_first = numpy.linspace(0, stages[0]['burn_time']) #время работы первой ступени
result_first = odeint(odeint_func, start_data, time_first, args=(k_first, f_tract_first, )) #результаты для первой ступени

new_mass = result_first[-1].copy() #последний результат работы первой ступени
new_mass[-1] -= stages[0]['stage_mass'] #отделение пустой первой ступени
start_data_2 = new_mass #начальные данные для второй ступени

k_second = stages[1]['fuel_mass'] / stages[1]['burn_time'] #расход топлива второй ступени
f_tract_second = stages[1]['f_tract'] #сила тяги второй ступени
time_second = numpy.linspace(0, stages[1]['burn_time'], 90) #время работы второй ступени
result_second = odeint(odeint_func, start_data_2, time_second, args=(k_second, f_tract_second, )) #результаты для второй ступени

#объединение результатов обеих ступеней
time = numpy.concatenate([time_first, time_first[-1] + time_second])
x = numpy.concatenate([result_first[:, 0], result_second[:, 0]])
x_speeds = numpy.concatenate([result_first[:, 1], result_second[:, 1]])
y = numpy.concatenate([result_first[:, 2], result_second[:, 2]])
y_speeds = numpy.concatenate([result_first[:, 3], result_second[:, 3]])
mass_rocket = numpy.concatenate([result_first[:, 4], result_second[:, 4]])
speeds = numpy.array([(x_speeds[i] ** 2 + y_speeds[i] ** 2) ** 0.5 for i in range(len(x_speeds))])
accelerations = numpy.array([speeds[i] - speeds[i - 1] for i in range(1, len(speeds))])
x_accelerations = numpy.array([x_speeds[i] - x_speeds[i - 1] for i in range(1, len(x_speeds))])
y_accelerations = numpy.array([y_speeds[i] - y_speeds[i - 1] for i in range(1, len(y_speeds))])

#считывание данных из KSP
with open("data_from_ksp.json", 'r', encoding='UTF-8') as file:
    data_ksp = json.load(file)

#организация данных из KSP
time_ksp = numpy.array(data_ksp[0]["time"])
altitude_ksp = numpy.array(data_ksp[0]["height"])
mass_ksp = numpy.array(data_ksp[0]["masses"])
speeds_ksp = numpy.array(data_ksp[0]["speeds"]) 
x_speeds_ksp = numpy.array(data_ksp[0]["x_speeds"])
y_speeds_ksp = numpy.array([data_ksp[0]["y_speeds"][i] for i in range(0, len(data_ksp[0]["y_speeds"]), 13)]) 
accelerations_ksp = numpy.array([data_ksp[0]["accelerations"][i] for i in range(0, len(data_ksp[0]["accelerations"]), 13)])
x_accelerations_ksp = numpy.array([data_ksp[0]["x_accelerations"][i] for i in range(0, len(data_ksp[0]["x_accelerations"]), 13)]) 
y_accelerations_ksp = numpy.array([data_ksp[0]["y_accelerations"][i] for i in range(0, len(data_ksp[0]["y_accelerations"]), 13)])

plt.figure(figsize=(15, 5))
#высота от времени
plt.subplot(1, 2, 1)
plt.plot(time, y, label='Высота по мат модели', color='red')
plt.plot(time_ksp, altitude_ksp, label='Высота по КСП', color='blue')
plt.title('Высота от времени')
plt.xlabel('Время, с')
plt.ylabel('Высота, м')
plt.legend()
plt.grid()

#скорость от времени 
plt.subplot(1, 2, 2)
plt.plot(time, speeds , label='Скорость по мат модели', color='red')
plt.plot(time_ksp, speeds_ksp, label='Скорость по КСП', color='blue')
plt.title('Скорость от времени')
plt.xlabel('Время, с')
plt.ylabel('Скорость, м/с')
plt.legend()
plt.grid()
plt.show()

#масса от времени
plt.figure(figsize=(15, 5))
plt.subplot(1, 2, 1)
plt.plot(time, mass_rocket, label='Масса по мат модели', color='red')
plt.plot(time_ksp, mass_ksp, label='Масса по КСП', color='blue')
plt.title('Масса от времени')
plt.xlabel('Время, с')
plt.ylabel('Масса, кг')
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(15, 5))
#горизонтальная скорость от времени
plt.subplot(1, 2, 1)
plt.plot(time, x_speeds , label='Горизонтальная скорость по мат модели', color='red')
plt.plot(time_ksp, x_speeds_ksp, label='Горизонтальная скорость по КСП', color='blue')
plt.title('Горизонтальная скорость от времени')
plt.xlabel('Время, с')
plt.ylabel('Скорость, м/с')
plt.legend()
plt.grid()

#вертикальная скорость от времени
plt.subplot(1, 2, 2)
plt.plot(time, y_speeds , label='Вертикальная скорость по мат модели', color='red')
plt.plot(numpy.array([time_ksp[x] for x in range(0, len(time_ksp), 13)]), y_speeds_ksp, label='Вертикальная скорость по КСП', color='blue')
plt.title('Вертикальная скорость от времени')
plt.xlabel('Время, с')
plt.ylabel('Скорость, м/с')
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(15, 5))
#ускорение от времени
plt.subplot(1, 2, 1)
plt.plot(time[:len(time)-1], accelerations , label='Ускорение по мат модели', color='red')
plt.plot(numpy.array([time_ksp[x] for x in range(0, len(time_ksp), 13)]), accelerations_ksp, label='Ускорение по КСП', color='blue')
plt.title('Ускорение от времени')
plt.xlabel('Время, c')
plt.ylabel('Ускорение, м/с^2')
plt.legend()
plt.grid()
plt.show()

plt.figure(figsize=(15, 5))
#горизонтальное ускорение от времени
plt.subplot(1, 2, 1)
plt.plot(time[:len(time)-1], x_accelerations, label='Горизонтальное ускорение по мат модели', color='red')
plt.plot(numpy.array([time_ksp[x] for x in range(0, len(time_ksp), 13)]), x_accelerations_ksp, label='Горизонтальное ускорение по КСП', color='blue')
plt.title('Горизонтальное ускорение от времени')
plt.xlabel('Время, c')
plt.ylabel('Ускорение, м/с^2')
plt.legend()
plt.grid()

#вертикальное ускорение от времени
plt.subplot(1, 2, 2)
plt.plot(time[:len(time)-1], y_accelerations, label='Вертикальное ускорение по мат модели', color='red')
plt.plot(numpy.array([time_ksp[x] for x in range(0, len(time_ksp), 13)]), y_accelerations_ksp, label='Вертикальное ускорение по КСП', color='blue')
plt.title('Вертикальное ускорение от времени')
plt.xlabel('Время, c')
plt.ylabel('Ускорение, м/с^2')
plt.legend()
plt.grid()
plt.show()
