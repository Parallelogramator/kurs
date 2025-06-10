KEY_MAP = {
    "CTRL": "LEFT_CTRL",
    "ALT": "LEFT_ALT",
    "SHIFT": "LEFT_SHIFT",
    "ESCAPE": "ESC",
    "ENTER": "RETURN",
    "TAB": "TAB",
    "SPACE": "SPACEBAR",
    "UP": "UP_ARROW",
    "DOWN": "DOWN_ARROW",
    "LEFT": "LEFT_ARROW",
    "RIGHT": "RIGHT_ARROW",
}


def generate_ino_file(modes, standard_buttons, dropdown_buttons):
    try:
        """Генерирует файл .ino на основе переданных данных."""
        mode_functions = []
        for mode, actions in modes.items():
            button_code = []
            for button, action in actions["standard_buttons"].items():
                button_code.append(generate_standard_button_action(button[-1], action))
            dropdown_code = []
            for button, action in actions["dropdown_buttons"].items():
                if action != 'Nothing':
                    dropdown_code.append(f'handle{action}Control(A{int(button[-1]) - 1});')

            function = f"""
    class {mode.lower().replace(" ", "")} : public ModeStrategy {{
    public:
        void execute() override{{
            bool {','.join([f'button{i + 1}State' for i in range(standard_buttons)])};
            checkButtonStates({','.join([f'button{i + 1}State' for i in range(standard_buttons)])});
            {'\n'.join([i for i in button_code])};
            
            {'\n'.join([i for i in dropdown_code])}
        }}
    }};
    """
            mode_functions.append(function)

        template = f"""
    #include <HID-Project.h>   // Для реализации HID-функций
    
    // Пины для кнопок, переключателя и потенциометра
    {'\n'.join([f'const int button{i + 1}Pin = {i + 2};' for i in range(standard_buttons)])}
    const int switchPin = 4;  // Кнопка для переключения режимов
    {'\n'.join([f'const int pot{i}Pin = A{i};' for i in range(dropdown_buttons)])}
    
    void handleVolumeControl(int pin) {{
    static int lastPotValue = 0; // Предыдущее значение потенциометра
    int potValue = analogRead(pin);

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
    
    // Базовый интерфейс для стратегии
    class ModeStrategy {{
    public:
        virtual void execute() = 0;
        virtual ~ModeStrategy() = default;
    }};
    
    {'\n'.join(mode_functions)}
    
    class ModeContext {{
        ModeStrategy* strategies[{len(modes)}]; // Список стратегий
        int currentMode = 0;
    
    public:
        ModeContext() {{
            {'\n'.join([f'strategies[{n}] = new {i.lower().replace(" ", "")}();' for n, i in enumerate(modes.keys())])}
        }}
    
        ~ModeContext() {{
            for (auto strategy : strategies) {{
                delete strategy;
            }}
        }}
    
        void switchMode() {{
            currentMode = (currentMode + 1) % {len(modes)}; // Циклический переход по режимам
        }}
    
        void executeCurrentMode() {{
            strategies[currentMode]->execute();
        }}
    }};
    
    // Переменные для управления
    int lastPotValue = 0;       // Предыдущее значение потенциометра
    int debounceDelay = 500;     // Задержка для антидребезга
    unsigned long lastDebounceTime = 0;
    
    // Создаем контекст
    ModeContext modeContext;
    
    void setup() {{
        // Инициализация пинов
        {'\n'.join([f'pinMode(button{i + 1}Pin, INPUT_PULLUP);' for i in range(standard_buttons)])}
        pinMode(switchPin, INPUT_PULLUP);
    
        // Инициализация HID
        Keyboard.begin();
        Consumer.begin();
    }}
    
    
    // Обработка кнопок
    void checkButtonStates({','.join([f'bool &button{i + 1}State' for i in range(standard_buttons)])}) {{
    {'\n'.join([f'button{i + 1}State = digitalRead(button{i + 1}Pin) == HIGH;' for i in range(standard_buttons)])}
    }}  
    
    void loop() {{
    bool switchState = digitalRead(switchPin);

    if (switchState) {{
        if (millis() - lastDebounceTime > debounceDelay) {{
            modeContext.switchMode(); // Переключаем режим
            lastDebounceTime = millis();
        }}
    }}
    
    modeContext.executeCurrentMode(); // Выполняем текущую стратегию
    delay(200); // Задержка предотвращает дребезг
    }}
    
    """
        with open("kurs.ino", "w", encoding="utf-8") as f:
            f.write(template)
        return 1
    except Exception as e:
        return e


def generate_standard_button_action(n, button):
    """Генерирует действие для кнопки в зависимости от её типа."""
    ret = f"if (button{n}State) {{\n"
    if button["type"] == "Print Text":
        action_text = button["action"].replace('"', '\\"')
        return ret + f'Keyboard.print("{action_text}");' + "\n}"
    elif button["type"] == "Key Combination":
        res = ""
        keys = button["action"].split("+")
        for key in keys:
            arduino_key = KEY_MAP.get(key.upper(), key.upper())
            if not arduino_key:
                continue
            res += f'Keyboard.press(KEY_{arduino_key});\n'
        res += "Keyboard.releaseAll();"
        return ret + res + "\n}"
    return ""
