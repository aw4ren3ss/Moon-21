import krpc 
import time
import json

#подключение к ракете
conn = krpc.connect(name='Moon-21') 
vessel = conn.space_center.active_vessel

#массив данных
data = [{
    "time": [],
    "height": [],
    "masses": [],
    "speeds": [],
    "x_speeds": [],
    "y_speeds": [],
    "accelerations": [],
    "x_accelerations": [],
    "y_accelerations": []
    }]

last_speed = 0 #последняя скорость
last_x_speed = 0 #последняя скорость по Ох
last_y_speed = 0 #последняя скорость по Оу

#считывание данных не начинается, пока ракета не стартует
while vessel.flight(vessel.orbit.body.reference_frame).speed < 0.1: 
    continue

print("Считывание данных началось.")
start_time = conn.space_center.ut #начало полёта

while True:
    current_time = conn.space_center.ut #текущее время
    
    past_time = current_time - start_time #прошедшее время с начала полета
    altitude = vessel.flight().mean_altitude #высота
    
    if past_time > 221: #проверка на конец работы обеих ступеней
        print("Конец работы.")
        break
    
    mass = vessel.mass #масса
    speed = vessel.flight(vessel.orbit.body.reference_frame).speed #скорость
    
    x_speed = vessel.flight(vessel.orbit.body.reference_frame).horizontal_speed #скорость по Ох
    x_acceleration = (x_speed - last_x_speed) / 0.1 #ускорение по Ох
    last_x_speed = x_speed #новое последнее значение скорости по Ох
    
    y_speed = vessel.flight(vessel.orbit.body.reference_frame).vertical_speed #скорость по Оу
    y_acceleration = (y_speed - last_y_speed) / 0.1 #ускорение по Оу
    last_y_speed = y_speed #новое последнее значение скорости по Оу

    acceleration = (speed - last_speed) / 0.1 #ускорение
    last_speed = speed #новое последнее значение скорости

    #добавление данных в массив
    data[0]["time"] += [past_time]
    data[0]["height"] += [altitude]
    data[0]["masses"] += [mass]
    data[0]["speeds"] += [speed]
    data[0]["x_speeds"] += [x_speed]
    data[0]["y_speeds"] += [y_speed]
    data[0]["accelerations"] += [acceleration]
    data[0]["x_accelerations"] += [x_acceleration]
    data[0]["y_accelerations"] += [y_acceleration]
    
    time.sleep(0.1) #считывание данных с шагом в 0.1 секунду
    
with open("data_from_ksp.json", 'w', encoding="UTF-8") as file: #запись данных в файл
    json.dump(data, file, ensure_ascii=False, indent=2)
    
