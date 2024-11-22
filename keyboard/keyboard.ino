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

// Реализация стратегии для режима 1
class Mode1 : public ModeStrategy {
public:
    void execute(bool button1State, bool button2State) override {
        if (button1State) {
            Keyboard.print("Mode 1 Action!");
        }
        if (button2State) {
            Keyboard.press(KEY_LEFT_ALT);
            Keyboard.press('c'); // Пример действия для режима 2 (Ctrl+C)
            delay(100);
            Keyboard.releaseAll();
        }
    }
};

// Реализация стратегии для режима 2
class Mode2 : public ModeStrategy {
public:
    void execute(bool button1State, bool button2State) override {
        if (button1State || button2State) {
            Keyboard.press(KEY_LEFT_CTRL);
            Keyboard.press('c'); // Ctrl+C
            delay(100);
            Keyboard.releaseAll();
        }
    }
};

// Реализация стратегии для режима 3
class Mode3 : public ModeStrategy {
public:
    void execute(bool button1State, bool button2State) override {
        if (button1State || button2State) {
            Keyboard.press(KEY_LEFT_CTRL);
            Keyboard.press(KEY_LEFT_SHIFT);
            Keyboard.press(KEY_ESC); // Ctrl+Shift+Esc
            delay(100);
            Keyboard.releaseAll();
        }
    }
};

// Контекст для управления стратегиями
class ModeContext {
    ModeStrategy* strategies[3]; // Список стратегий
    int currentMode = 0;

public:
    ModeContext() {
        strategies[0] = new Mode1();
        strategies[1] = new Mode2();
        strategies[2] = new Mode3();
    }

    ~ModeContext() {
        for (auto strategy : strategies) {
            delete strategy;
        }
    }

    void switchMode() {
        currentMode = (currentMode + 1) % 3; // Циклический переход по режимам
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
