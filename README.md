# Kissinger


<img height="100" src="logo.jpeg" width="100"/>

Современный telegram бот для kispython.ru

![](upload.gif)

Быстрая настройка
## Возможности
Kissinger повторяет все реализованные возможности kispython.ru:
* Выводит условия 
* Загружает код на проверку
* Отображает статус выполнения задания, выводит ошибки компиляции

И даже больше:
* Kissinger запоминает в какой группе вы учитесь и какой у вас вариант
* По умолчанию бот выводит статистику только по вашему варианту, что избавляет пользователя от визуального мусора

![](introdution.gif)

Никогда с первого раза не получается...
## Установка

### 🐋 Лучший способ -- Docker контейнер
Я сделаю его к следующему апдейту, а пока придётся страдать

### 🍥 Если у вас Debian-based Linux:
1. Скопируйте эту команду. Она загрузит репозиторий и установить все необходимые зависимости:

```git clone https://github.com/aaplnv/kissinger && cd kissinger && sudo chmod +x ./install.sh && sudo ./install.sh```

2. Теперь вам нужно заполнить конфигурацию. Откройте config и следуйте по инструкциям:

```nano src/default_config.yml```

3. Теперь можно запускать:
```make run```

### 🍎 Если у вас MacOS:
Завидую.

### 🪟 Если у вас Windows:
Сочувствую.

