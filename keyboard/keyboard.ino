
    #include <HID-Project.h>   // Для реализации HID-функций
    
    // Пины для кнопок, переключателя и потенциометра
    const int button1Pin = 2; // Программируемая кнопка 1
    const int button2Pin = 3; // Программируемая кнопка 2
    const int switchPin = 4;  // Кнопка для переключения режимов
    const int potPin = A0;    // Пин потенциометра
    
    // Базовый интерфейс для стратегии
    class ModeStrategy {
    public:
        virtual void execute(bool button1State, bool button2State) = 0;
        virtual ~ModeStrategy() = default;
    };
    
    
    class 123a : public ModeStrategy {
    public:
        void execute(bool button1State, bool button2State) {
            if (button1State) {
                Keyboard.print("фва");
            }
            if (button2State) {
                Keyboard.print("");
            }
        }
    };
    
    
    class ModeContext {
        ModeStrategy* strategies[1]; // Список стратегий
        int currentMode = 0;
    
    public:
        ModeContext() {
            strategies[0] = new 123a();
        }
    
        ~ModeContext() {
            for (auto strategy : strategies) {
                delete strategy;
            }
        }
    
        void switchMode() {
            currentMode = (currentMode + 1) % 1; // Циклический переход по режимам
        }
    
        void executeCurrentMode(bool button1State, bool button2State) {
            strategies[currentMode]->execute(button1State, button2State);
        }
    };
    
    // Переменные для управления
    int lastPotValue = 0;       // Предыдущее значение потенциометра
    int debounceDelay = 50;     // Задержка для антидребезга
    unsigned long lastDebounceTime = 0;
    
    // Создаем контекст
    ModeContext modeContext;
    
    void setup() {
        // Инициализация пинов
        pinMode(button1Pin, INPUT_PULLUP);
        pinMode(button2Pin, INPUT_PULLUP);
        pinMode(switchPin, INPUT_PULLUP);
    
        // Инициализация HID
        Keyboard.begin();
        Consumer.begin();
    }
    
    // Переключение режимов
    void handleModeSwitch() {
        static bool lastSwitchState = HIGH;
        bool switchState = digitalRead(switchPin);
    
        if (switchState != lastSwitchState) {
            if (millis() - lastDebounceTime > debounceDelay) {
                modeContext.switchMode(); // Переключаем режим
                lastDebounceTime = millis();
            }
        }
        lastSwitchState = switchState;
    }
    
    // Управление громкостью через потенциометр
    void handleVolumeControl() {
        int potValue = analogRead(potPin);
    
        if (abs(potValue - lastPotValue) > 10) { // Проверка изменения
            int volumeChange = map(potValue, 0, 1023, -10, 10);
            if (volumeChange > 0) {
                for (int i = 0; i < volumeChange; i++) {
                    Consumer.write(MEDIA_VOLUME_UP);
                }
            } else {
                for (int i = 0; i < abs(volumeChange); i++) {
                    Consumer.write(MEDIA_VOLUME_DOWN);
                }
            }
            lastPotValue = potValue;
            delay(50);
        }
    }
    
    // Обработка кнопок
    void handleButtonActions() {
        static bool lastButton1State = HIGH;
        static bool lastButton2State = HIGH;
    
        bool button1State = digitalRead(button1Pin) == LOW && lastButton1State == HIGH;
        bool button2State = digitalRead(button2Pin) == LOW && lastButton2State == HIGH;
    
        modeContext.executeCurrentMode(button1State, button2State); // Выполняем текущую стратегию
        delay(200); // Задержка предотвращает дребезг
    
        lastButton1State = digitalRead(button1Pin);
        lastButton2State = digitalRead(button2Pin);
    }
    
    void loop() {
        handleModeSwitch();
        handleVolumeControl();
        handleButtonActions();
    }
    
    