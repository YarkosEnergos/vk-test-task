# green-button

Скрипт запускает Android-приложение по имени пакета на телефоне, подключённом через `adb`,
находит на экране зелёную кнопку и нажимает на неё. Если за 10 секунд кнопка не появилась, выводит сообщение.

## Требования

- Python 3.12
- [Android SDK Platform-Tools](https://developer.android.com/tools/releases/platform-tools): `adb` должен быть в `PATH`
- Телефон с включённой отладкой по USB (`adb devices` показывает `device`)

Зависимости (`requirements.txt`):

- `opencv-python-headless==5.0.0.93`
- `numpy==2.5.3`

## Установка

```bash
python3.12 -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

```bash
python main.py com.example.app
python main.py com.example.app --timeout 15
```

Коды выхода: `0` — кнопка нажата, `1` — кнопка не найдена за отведённое время, `2` — ошибка (неверные аргументы, нет `adb` или устройства, приложение не установлено).

## Как это работает

1. `adb shell monkey -p <package> -c android.intent.category.LAUNCHER 1` запускает приложение.
2. Каждые 0,5 с скрипт делает скриншот (`adb exec-out screencap -p`) и ищет на нём кнопку (`detector.py`):
   - переводит изображение в HSV и оставляет зелёные пиксели;
   - выделяет контуры зелёных областей;
   - отбрасывает мелкие области, области во всю ширину экрана (тулбары) и фигуры неправильной формы;
   - из оставшихся выбирает самую крупную область.
3. В центр найденной кнопки отправляется `adb shell input tap x y`.

Appium, UIAutomator и другие автоматизаторы не используются, только команды `adb` и OpenCV.

## Тесты

```bash
pip install -r requirements-dev.txt
python -m pytest
```
