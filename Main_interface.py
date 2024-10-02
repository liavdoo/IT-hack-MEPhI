import folium
from tkinter import *
import random
from tkinter import messagebox


latitude = 55.748082          # Широта 
longitude = 37.680212         # Долгота

living_space = 19e4           # Жилая площадь (население) [m^2]
working_space = 21.4e4        # Нежилая площадь (рабочие места) [m^2]

first_living = 25             # Поэтажная жилая площадь (1 категория) [m^2]
average_home_1 = 2            # Среднее число жильцов в площади первой категории // коэффициент, который мы добавили сами
second_living = 45            # Поэтажная жилая площадь (2 категория) [m^2]
average_home_2 = 3            # Среднее число жильцов в площади второй категории // коэффициент, который мы добавили сами
N = 5000                      # Количество квартир первого типа                  // коэффициент, который мы добавили сами

first_office = 35             # Среднее значение площади офиса [m^2]
average_number_work = 6       # Среднее количество работников на один офис [чел./офис] // коэффициент, который мы добавили сами

coeff_working_people = 0.57   # Доля трудоспособного населения
people_with_IT = 0.3          # Доля использующих индивидуальный транспорт

coeff_avto = 1.2              # Коэффициент заполнения авто

coeff_morning_living = 0.1    # Доля транспортного спроса жилой застройки в час пик
coeff_morning_working = 0.35  # Доля транспортного спроса работников в час пик

# Площадь Ильича / Римская / Серп и Молот
station_rush_morning = [8.4e3, 4.6e3, 1e3]   # Пассажиропоток утром, [тыс.чел./час пик]
station_rush_evening = [5.6e3, 6.6e3, 3.5e3] # Пассажиропоток вечером, [тыс.чел./час пик]
station_limits = [16e3, 16e3, 5e3]           # Максимальная нагрузка станций [тыс.чел./час пик]

# Гжельский пер. / ул. Сергея Радонежского / ул. Золоторожский Вал
traffic_rush = [150, 2400, 300]       # Количество машин в час пик [машин/час]
traffic_points = [3, 7, 5]            # Загруженность дороги в баллах
traffic_lane = [1, 3, 1] # Количество полос // коэффициент, который мы добавили сами

#Ищем следующие величины:
residents=0
workers=0
new_station_rush_m = [0, 0, 0]
new_station_rush_e  = [0, 0, 0]
new_traffic_rush = [0, 0, 0]

overload_station_rush_m = [0, 0, 0]
overload_station_rush_e = [0, 0, 0]
overload_traffic_rush = [0, 0, 0]

