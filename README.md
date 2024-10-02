# IT-hack MEPhI. Задача от МосТрансПроекта

## Команда "Три кота на мясо, один на молоко"
- Сороко Надежда
- Авдоченко Ангелина
- Бугаец Арина
- Кузьмина Дарья

## Цель
Прогноз дополнительных нагрузок на дорожно-транспортную сеть (метро и дороги) при вводе новых объектов недвижимости. 

## Решение от команды
Наш проект предназначен для моделирования и анализа изменений нагрузки на транспортную инфраструктуру при вводе новых объектов застройки. Он предоставляет пользователям возможность оценить запас или дефицит пропускной способности дорог и станций метро, что позволяет принимать обоснованные решения в процессе планирования городской застройки. 
Для исходных данных была решена задача о выявлении нагрузок сверх нормы (получены численные оценки), а также разработан интерфейс для взаимодействия с пользователем, который позволяет менять вводимые параметры.

## Техническое описание проекта
Код решения написан на Python. Использовались библиотеки tkinter для создания интерфейса и folium для отображения интерактивной карты. 

### [файл Main_interface.py](/Main_interface.py)
Непосредственно решение от нашей команды, при запуске которого открывается интерфейс

### презентация.pptx
Оформленное в презентацию подробное описание проекта.

## Как использовать?
При запуске фалйа Main_interface.py появляется окно с возможностью изменения входных данных (автоматически все поля заполнены числами из презентации задачи). Пользователь может поменять необходимые коэффициенты на свое усмотрение
