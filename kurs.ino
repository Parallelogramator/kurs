
    #include <HID-Project.h>   // Для реализации HID-функций
    
    // Пины для кнопок, переключателя и потенциометра
    const int button1Pin = 2;
const int button2Pin = 3;
const int button3Pin = 4;
const int button4Pin = 5;
    const int switchPin = 4;  // Кнопка для переключения режимов
    const int pot0Pin = A0;
    
    void handleVolumeControl(int pin) {
    static int lastPotValue = 0; // Предыдущее значение потенциометра
    int potValue = analogRead(pin);

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
    
    // Базовый интерфейс для стратегии
    class ModeStrategy {
    public:
        virtual void execute() = 0;
        virtual ~ModeStrategy() = default;
    };
    
    
    class mode1 : public ModeStrategy {
    public:
        void execute() override{
            bool button1State,button2State,button3State,button4State;
            checkButtonStates(button1State,button2State,button3State,button4State);
            if (button1State) {
Keyboard.press(KEY_LEFT_CTRL);
Keyboard.press(KEY_C);
Keyboard.releaseAll();
}
if (button2State) {
Keyboard.print("asd");
}
if (button3State) {
Keyboard.print("qwe");
}
if (button4State) {
Keyboard.print("wqe");
};
            
            handleVolumeControl(A1);
        }
    };
    

    class asdasd : public ModeStrategy {
    public:
        void execute() override{
            bool button1State,button2State,button3State,button4State;
            checkButtonStates(button1State,button2State,button3State,button4State);
            if (button1State) {
Keyboard.print("qe");
}
if (button2State) {
Keyboard.print("q");
}
if (button3State) {
Keyboard.print("qq");
}
if (button4State) {
Keyboard.press(KEY_LEFT_CTRL);
Keyboard.press(KEY_D);
Keyboard.press(KEY_S);
Keyboard.releaseAll();
};
            
            handleVolumeControl(A0);
handleVolumeControl(A1);
        }
    };
    

    class sd4 : public ModeStrategy {
    public:
        void execute() override{
            bool button1State,button2State,button3State,button4State;
            checkButtonStates(button1State,button2State,button3State,button4State);
            if (button1State) {
Keyboard.releaseAll();
}
if (button2State) {
Keyboard.releaseAll();
}
if (button3State) {
Keyboard.print("");
}
if (button4State) {
Keyboard.print("pr");
};
            
            handleVolumeControl(A0);
        }
    };
    
    
    class ModeContext {
        ModeStrategy* strategies[3]; // Список стратегий
        int currentMode = 0;
    
    public:
        ModeContext() {
            strategies[0] = new mode1();
strategies[1] = new asdasd();
strategies[2] = new sd4();
        }
    
        ~ModeContext() {
            for (auto strategy : strategies) {
                delete strategy;
            }
        }
    
        void switchMode() {
            currentMode = (currentMode + 1) % 3; // Циклический переход по режимам
        }
    
        void executeCurrentMode() {
            strategies[currentMode]->execute();
        }
    };
    
    // Переменные для управления
    int lastPotValue = 0;       // Предыдущее значение потенциометра
    int debounceDelay = 500;     // Задержка для антидребезга
    unsigned long lastDebounceTime = 0;
    
    // Создаем контекст
    ModeContext modeContext;
    
    void setup() {
        // Инициализация пинов
        pinMode(button1Pin, INPUT_PULLUP);
pinMode(button2Pin, INPUT_PULLUP);
pinMode(button3Pin, INPUT_PULLUP);
pinMode(button4Pin, INPUT_PULLUP);
        pinMode(switchPin, INPUT_PULLUP);
    
        // Инициализация HID
        Keyboard.begin();
        Consumer.begin();
    }
    
    
    // Обработка кнопок
    void checkButtonStates(bool &button1State,bool &button2State,bool &button3State,bool &button4State) {
    button1State = digitalRead(button1Pin) == HIGH;
button2State = digitalRead(button2Pin) == HIGH;
button3State = digitalRead(button3Pin) == HIGH;
button4State = digitalRead(button4Pin) == HIGH;
    }  
    
    void loop() {
    bool switchState = digitalRead(switchPin);

    if (switchState) {
        if (millis() - lastDebounceTime > debounceDelay) {
            modeContext.switchMode(); // Переключаем режим
            lastDebounceTime = millis();
        }
    }
    
    modeContext.executeCurrentMode(); // Выполняем текущую стратегию
    delay(200); // Задержка предотвращает дребезг
    }
    
    