import re

# Словарь для сопоставления строковых названий клавиш с константами из HID-Project.h
KEY_MAP = {
    'ctrl': 'KEY_LEFT_CTRL', 'shift': 'KEY_LEFT_SHIFT', 'alt': 'KEY_LEFT_ALT',
    'win': 'KEY_LEFT_GUI', 'esc': 'KEY_ESC', 'enter': 'KEY_ENTER',
    'tab': 'KEY_TAB', 'backspace': 'KEY_BACKSPACE', 'delete': 'KEY_DELETE',
    'insert': 'KEY_INSERT', 'up': 'KEY_UP_ARROW', 'down': 'KEY_DOWN_ARROW',
    'left': 'KEY_LEFT_ARROW', 'right': 'KEY_RIGHT_ARROW',
    'f1': 'KEY_F1', 'f2': 'KEY_F2', 'f3': 'KEY_F3', 'f4': 'KEY_F4',
    'f5': 'KEY_F5', 'f6': 'KEY_F6', 'f7': 'KEY_F7', 'f8': 'KEY_F8',
    'f9': 'KEY_F9', 'f10': 'KEY_F10', 'f11': 'KEY_F11', 'f12': 'KEY_F12',
}


def parse_and_press_keys(action_string):
    """Генерирует C++ код для нажатия комбинации клавиш."""
    if not action_string.strip():
        return "        // No action defined\n"

    parts = [p.strip().lower() for p in action_string.split('+')]
    press_calls = []

    for part in parts:
        if part in KEY_MAP:
            press_calls.append(f"            Keyboard.press({KEY_MAP[part]});")
        elif len(part) == 1:
            press_calls.append(f"            Keyboard.press('{part}');")
        else:
            press_calls.append(f"            // Unknown key: {part}")

    if not press_calls:
        return ""

    code = "\n".join(press_calls)
    code += "\n            delay(50);\n"
    code += "            Keyboard.releaseAll();\n"
    return code


