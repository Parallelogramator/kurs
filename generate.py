import re

# Словарь сопоставления клавиш из QT в Arduino HID
KEY_MAP = {
    "CTRL": "LEFT_CTRL",
    "ALT": "LEFT_ALT",
    "SHIFT": "LEFT_SHIFT",
    "ESC": "ESC",
    "ENTER": "RETURN",
    "TAB": "TAB",
    "SPACE": "SPACEBAR",
    "UP": "UP_ARROW",
    "DOWN": "DOWN_ARROW",
    "LEFT": "LEFT_ARROW",
    "RIGHT": "RIGHT_ARROW",
    # Добавьте другие клавиши по необходимости
}


def generate_ino_file(modes):
    """Генерирует файл .ino на основе переданных данных."""
    # Генерация функций для каждого режима
    mode_functions = []
    for mode, actions in modes.items():
        button1_code = generate_button_action(actions["button1"])
        button2_code = generate_button_action(actions["button2"])
        function = f"""
class {mode.lower().replace(" ", "")} : public ModeStrategy {{
public:
    void execute(bool button1State, bool button2State) {{
        if (button1State) {{
            {button1_code}
        }}
        if (button2State) {{
            {button2_code}
        }}
    }}
}};
"""
        mode_functions.append(function)

    # Объединяем функции в код
    template = f"""
#include <HID-Project.h>   // Для реализации HID-функций

// Пины для кнопок, переключателя и потенциометра
const int button1Pin = 2; // Программируемая кнопка 1
const int button2Pin = 3; // Программируемая кнопка 2
const int switchPin = 4;  // Кнопка для переключения режимов
const int potPin = A0;    // Пин потенциометра

// Базовый интерфейс для стратегии
class ModeStrategy {{
public:
    virtual void execute(bool button1State, bool button2State) = 0;
    virtual ~ModeStrategy() = default;
}};

{''.join(mode_functions)}

class ModeContext {{
    ModeStrategy* strategies[{len(modes)}]; // Список стратегий
    int currentMode = 0;

public:
    ModeContext() {{
        {'\n'.join([f'strategies[{i}] = new mode{i + 1}();' for i in range(len(modes))])}
    }}

    ~ModeContext() {{
        for (auto strategy : strategies) {{
            delete strategy;
        }}
    }}

    void switchMode() {{
        currentMode = (currentMode + 1) % {len(modes)}; // Циклический переход по режимам
    }}

    void executeCurrentMode(bool button1State, bool button2State) {{
        strategies[currentMode]->execute(button1State, button2State);
    }}
}};

// Переменные для управления
int lastPotValue = 0;       // Предыдущее значение потенциометра
int debounceDelay = 50;     // Задержка для антидребезга
unsigned long lastDebounceTime = 0;

// Создаем контекст
ModeContext modeContext;

void setup() {{
    // Инициализация пинов
    pinMode(button1Pin, INPUT_PULLUP);
    pinMode(button2Pin, INPUT_PULLUP);
    pinMode(switchPin, INPUT_PULLUP);

    // Инициализация HID
    Keyboard.begin();
    Consumer.begin();
}}

// Переключение режимов
void handleModeSwitch() {{
    static bool lastSwitchState = HIGH;
    bool switchState = digitalRead(switchPin);

    if (switchState != lastSwitchState) {{
        if (millis() - lastDebounceTime > debounceDelay) {{
            modeContext.switchMode(); // Переключаем режим
            lastDebounceTime = millis();
        }}
    }}
    lastSwitchState = switchState;
}}

// Управление громкостью через потенциометр
void handleVolumeControl() {{
    int potValue = analogRead(potPin);

    if (abs(potValue - lastPotValue) > 10) {{ // Проверка изменения
        int volumeChange = map(potValue, 0, 1023, -10, 10);
        if (volumeChange > 0) {{
            for (int i = 0; i < volumeChange; i++) {{
                Consumer.write(MEDIA_VOLUME_UP);
            }}
        }} else {{
            for (int i = 0; i < abs(volumeChange); i++) {{
                Consumer.write(MEDIA_VOLUME_DOWN);
            }}
        }}
        lastPotValue = potValue;
        delay(50);
    }}
}}

// Обработка кнопок
void handleButtonActions() {{
    static bool lastButton1State = HIGH;
    static bool lastButton2State = HIGH;

    bool button1State = digitalRead(button1Pin) == LOW && lastButton1State == HIGH;
    bool button2State = digitalRead(button2Pin) == LOW && lastButton2State == HIGH;

    modeContext.executeCurrentMode(button1State, button2State); // Выполняем текущую стратегию
    delay(200); // Задержка предотвращает дребезг

    lastButton1State = digitalRead(button1Pin);
    lastButton2State = digitalRead(button2Pin);
}}

void loop() {{
    handleModeSwitch();
    handleVolumeControl();
    handleButtonActions();
}}

"""
    with open("kurs.ino", "w", encoding="utf-8") as f:
        f.write(template)
    return 1


def generate_button_action(button):
    """Генерирует действие для кнопки в зависимости от её типа."""
    if button["type"] == "Print Text":
        # Экранируем кавычки внутри текста
        action_text = button["action"].replace('"', '\\"')
        return f'Keyboard.print("{action_text}");'
    elif button["type"] == "Key Combination":
        res = ""
        keys = button["action"].split("+")
        for key in keys:
            arduino_key = KEY_MAP.get(key.upper(), key.upper())
            res += f'Keyboard.press(KEY_{arduino_key});\n'
        res += "Keyboard.releaseAll();"
        return res
    return ""
