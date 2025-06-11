#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <HID-Project.h>
#include <Encoder.h>

// --- OLED DISPLAY SETTINGS ---
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

// --- PIN DEFINITIONS ---
const int ENCODER_S1_PIN = 5;
const int ENCODER_S2_PIN = 6;
const int ENCODER_KEY_PIN = 4;

const int button1Pin = 7;
const int button2Pin = 8;
const int button3Pin = 9;
const int button4Pin = 10;


// --- ENCODER OBJECT ---
Encoder myEnc(ENCODER_S1_PIN, ENCODER_S2_PIN);

// --- BASE STRATEGY INTERFACE ---
class ModeStrategy {
public:
    virtual const char* getModeName() const = 0;
    virtual void execute(bool button1State, bool button2State, bool button3State, bool button4State) = 0;
    virtual ~ModeStrategy() = default;
};

// --- MODE STRATEGY CLASSES ---
class Mode_Mode_1 : public ModeStrategy {
public:
    const char* getModeName() const override { return "Mode 1"; }
    void execute(bool button1State, bool button2State, bool button3State, bool button4State) override {
        if (button1State) {
            Keyboard.press(KEY_LEFT_CTRL);
            Keyboard.press('c');
            delay(50);
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
        }
    }
};

class Mode_asdasd : public ModeStrategy {
public:
    const char* getModeName() const override { return "asdasd"; }
    void execute(bool button1State, bool button2State, bool button3State, bool button4State) override {
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
            Keyboard.press(KEY_LEFT_ALT);
            delay(50);
            Keyboard.releaseAll();
        }
    }
};

class Mode_sd4 : public ModeStrategy {
public:
    const char* getModeName() const override { return "sd4"; }
    void execute(bool button1State, bool button2State, bool button3State, bool button4State) override {
        if (button1State) {
        // No action defined
        }
        if (button2State) {
        // No action defined
        }
        if (button3State) {
            // No text to print
        }
        if (button4State) {
            Keyboard.print("pr");
        }
    }
};


// --- MODE CONTEXT ---
class ModeContext {
    ModeStrategy* strategies[3];
    int currentMode = 0;
public:
    ModeContext() {
        strategies[0] = new Mode_Mode_1();
        strategies[1] = new Mode_asdasd();
        strategies[2] = new Mode_sd4();
    }
    ~ModeContext() {
        for (int i = 0; i < 3; ++i) { delete strategies[i]; }
    }
    void switchMode() {
        currentMode = (currentMode + 1) % 3;
    }
    void executeCurrentMode(bool button1State, bool button2State, bool button3State, bool button4State) {
        strategies[currentMode]->execute(button1State, button2State, button3State, button4State);
    }
    const char* getCurrentModeName() const {
        return strategies[currentMode]->getModeName();
    }
};


// --- GLOBAL VARIABLES ---
ModeContext modeContext;
unsigned long lastDebounceTime = 0;
const int debounceDelay = 250;
long oldEncoderPosition = -999;

// --- HELPER FUNCTIONS ---
void setupDisplay() {
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { 
        for(;;); // Loop forever if display fails
    }
    display.clearDisplay();
    display.setTextSize(2);
    display.setTextColor(SSD1306_WHITE);
    display.display();
}

void updateDisplay(const char* modeName) {
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println(modeName);
    display.display();
}

void handleEncoderRotation() {
    long newEncoderPosition = myEnc.read() / 4;
    if (newEncoderPosition != oldEncoderPosition) {
        if (newEncoderPosition > oldEncoderPosition) {
            Consumer.write(MEDIA_VOLUME_UP);
        } else {
            Consumer.write(MEDIA_VOLUME_DOWN);
        }
        oldEncoderPosition = newEncoderPosition;
    }
}

void handleEncoderButton() {
    if (digitalRead(ENCODER_KEY_PIN) == LOW) {
        if ((millis() - lastDebounceTime) > debounceDelay) {
            modeContext.switchMode();
            updateDisplay(modeContext.getCurrentModeName());
            lastDebounceTime = millis();
        }
    }
}

void setup() {
    pinMode(ENCODER_KEY_PIN, INPUT_PULLUP);
    pinMode(button1Pin, INPUT_PULLUP);
    pinMode(button2Pin, INPUT_PULLUP);
    pinMode(button3Pin, INPUT_PULLUP);
    pinMode(button4Pin, INPUT_PULLUP);

    Keyboard.begin();
    Consumer.begin();
    setupDisplay();
    updateDisplay(modeContext.getCurrentModeName());
}

void loop() {
    // 1. Handle encoder rotation (Volume) and button press (Switch Mode)
    handleEncoderRotation();
    handleEncoderButton();

    // 2. Read states of additional standard buttons
    bool button1State = (digitalRead(button1Pin) == LOW);
    bool button2State = (digitalRead(button2Pin) == LOW);
    bool button3State = (digitalRead(button3Pin) == LOW);
    bool button4State = (digitalRead(button4Pin) == LOW);

    // 3. Execute actions for the current mode based on standard buttons
    modeContext.executeCurrentMode(button1State, button2State, button3State, button4State);

    delay(10); // Small delay for stability
}