#Отрытие карты
map_osm = folium.Map(location=[latitude, longitude], zoom_start=99)
folium.Marker(
    location=[latitude, longitude],
    popup="Ваша точка",
    icon=folium.Icon(color="red", icon="info-sign"),
).add_to(map_osm)
map_osm.save("hahaton_map.html")
import webbrowser
webbrowser.open_new_tab("hahaton_map.html")
# Расчет
def calculate(living_space, working_space,first_living,average_home_1, second_living, average_home_2, N,first_office, average_number_work,coeff_working_people, people_with_IT, coeff_avto, coeff_morning_living, coeff_morning_working, station_rush_morning, station_rush_evening, station_limits, traffic_rush, traffic_points):

    global residents
    global workers
    global new_station_rush_m
    global new_station_rush_e
    global new_traffic_rush
    global overload_station_rush_m
    global overload_station_rush_e
    global overload_traffic_rush

    people_without_IT = 1. - people_with_IT        # Доля использующих общественный транспорт
    traffic_limits = [int(traffic_rush[i]/traffic_points[i]*10) for i in range(len(traffic_rush))] # Максимальная загрузка дорог 
    traffic_lane = [1, 3, 1] # Количество полос
    traffic_limits_per_one = [int(traffic_limits[i]/traffic_lane[i]) for i in range(len(traffic_limits))] # "Средняя загруженность" одной полосы

    """Ниже - функция подсчета необходимых для разгрузки дорожных полос (выводит список количеств (0 - если дорога не перегружена))"""

    lanes_needed = []
    def lane_deficit(new_traffic_rush, is_traffic_problems):
      lanes_needed.clear()
      for i in range(len(traffic_limits)):
        if is_traffic_problems[i] != False:
          lanes_needed.append(int((new_traffic_rush[i] - traffic_limits[i]) // traffic_limits_per_one[i] + 1 ))
        else:
          lanes_needed.append("-")  

    """
    Расчет количества населения через площади: на жилых площадях будет $n_1$ человек на $25м^2$ или $n_2$ человек $45м^2$, а на офисных соответственно $n_{of}$ человек на $35м^2$. Средние площади, кстати говоря, тоже параметр задачи

    В нашем предположении существует жилье 2 типов, причем примерное количество квартир первого типа известно (равно N).
    """

    def residents_(living_space, first_living, second_living, N, average_home_1, average_home_2):
      return N*average_home_1 + (living_space - N * first_living) // second_living * average_home_2 + 1

    def workers_(working_space, first_office, average_number_work):
      return (working_space // first_office + 1) * average_number_work

    """Здесь считаем непосредственно количество жильцов района и работников
    """

    residents = residents_(living_space, first_living, second_living, N, average_home_1, average_home_2)
    workers = workers_(working_space, first_office, average_number_work)

    """# **Подсчет новой нагрузки**

    Здесь идет подсчет прибавки загруженности на станциях и дорогах (т.е. количество людей и машин сверху)

    "Спрос" с человеческой стороны расчитывается через сумму доли жителей и доли работников:

    * Доля от жителей: количество жителей * доля трудоспособного населения * доля отсчета жителей по утрам * доля людей на общественном транспорте

    * Доля от работяг: количество работяг * доля отсчета работяг по утрам * доля людей на общественном транспорте

    "Спрос" от машин - аналогично, но домножается на долю людей на индивидуальном транспорте и делится на коэффициент заполняемости авто

    Далее рассчитала прибавку в час пик следующим образом: посчитала суммарное число людей на всех станциях / машин на дорогах, потом для каждого элемента (станции или дороги) нашла относительную долю потока и умножила на количество "спроса" людей/машин
    """

    spros_people = (residents * coeff_working_people * coeff_morning_living  + workers * coeff_morning_working) * people_without_IT
    spros_cars = int((residents * coeff_working_people * coeff_morning_living + workers * coeff_morning_working) * people_with_IT / coeff_avto) + 1

    people_plus_morning = []
    people_plus_evening = []
    cars_plus = []

    for element in station_rush_morning:
      people_plus_morning.append(int(element/sum(station_rush_morning)*spros_people)+1)

    for element in station_rush_evening:
      people_plus_evening.append(int(element/sum(station_rush_evening)*spros_people)+1)

    for element in traffic_rush:
      cars_plus.append(int(element/sum(traffic_rush) * spros_cars * coeff_working_people) + 1)

    """тут прибавляем к уже имеющимся нагрузкам на станциях/дорогах спрос и сравнила с пределами загрузки станций"""

    new_station_rush_m = [station_rush_morning[i] + people_plus_morning[i] for i in range(len(station_rush_morning))]
    new_station_rush_e = [station_rush_evening[i] + people_plus_evening[i] for i in range(len(station_rush_evening))]
    new_traffic_rush = [traffic_rush[i] + cars_plus[i] for i in range(len(traffic_rush))]

    is_station_problems_m = [new_station_rush_m[i]>station_limits[i] for i in range(len(new_station_rush_m))]
    is_station_problems_e = [new_station_rush_e[i]>station_limits[i] for i in range(len(new_station_rush_e))]
    is_traffic_problems = [new_traffic_rush[i]>traffic_limits[i] for i in range(len(new_traffic_rush))]

    lane_deficit(new_traffic_rush, is_traffic_problems)
    
    """Непосредственные количества людей/машин, которые превышают максимальную нагрузку"""

    def load_problem(new_arr, limits):
      load=[]
      for i in range(len(new_arr)):
        if new_arr[i] - limits[i] > 0:
          load.append(new_arr[i] - limits[i])
        else:
          load.append("-")

      return load

    overload_station_rush_m = load_problem(new_station_rush_m, station_limits) # Сверхнагрузка утром на станции
    overload_station_rush_e = load_problem(new_station_rush_e, station_limits) # Сверхнагрузка вечером на станции
    overload_traffic_rush = load_problem(new_traffic_rush, traffic_limits) # Сверхнагрузка на дороги

    return is_station_problems_m, is_station_problems_e, is_traffic_problems, is_traffic_problems, lanes_needed


# Создаем главное окно приложения
root = Tk()
root.title("Расчет нагрузки на инфраструктуру")
root.geometry("1800x1100")

# Создаем холст для прокрутки и фрейм для ввода данных
canvas = Canvas(root)
scrollbar = Scrollbar(root, orient="vertical", command=canvas.yview)
table_frame = Frame(canvas)

table_frame.bind(
    "<Configure>",
    lambda e: canvas.configure(
        scrollregion=canvas.bbox("all")
    )
)

canvas.create_window((0, 0), window=table_frame)

canvas.configure(yscrollcommand=scrollbar.set)

canvas.pack(side="left", fill="both", expand=True)
scrollbar.pack(side="right", fill="y")

####################
# Размещение элементов на форме

Input = Frame(table_frame)
Botton_frame = Frame(table_frame)
Output = Frame(table_frame)
 
Input.pack(fill = BOTH, expand = True, anchor="center")
Botton_frame.pack(fill = BOTH, expand = True, anchor="center")
Output.pack(fill = BOTH, expand = True, anchor="center")

# Надписи для полей ввода
label_living_space = Label(Input, text="Жилая площадь (население) [m^2]")
label_working_space = Label(Input, text="Нежилая площадь (рабочие места) [m^2]")
label_first_living = Label(Input, text="Поэтажная жилая площадь (1 категория) [m^2]")
label_average_home_1 = Label(Input, text="Среднее число жильцов в площади первой категории")
label_second_living = Label(Input, text="Поэтажная жилая площадь (2 категория) [m^2]")
label_average_home_2 = Label(Input, text="Среднее число жильцов в площади второй категории")
label_N = Label(Input, text="Количество квартир первого типа")
label_first_office = Label(Input, text="Среднее значение площади офиса [m^2]")
label_average_number_work = Label(Input, text="Среднее количество работников на один офис [чел./офис]")
label_coeff_working_people = Label(Input, text="Доля трудоспособного населения")
label_people_with_IT= Label(Input, text="Доля использующих индивидуальный транспорт")
label_coeff_avto = Label(Input, text="Коэффициент заполнения авто")
label_coeff_morning_living = Label(Input, text="Доля транспортного спроса жилой застройки в час пик")
label_coeff_morning_working = Label(Input, text="Доля транспортного спроса работников в час пик")
label_station_rush_morning_0 = Label(Input, text="Площадь Ильича, Пассажиропоток утром [тыс.чел./час пик]")
label_station_rush_morning_1 = Label(Input, text="Римская, Пассажиропоток утром [тыс.чел./час пик]")
label_station_rush_morning_2 = Label(Input, text="Серп и Молот, Пассажиропоток утром [тыс.чел./час пик]")
label_station_rush_evening_0 = Label(Input, text="Площадь Ильича, Пассажиропоток вечером [тыс.чел./час пик]")
label_station_rush_evening_1 = Label(Input, text="Римская, Пассажиропоток вечером [тыс.чел./час пик]")
label_station_rush_evening_2 = Label(Input, text="Серп и Молот, Пассажиропоток вечером [тыс.чел./час пик]")
label_station_limits_0 = Label(Input, text="Площадь Ильича, Максимальная нагрузка станций [тыс.чел./час пик]")
label_station_limits_1 = Label(Input, text="Римская, Максимальная нагрузка станций [тыс.чел./час пик]")
label_station_limits_2 = Label(Input, text="Серп и Молот, Максимальная нагрузка станций [тыс.чел./час пик]")
label_traffic_rush_0 = Label(Input, text="Гжельский пер., Количество машин в час пик [машин/час]")
label_traffic_rush_1 = Label(Input, text="ул. Сергея Радонежского, Количество машин в час пик [машин/час]")
label_traffic_rush_2 = Label(Input, text="ул. Золоторожский Вал, Количество машин в час пик [машин/час]")
label_traffic_points_0 = Label(Input, text="Гжельский пер., Загруженность дороги в баллах")
label_traffic_points_1 = Label(Input, text="ул. Сергея Радонежского, Загруженность дороги в баллах")
label_traffic_points_2 = Label(Input, text="ул. Золоторожский Вал, Загруженность дороги в баллах")


# Поля ввода для адреса, типа и площади
living_space_entry = Entry(Input)
working_space_entry = Entry(Input)
first_living_entry = Entry(Input)
average_home_1_entry = Entry(Input)
second_living_entry = Entry(Input)
average_home_2_entry = Entry(Input)
N_entry = Entry(Input)
first_office_entry = Entry(Input)
average_number_work_entry = Entry(Input)
coeff_working_people_entry = Entry(Input)
people_with_IT_entry = Entry(Input)
coeff_avto_entry = Entry(Input)
coeff_morning_living_entry = Entry(Input)
coeff_morning_working_entry = Entry(Input)
station_rush_morning_0_entry = Entry(Input)
station_rush_morning_1_entry = Entry(Input)
station_rush_morning_2_entry = Entry(Input)
station_rush_evening_0_entry = Entry(Input)
station_rush_evening_1_entry = Entry(Input)
station_rush_evening_2_entry = Entry(Input)
station_limits_0_entry = Entry(Input)
station_limits_1_entry = Entry(Input)
station_limits_2_entry = Entry(Input)
traffic_rush_0_entry = Entry(Input)
traffic_rush_1_entry = Entry(Input)
traffic_rush_2_entry = Entry(Input)
traffic_points_0_entry = Entry(Input)
traffic_points_1_entry = Entry(Input)
traffic_points_2_entry = Entry(Input)
time_entry = Entry(Input)

# Размещение элементов на форме

# Названия:
label_living_space.grid(row=0, column=0, sticky=W, padx=10, pady=5)
label_working_space.grid(row=1, column=0, sticky=W, padx=10, pady=5)
label_first_living.grid(row=2, column=0, sticky=W, padx=10, pady=5)
label_average_home_1.grid(row=3, column=0, sticky=W, padx=10, pady=5)
label_second_living.grid(row=4, column=0, sticky=W, padx=10, pady=5)
label_average_home_2.grid(row=5, column=0, sticky=W, padx=10, pady=5)
label_N.grid(row=6, column=0, sticky=W, padx=10, pady=5)
label_first_office.grid(row=7, column=0, sticky=W, padx=10, pady=5)
label_average_number_work.grid(row=8, column=0, sticky=W, padx=10, pady=5)
label_coeff_working_people.grid(row=9, column=0, sticky=W, padx=10, pady=5)
label_people_with_IT.grid(row=10, column=0, sticky=W, padx=10, pady=5)
label_coeff_avto.grid(row=11, column=0, sticky=W, padx=10, pady=5)
label_coeff_morning_living.grid(row=12, column=0, sticky=W, padx=10, pady=5)
label_coeff_morning_working.grid(row=13, column=0, sticky=W, padx=10, pady=5)
label_station_rush_morning_0.grid(row=14, column=0, sticky=W, padx=10, pady=5)
label_station_rush_morning_1.grid(row=0, column=2, sticky=W, padx=10, pady=5)
label_station_rush_morning_2.grid(row=1, column=2, sticky=W, padx=10, pady=5)
label_station_rush_evening_0.grid(row=2, column=2, sticky=W, padx=10, pady=5)
label_station_rush_evening_1.grid(row=3, column=2, sticky=W, padx=10, pady=5)
label_station_rush_evening_2.grid(row=4, column=2, sticky=W, padx=10, pady=5)
label_station_limits_0.grid(row=5, column=2, sticky=W, padx=10, pady=5)
label_station_limits_1.grid(row=6, column=2, sticky=W, padx=10, pady=5)
label_station_limits_2.grid(row=7, column=2, sticky=W, padx=10, pady=5)
label_traffic_rush_0.grid(row=8, column=2, sticky=W, padx=10, pady=5)
label_traffic_rush_1.grid(row=9, column=2, sticky=W, padx=10, pady=5)
label_traffic_rush_2.grid(row=10, column=2, sticky=W, padx=10, pady=5)
label_traffic_points_0.grid(row=11, column=2, sticky=W, padx=10, pady=5)
label_traffic_points_1.grid(row=12, column=2, sticky=W, padx=10, pady=5)
label_traffic_points_2.grid(row=13, column=2, sticky=W, padx=10, pady=5)

# Ячейки:
living_space_entry.grid(row=0, column=1, padx=10, pady=5)
working_space_entry.grid(row=1, column=1, padx=10, pady=5)
first_living_entry.grid(row=2, column=1, padx=10, pady=5)
average_home_1_entry.grid(row=3, column=1, padx=10, pady=5)
second_living_entry.grid(row=4, column=1, padx=10, pady=5)
average_home_2_entry.grid(row=5, column=1, padx=10, pady=5)
N_entry.grid(row=6, column=1, padx=10, pady=5)
first_office_entry.grid(row=7, column=1, padx=10, pady=5)
average_number_work_entry.grid(row=8, column=1, padx=10, pady=5)
coeff_working_people_entry.grid(row=9, column=1, padx=10, pady=5)
people_with_IT_entry.grid(row=10, column=1, padx=10, pady=5)
coeff_avto_entry.grid(row=11, column=1, padx=10, pady=5)
coeff_morning_living_entry.grid(row=12, column=1, padx=10, pady=5)
coeff_morning_working_entry.grid(row=13, column=1, padx=10, pady=5)
station_rush_morning_0_entry.grid(row=14, column=1, padx=10, pady=5)
station_rush_morning_1_entry.grid(row=0, column=3, padx=10, pady=5)
station_rush_morning_2_entry.grid(row=1, column=3, padx=10, pady=5)
station_rush_evening_0_entry.grid(row=2, column=3, padx=10, pady=5)
station_rush_evening_1_entry.grid(row=3, column=3, padx=10, pady=5)
station_rush_evening_2_entry.grid(row=4, column=3, padx=10, pady=5)
station_limits_0_entry.grid(row=5, column=3, padx=10, pady=5)
station_limits_1_entry.grid(row=6, column=3, padx=10, pady=5)
station_limits_2_entry.grid(row=7, column=3, padx=10, pady=5)
traffic_rush_0_entry.grid(row=8, column=3, padx=10, pady=5)
traffic_rush_1_entry.grid(row=9, column=3, padx=10, pady=5)
traffic_rush_2_entry.grid(row=10, column=3, padx=10, pady=5)
traffic_points_0_entry.grid(row=11, column=3, padx=10, pady=5)
traffic_points_1_entry.grid(row=12, column=3, padx=10, pady=5)
traffic_points_2_entry.grid(row=13, column=3, padx=10, pady=5)

# Автозаполнение ячеек
living_space_entry.insert(0, "19e4")
working_space_entry.insert(0, "21.4e4")
first_living_entry.insert(0, "25")
average_home_1_entry.insert(0, "2")
second_living_entry.insert(0, "45")
average_home_2_entry.insert(0, "3")
N_entry.insert(0, "5000")
first_office_entry.insert(0, "35")
average_number_work_entry.insert(0, "6")
coeff_working_people_entry.insert(0, "0.57")
people_with_IT_entry.insert(0, "0.3")
coeff_avto_entry.insert(0, "1.2")
coeff_morning_living_entry.insert(0, "0.1")
coeff_morning_working_entry.insert(0, "0.35")
station_rush_morning_0_entry.insert(0, "8.4e3")
station_rush_morning_1_entry.insert(0, "4.6e3")
station_rush_morning_2_entry.insert(0, "1e3")
station_rush_evening_0_entry.insert(0, "5.6e3")
station_rush_evening_1_entry.insert(0, "6.6e3")
station_rush_evening_2_entry.insert(0, "3.5e3")
station_limits_0_entry.insert(0, "16e3")
station_limits_1_entry.insert(0, "16e3")
station_limits_2_entry.insert(0, "5e3")
traffic_rush_0_entry.insert(0, "150")
traffic_rush_1_entry.insert(0, "2400")
traffic_rush_2_entry.insert(0, "300")
traffic_points_0_entry.insert(0, "3")
traffic_points_1_entry.insert(0, "7")
traffic_points_2_entry.insert(0, "5")

label_error = Label(Botton_frame, text="")

# Кнопка для расчета
def input():
    
    global residents
    global workers
    global new_station_rush_m
    global new_station_rush_e
    global new_traffic_rush
    global load
    global living_space
    global working_space
    global first_living
    global average_home_1
    global second_living
    global average_home_2
    global N
    global first_office
    global average_number_work
    global coeff_working_people
    global people_with_IT
    global coeff_avto
    global coeff_morning_living
    global coeff_morning_working
    global station_rush_morning
    global station_rush_evening
    global station_limits
    global traffic_rush
    global traffic_points

    global is_station_problems_m
    global is_station_problems_e
    global is_traffic_problems
    global is_traffic_problems
    global lanes_needed 
    global label_error
      
    # Получаем данные из полей ввода
    label_error.destroy()

    living_space = living_space_entry.get()
    # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          living_space = float(living_space)
        
          # Проверяем, что число >= 0
          if living_space < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Жилая площадь' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)


      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Жилая площадь' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)

  
    working_space = working_space_entry.get()
    # Проверка введенных данных 
    try:
          # Преобразуем значение в число с плавающей точкой
          working_space = float(working_space)
        
          # Проверяем, что число >= 0
          if working_space < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Нежилая площадь' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Нежилая площадь' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)

    first_living = first_living_entry.get()
    # Проверка введенных данных  
    try:
          # Преобразуем значение в число с плавающей точкой
          first_living = float(first_living)
        
          # Проверяем, что число >= 0
          if first_living < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Поэтажная жилая площадь (1 категория) ' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Поэтажная жилая площадь (1 категория) ' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)

    average_home_1 = average_home_1_entry.get()
    # Проверка введенных данных    
    try:
          # Преобразуем значение в число с плавающей точкой
          average_home_1 = float(average_home_1)
        
          # Проверяем, что число >= 0
          if average_home_1 < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее число жильцов в площади первой категории' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее число жильцов в площади первой категории' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    second_living = second_living_entry.get()
    # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          second_living = float(second_living)
        
          # Проверяем, что число >= 0
          if second_living < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Поэтажная жилая площадь (2 категория)' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Поэтажная жилая площадь (2 категория)' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    average_home_2 = average_home_2_entry.get()
    # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          average_home_2 = float(average_home_2)
        
          # Проверяем, что число >= 0
          if average_home_2 < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее число жильцов в площади второй категории' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее число жильцов в площади второй категории' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    N = N_entry.get()
    # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          N = float(N)
        
          # Проверяем, что число >= 0
          if N <= 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Количество квартир первого типа' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Количество квартир первого типа' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  

    first_office = first_office_entry.get()
    # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          first_office = float(first_office)
        
          # Проверяем, что число >= 0
          if first_office < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее значение площади офиса' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее значение площади офиса' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    average_number_work = average_number_work_entry.get()
    # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          average_number_work = float(average_number_work)
        
          # Проверяем, что число >= 0
          if average_number_work < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее количество работников на один офис' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Среднее количество работников на один офис' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  

    coeff_working_people = coeff_working_people_entry.get()
    # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          coeff_working_people = float(coeff_working_people)
        
          # Проверяем, что число >= 0
          if coeff_working_people < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля трудоспособного населения' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)
          if coeff_working_people > 1 :
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля трудоспособного населения' должно быть меньше 1!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля трудоспособного населения' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    people_with_IT=people_with_IT_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          people_with_IT = float(people_with_IT)
        
          # Проверяем, что число >= 0
          if people_with_IT < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля использующих индивидуальный транспорт' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

          if people_with_IT > 1:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля использующих индивидуальный транспорт' должно быть меньше 1!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля использующих индивидуальный транспорт' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    

    coeff_avto = coeff_avto_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          coeff_avto = float(coeff_avto)
        
          # Проверяем, что число >= 0
          if coeff_avto < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Коэффициент заполнения авто' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Коэффициент заполнения авто' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    

    coeff_morning_living = coeff_morning_living_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          coeff_morning_living = float(coeff_morning_living)
        
          # Проверяем, что число >= 0
          if coeff_morning_living < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля транспортного спроса жилой застройки в час пик' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)
          if coeff_morning_living > 1:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля транспортного спроса жилой застройки в час пик' должно быть меньше 1!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля транспортного спроса жилой застройки в час пик' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    coeff_morning_working = coeff_morning_working_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          coeff_morning_working = float(coeff_morning_working)
        
          # Проверяем, что число >= 0
          if coeff_morning_working < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля транспортного спроса работников в час пик' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)
          if coeff_morning_working > 1:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля транспортного спроса работников в час пик' должно быть меньше 1!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Доля транспортного спроса работников в час пик' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    

    station_rush_morning[0] = station_rush_morning_0_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_rush_morning[0] = float(station_rush_morning[0])
        
          # Проверяем, что число >= 0
          if station_rush_morning[0] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Площадь Ильича, Пассажиропоток утром' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Площадь Ильича, Пассажиропоток утром' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    station_rush_morning[1] = station_rush_morning_1_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_rush_morning[1] = float(station_rush_morning[1])
        
          # Проверяем, что число >= 0
          if station_rush_morning[1] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Римская, Пассажиропоток утром' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Римская, Пассажиропоток утром' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    station_rush_morning[2] = station_rush_morning_2_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_rush_morning[2] = float(station_rush_morning[2])
        
          # Проверяем, что число >= 0
          if station_rush_morning[2] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Серп и Молот, Пассажиропоток утром' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Серп и Молот, Пассажиропоток утром' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    station_rush_evening[0] = station_rush_evening_0_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_rush_evening[0] = float(station_rush_evening[0])
        
          # Проверяем, что число >= 0
          if station_rush_evening[0] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Площадь Ильича, Пассажиропоток вечером' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Площадь Ильича, Пассажиропоток вечером' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    station_rush_evening[1] = station_rush_evening_1_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_rush_evening[1] = float(station_rush_evening[1])
        
          # Проверяем, что число >= 0
          if station_rush_evening[1] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Римская, Пассажиропоток вечером' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Римская, Пассажиропоток вечером' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    station_rush_evening[2] = station_rush_evening_2_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_rush_evening[2] = float(station_rush_evening[2])
        
          # Проверяем, что число >= 0
          if station_rush_evening[2] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Серп и Молот, Пассажиропоток вечером' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Серп и Молот, Пассажиропоток вечером' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    station_limits[0] = station_limits_0_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_limits[0] = float(station_limits[0])
        
          # Проверяем, что число >= 0
          if station_limits[0] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Площадь Ильича, Максимальная нагрузка станций' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Площадь Ильича, Максимальная нагрузка станций' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    station_limits[1] = station_limits_1_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_limits[1] = float(station_limits[1])
        
          # Проверяем, что число >= 0
          if station_limits[1] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Римская, Максимальная нагрузка станций' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Римская, Максимальная нагрузка станций' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    station_limits[2] = station_limits_2_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          station_limits[2] = float(station_limits[2])
        
          # Проверяем, что число >= 0
          if station_limits[2] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Серп и Молот, Максимальная нагрузка станций' должно быть неотрицательным", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Серп и Молот, Максимальная нагрузка станций' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
    
    traffic_rush[0] = traffic_rush_0_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          traffic_rush[0] = float(traffic_rush[0])
        
          # Проверяем, что число >= 0
          if traffic_rush[0] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Гжельский пер., Количество машин в час пик' должно неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Гжельский пер., Количество машин в час пик' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    traffic_rush[1] = traffic_rush_1_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          traffic_rush[1] = float(traffic_rush[1])
        
          # Проверяем, что число >= 0
          if traffic_rush[1] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Сергея Радонежского, Количество машин в час пик' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Сергея Радонежского , Количество машин в час пик' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    traffic_rush[2] = traffic_rush_2_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          traffic_rush[2] = float(traffic_rush[2])
        
          # Проверяем, что число >= 0
          if traffic_rush[2] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Золоторожский Вал, Количество машин в час пик' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Золоторожский Вал, Количество машин в час пик' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    traffic_points[0] = traffic_points_0_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          traffic_points[0] = float(traffic_points[0])
        
          # Проверяем, что число >= 0
          if traffic_points[0] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Гжельский пер., Загруженность дороги в баллах' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'Гжельский пер., Загруженность дороги в баллах' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    traffic_points[1] = traffic_points_1_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          traffic_points[1] = float(traffic_points[1])
        
          # Проверяем, что число >= 0
          if traffic_points[1] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Сергея Радонежского , Загруженность дороги в баллах' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Сергея Радонежского , Загруженность дороги в баллах' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  
    traffic_points[2] = traffic_points_2_entry.get()
        # Проверка введенных данных
    try:
          # Преобразуем значение в число с плавающей точкой
          traffic_points[2] = float(traffic_points[2])
        
          # Проверяем, что число >= 0
          if traffic_points[2] < 0:
              label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Золоторожский Вал, Загруженность дороги в баллах' должно быть неотрицательным!", font=("TkDefaultFont", 24))
              label_error.pack(padx=10, pady=5)

      
    except ValueError:
          # Если значение не может быть преобразовано в число
          label_error = Label(Botton_frame, foreground="#B71C1C", text=f"Ошибка! Значение 'ул. Золоторожский Вал, Загруженность дороги в баллах' должно быть числом!", font=("TkDefaultFont", 24))
          label_error.pack(padx=10, pady=5)
  

    # Делаем расчеты
    is_station_problems_m, is_station_problems_e, is_traffic_problems, is_traffic_problems, lanes_needed = calculate(living_space, working_space,first_living,average_home_1, second_living, average_home_2, N,first_office, average_number_work,coeff_working_people, people_with_IT, coeff_avto, coeff_morning_living, coeff_morning_working, station_rush_morning, station_rush_evening, station_limits, traffic_rush, traffic_points)
    
    # Очищаем фрейм вывода
    for widget in Output.winfo_children():
       widget.destroy()

    # Выводим результаты
    print_results()

    
    
    
input_button = Button(Botton_frame, text="Рассчитать нагрузку",font=("TkDefaultFont", 24), command=input)
input_button.pack(pady=10)

# Вывод результатов
def print_results():
    current_row=0
    result_label = Label(Output, text="РЕЗУЛЬТАТЫ", font=("TkDefaultFont", 24))
    result_label.grid(row=current_row, column=2, padx=20, pady=5)
    current_row+=1

    label_residents = Label(Output, text=f"Количество жильцов района [чел.]: {residents}")
    label_residents.grid(row=current_row, column=2, padx=20, pady=5)
    current_row+=1

    label_workers = Label(Output, text=f"Количество приезжающих на работу [чел.]: {workers}")
    label_workers.grid(row=current_row, column=2, padx=20, pady=5)
    current_row+=1

#########################################
    label_new_station_rush_m = Label(Output, text=f"ПАССАЖИРОПОТОК УТРОМ: [тыс.чел./час пик]", font=("TkDefaultFont", 16))
    label_new_station_rush_m.grid(row=current_row, column=2, padx=20, pady=5)
    current_row+=1

    col=""
    if (is_station_problems_m[0]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_station_rush_m_0 = Label(Output, foreground=col, text=f"Площадь Ильича - {new_station_rush_m[0]}")
    label_new_station_rush_m_0.grid(row=current_row, column=1, padx=20, pady=5)

    if (is_station_problems_m[1]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_station_rush_m_1 = Label(Output, foreground=col, text=f"Римская - {new_station_rush_m[1]}")
    label_new_station_rush_m_1.grid(row=current_row, column=2, padx=20, pady=5)

    if (is_station_problems_m[2]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_station_rush_m_2 = Label(Output, foreground=col, text=f"Серп и Молот - {new_station_rush_m[2]}")
    label_new_station_rush_m_2.grid(row=current_row, column=3, padx=20, pady=5)
    
    current_row+=1

    label_overload_station_rush_m = Label(Output, text=f"Сверхнагрузка на станции [тыс.чел./час пик]:")
    label_overload_station_rush_m.grid(row=current_row, sticky=E, column=0, padx=30, pady=5)

    label_overload_station_rush_m_0 = Label(Output, text=overload_station_rush_m[0])
    label_overload_station_rush_m_0.grid(row=current_row, column=1, padx=30, pady=5)
    label_overload_station_rush_m_1 = Label(Output, text=overload_station_rush_m[1])
    label_overload_station_rush_m_1.grid(row=current_row, column=2, padx=30, pady=5)
    label_overload_station_rush_m_2 = Label(Output, text=overload_station_rush_m[2])
    label_overload_station_rush_m_2.grid(row=current_row, column=3, padx=30, pady=5)

    current_row+=1
####################################
    label_new_station_rush_e = Label(Output, text=f"ПАССАЖИРОПОТОК ВЕЧЕРОМ [тыс.чел./час пик]:", font=("TkDefaultFont", 16))
    label_new_station_rush_e.grid(row=current_row, column=2, padx=20, pady=5)
    current_row+=1

    if (is_station_problems_e[0]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_station_rush_e_0 = Label(Output, foreground=col, text=f"Площадь Ильича - {new_station_rush_e[0]}")
    label_new_station_rush_e_0.grid(row=current_row, column=1, padx=20, pady=5)

    if (is_station_problems_e[1]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_station_rush_e_1 = Label(Output, foreground=col, text=f"Римская - {new_station_rush_e[1]}")
    label_new_station_rush_e_1.grid(row=current_row, column=2, padx=20, pady=5)

    if (is_station_problems_e[2]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_station_rush_e_2 = Label(Output, foreground=col, text=f"Серп и Молот - {new_station_rush_e[2]}")
    label_new_station_rush_e_2.grid(row=current_row, column=3, padx=20, pady=5)

    current_row+=1

    label_overload_station_rush_e = Label(Output, text=f"Сверхнагрузка на станции [тыс.чел./час пик]:")
    label_overload_station_rush_e.grid(row=current_row, column=0, padx=20, pady=5)

    label_overload_station_rush_e_0 = Label(Output, text=overload_station_rush_e[0])
    label_overload_station_rush_e_0.grid(row=current_row, column=1, padx=20, pady=5)
    label_overload_station_rush_e_1 = Label(Output, text=overload_station_rush_e[1])
    label_overload_station_rush_e_1.grid(row=current_row, column=2, padx=20, pady=5)
    label_overload_station_rush_e_2 = Label(Output, text=overload_station_rush_e[2])
    label_overload_station_rush_e_2.grid(row=current_row, column=3, padx=20, pady=5)

    current_row+=1
#######################################################
    label_new_traffic_rush = Label(Output, text=f"ЗАГРУЗКА ДОРОГ [машин/час]:", font=("TkDefaultFont", 16))
    label_new_traffic_rush.grid(row=current_row, column=2, padx=20, pady=5)
    current_row+=1

    if (is_traffic_problems[0]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_traffic_rush_0 = Label(Output, foreground=col, text=f"Гжельский пер. - {new_traffic_rush[0]}")
    label_new_traffic_rush_0.grid(row=current_row, column=1, padx=20, pady=5)

    if (is_traffic_problems[1]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_traffic_rush_1 = Label(Output, foreground=col, text=f"ул. Сергея Радонежского - {new_traffic_rush[1]}")
    label_new_traffic_rush_1.grid(row=current_row, column=2, padx=20, pady=5)

    if (is_traffic_problems[2]):
      col="#B71C1C"
    else:
      col="#0BDA51"
    label_new_traffic_rush_2 = Label(Output, foreground=col, text=f"ул. Золоторожский Вал - {new_traffic_rush[2]}")
    label_new_traffic_rush_2.grid(row=current_row, column=3, padx=20, pady=5)

    current_row+=1

    label_overload_traffic_rush = Label(Output, text=f"Сверхнагрузка на дороги [машин/час]:")
    label_overload_traffic_rush.grid(row=current_row, column=0, padx=20, pady=5)

    label_overload_traffic_rush_0 = Label(Output, text=overload_traffic_rush[0])
    label_overload_traffic_rush_0.grid(row=current_row, column=1, padx=20, pady=5)
    label_overload_traffic_rush_1 = Label(Output, text=overload_traffic_rush[1])
    label_overload_traffic_rush_1.grid(row=current_row, column=2, padx=20, pady=5)
    label_overload_traffic_rush_2 = Label(Output, text=overload_traffic_rush[2])
    label_overload_traffic_rush_2.grid(row=current_row, column=3, padx=20, pady=5)

    current_row+=1
    
    label_lanes_needed = Label(Output, text=f"Дефицит дорожных полос:")
    label_lanes_needed.grid(row=current_row, column=0, padx=20, pady=5)

    label_lanes_needed_0 = Label(Output, text=lanes_needed[0])
    label_lanes_needed_0.grid(row=current_row, column=1, padx=20, pady=5)
    label_lanes_needed_1 = Label(Output, text=lanes_needed[1])
    label_lanes_needed_1.grid(row=current_row, column=2, padx=20, pady=5)
    label_lanes_needed_2 = Label(Output, text=lanes_needed[2])
    label_lanes_needed_2.grid(row=current_row, column=3, padx=20, pady=5)

    current_row+=1

# Запуск цикла обработки событий
root.mainloop()