def generate_ino_file(modes, num_standard_buttons, num_drop_buttons):
    """
    Главная функция, генерирующая .ino код для устройства
    с энкодером и дополнительными кнопками.
    """

    pin_definitions = "\n"
    pin_definitions += "const int ENCODER_S1_PIN = 5;\n"
    pin_definitions += "const int ENCODER_S2_PIN = 6;\n"
    pin_definitions += "const int ENCODER_KEY_PIN = 4;\n\n"

    standard_button_pins = list(range(7, 7 + num_standard_buttons))
    for i in range(num_standard_buttons):
        pin_definitions += f"const int button{i + 1}Pin = {standard_button_pins[i]};\n"

    strategy_classes = "\n"
    mode_names = list(modes.keys())
    button_state_params = ", ".join(
        [f"bool button{i + 1}State" for i in range(num_standard_buttons)]) if num_standard_buttons > 0 else ""

    for mode_name in mode_names:
        class_name = "Mode_" + re.sub(r'\W+', '_', mode_name)
        mode_data = modes[mode_name]

        strategy_classes += f"class {class_name} : public ModeStrategy {{\n"
        strategy_classes += "public:\n"
        strategy_classes += f'    const char* getModeName() const override {{ return "{mode_name}"; }}\n'
        strategy_classes += f"    void execute({button_state_params}) override {{\n"

        for i in range(num_standard_buttons):
            btn_key = f"button{i + 1}"
            if btn_key in mode_data.get('standard_buttons', {}):
                button_data = mode_data['standard_buttons'][btn_key]
                strategy_classes += f"        if (button{i + 1}State) {{\n"
                if button_data['type'] == 'Key Combination':
                    strategy_classes += parse_and_press_keys(button_data['action'])
                elif button_data['type'] == 'Print Text':
                    action_text = button_data['action'].replace('\\', '\\\\').replace('"', '\\"')
                    if action_text:
                        strategy_classes += f'            Keyboard.print("{action_text}");\n'
                    else:
                        strategy_classes += '            // No text to print\n'
                strategy_classes += "        }\n"

        strategy_classes += "    }\n};\n\n"

    # --- 3. Генерация ModeContext ---
    context_class = "\n"
    context_class += "class ModeContext {\n"
    context_class += f"    ModeStrategy* strategies[{len(mode_names)}];\n"
    context_class += "    int currentMode = 0;\n"
    context_class += "public:\n"
    context_class += "    ModeContext() {\n"
    for i, mode_name in enumerate(mode_names):
        class_name = "Mode_" + re.sub(r'\W+', '_', mode_name)
        context_class += f"        strategies[{i}] = new {class_name}();\n"
    context_class += "    }\n"
    context_class += "    ~ModeContext() {\n"
    context_class += f"        for (int i = 0; i < {len(mode_names)}; ++i) {{ delete strategies[i]; }}\n"
    context_class += "    }\n"
    context_class += "    void switchMode() {\n"
    context_class += f"        currentMode = (currentMode + 1) % {len(mode_names)};\n"
    context_class += "    }\n"

    execute_params = ', '.join([f'button{i + 1}State' for i in range(num_standard_buttons)])
    context_class += f"    void executeCurrentMode({button_state_params}) {{\n"
    context_class += f"        strategies[currentMode]->execute({execute_params});\n"
    context_class += "    }\n"
    context_class += "    const char* getCurrentModeName() const {\n"
    context_class += "        return strategies[currentMode]->getModeName();\n"
    context_class += "    }\n"
    context_class += "};\n"

    # --- 4. Генерация кода для setup() и loop() ---
    pin_setup_code = "\n    ".join([f"pinMode(button{i + 1}Pin, INPUT_PULLUP);" for i in range(num_standard_buttons)])
    button_read_code = "\n    ".join(
        [f"bool button{i + 1}State = (digitalRead(button{i + 1}Pin) == LOW);" for i in range(num_standard_buttons)])

    # --- 5. Собираем финальный .ino файл ---
    ino_template = f"""
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <HID-Project.h>
#include <Encoder.h>

#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 32
#define OLED_RESET -1
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, OLED_RESET);

{pin_definitions}

Encoder myEnc(ENCODER_S1_PIN, ENCODER_S2_PIN);

class ModeStrategy {{
public:
    virtual const char* getModeName() const = 0;
    virtual void execute({button_state_params}) = 0;
    virtual ~ModeStrategy() = default;
}};

{strategy_classes}
{context_class}

ModeContext modeContext;
unsigned long lastDebounceTime = 0;
const int debounceDelay = 250;
long oldEncoderPosition = -999;

void setupDisplay() {{
    if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) {{ 
        for(;;); 
    }}
    display.clearDisplay();
    display.setTextSize(2);
    display.setTextColor(SSD1306_WHITE);
    display.display();
}}

void updateDisplay(const char* modeName) {{
    display.clearDisplay();
    display.setCursor(0, 0);
    display.println(modeName);
    display.display();
}}

void handleEncoderRotation() {{
    long newEncoderPosition = myEnc.read() / 4;
    if (newEncoderPosition != oldEncoderPosition) {{
        if (newEncoderPosition > oldEncoderPosition) {{
            Consumer.write(MEDIA_VOLUME_UP);
        }} else {{
            Consumer.write(MEDIA_VOLUME_DOWN);
        }}
        oldEncoderPosition = newEncoderPosition;
    }}
}}

void handleEncoderButton() {{
    if (digitalRead(ENCODER_KEY_PIN) == LOW) {{
        if ((millis() - lastDebounceTime) > debounceDelay) {{
            modeContext.switchMode();
            updateDisplay(modeContext.getCurrentModeName());
            lastDebounceTime = millis();
        }}
    }}
}}

void setup() {{
    pinMode(ENCODER_KEY_PIN, INPUT_PULLUP);
    {pin_setup_code}

    Keyboard.begin();
    Consumer.begin();
    setupDisplay();
    updateDisplay(modeContext.getCurrentModeName());
}}

void loop() {{
    handleEncoderRotation();
    handleEncoderButton();

    {button_read_code}

    modeContext.executeCurrentMode({execute_params});

    delay(10); // Small delay for stability
}}
"""
    output_filename = "kurs.ino"
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(ino_template.strip())
    return 1


if __name__ == "__main__":
    config = {
        'modes': {
            'Mode 1': {
                'standard_buttons': {
                    'button1': {'type': 'Key Combination', 'action': 'Ctrl+C'},
                    'button2': {'type': 'Print Text', 'action': 'Hello World!'},
                    'button3': {'type': 'Print Text', 'action': 'Button 3'},
                    'button4': {'type': 'Print Text', 'action': 'Button 4'}
                },
                'dropdown_buttons': {
                    'dropdown_button1': 'Nothing'
                }
            },
            'SoundPad': {
                'standard_buttons': {
                    'button1': {'type': 'Print Text', 'action': 'Playing sound 1...'},
                    'button2': {'type': 'Print Text', 'action': 'Playing sound 2...'},
                    'button3': {'type': 'Key Combination', 'action': 'Alt+F4'},
                    'button4': {'type': 'Key Combination', 'action': ''}
                },
                'dropdown_buttons': {
                    'dropdown_button1': 'Volume'
                }
            },
            'Shortcuts': {
                'standard_buttons': {
                    'button1': {'type': 'Key Combination', 'action': 'Win+Tab'},
                    'button2': {'type': 'Key Combination', 'action': 'Ctrl+Shift+Esc'},
                    'button3': {'type': 'Print Text', 'action': ''},
                    'button4': {'type': 'Print Text', 'action': 'Opening task manager!'}
                },
                'dropdown_buttons': {
                    'dropdown_button1': 'Volume'
                }
            }
        },
        'standard_buttons': 4,
        'dropdown_buttons': 1
    }

    # Генерируем код
    generated_code = generate_ino_file(
        config['modes'],
        config['standard_buttons'],
        config['dropdown_buttons']
    )



    print(f"Arduino sketch successfully generated and saved to '{1}'")
    # print("\n--- Generated Code ---\n")
    # print(generated_code)