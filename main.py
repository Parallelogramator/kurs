import sys
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QGridLayout, QMessageBox, QStackedWidget
)
from PyQt5.QtCore import Qt

from generate import generate_ino_file
from upload import upload_ino_file


class KeyCaptureLineEdit(QLineEdit):
    def __init__(self):
        super().__init__()
        self.captured_keys = set()
        self.recording = False

    def focusInEvent(self, event):
        """Начать запись при фокусе на поле ввода."""
        super().focusInEvent(event)
        self.recording = True
        self.captured_keys.clear()
        self.setText("")

    def focusOutEvent(self, event):
        """Остановить запись при потере фокуса."""
        super().focusOutEvent(event)
        self.recording = False

    def keyPressEvent(self, event):
        """Обрабатывать нажатие клавиш."""
        if self.recording:
            key = event.key()
            modifiers = QApplication.keyboardModifiers()
            keys = []

            if modifiers & Qt.ControlModifier:
                keys.append("Ctrl")
            if modifiers & Qt.ShiftModifier:
                keys.append("Shift")
            if modifiers & Qt.AltModifier:
                keys.append("Alt")

            # Добавляем основную клавишу
            if key >= Qt.Key_A and key <= Qt.Key_Z:
                keys.append(chr(key))
            elif key == Qt.Key_Space:
                keys.append("Space")
            elif key == Qt.Key_Backspace:
                keys.append("Backspace")
            elif key == Qt.Key_Delete:
                keys.append("Delete")
            elif key == Qt.Key_Enter or key == Qt.Key_Return:
                keys.append("Enter")
            elif key == Qt.Key_Tab:
                keys.append("Tab")
            elif key == Qt.Key_Escape:
                keys.append("Escape")
            elif key >= Qt.Key_0 and key <= Qt.Key_9:
                keys.append(chr(key))

            # Обновляем текстовое поле с комбинацией
            self.captured_keys.update(keys)
            self.setText("+".join(sorted(self.captured_keys)))
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Обрабатывать отпускание клавиш."""
        if not self.recording:
            super().keyReleaseEvent(event)


class ArduinoCodeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Arduino Code Generator")
        self.setGeometry(100, 100, 1400, 1000)  # Увеличение размеров окна

        # Данные для режимов
        self.modes = {
            "Mode 1": {"button1": {"type": "Print Text", "action": ""}, "button2": {"type": "Print Text", "action": ""}},
            "Mode 2": {"button1": {"type": "Print Text", "action": ""}, "button2": {"type": "Print Text", "action": ""}},
            "Mode 3": {"button1": {"type": "Print Text", "action": ""}, "button2": {"type": "Print Text", "action": ""}},
        }

        # Создание интерфейса
        self.setup_ui()
        self.update_mode()

    def setup_ui(self):
        """Создаёт интерфейс окна."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout()
        central_widget.setLayout(layout)

        # Элементы интерфейса
        self.mode_selector = QComboBox()
        self.mode_selector.addItems(["Mode 1", "Mode 2", "Mode 3"])
        self.mode_selector.currentIndexChanged.connect(self.update_mode)
        layout.addWidget(QLabel("Select Mode:"))
        layout.addWidget(self.mode_selector)

        self.grid_layout = QGridLayout()
        layout.addLayout(self.grid_layout)

        # Поля для настройки кнопок
        self.create_button_ui("Button 1", 0)
        self.create_button_ui("Button 2", 2)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_mode_data)
        layout.addWidget(self.save_button)

        self.generate_button = QPushButton("Generate .ino File")
        self.generate_button.clicked.connect(self.on_generate_code_clicked)
        layout.addWidget(self.generate_button)

        self.upload_button = QPushButton("upload .ino File")
        self.upload_button.clicked.connect(self.on_upload_code_clicked)
        layout.addWidget(self.upload_button)

    def create_button_ui(self, label, row):
        """Создаёт интерфейс для настройки одной кнопки."""
        action_type = QComboBox()
        action_type.addItems(["Print Text", "Key Combination"])
        action_type.currentIndexChanged.connect(self.update_input_type)

        stacked_input = QStackedWidget()
        input_field = QLineEdit()
        key_input_field = KeyCaptureLineEdit()
        stacked_input.addWidget(input_field)
        stacked_input.addWidget(key_input_field)

        clear_button = QPushButton("Clear")
        clear_button.clicked.connect(lambda: self.clear_field(stacked_input))

        self.grid_layout.addWidget(QLabel(f"{label} Action Type:"), row, 0)
        self.grid_layout.addWidget(action_type, row, 1)
        self.grid_layout.addWidget(stacked_input, row + 1, 1)
        self.grid_layout.addWidget(clear_button, row + 1, 2)

        # Упрощённое именование
        setattr(self, f"{label.replace(' ', '').lower()}_action_type", action_type)
        setattr(self, f"{label.replace(' ', '').lower()}_stacked_input", stacked_input)

    def update_input_type(self):
        """Обновляет видимость полей ввода в зависимости от типа действия."""
        for label in ["button1", "button2"]:
            action_type = getattr(self, f"{label}_action_type").currentText()
            stacked_input = getattr(self, f"{label}_stacked_input")
            if action_type == "Print Text":
                stacked_input.setCurrentIndex(0)
            else:
                stacked_input.setCurrentIndex(1)

    def clear_field(self, stacked_input):
        """Очищает поля ввода."""
        for i in range(stacked_input.count()):
            stacked_input.widget(i).clear()

    def update_mode(self):
        """Обновляет поля ввода в соответствии с текущим режимом."""
        mode = self.mode_selector.currentText()
        button1_data = self.modes[mode]["button1"]
        button2_data = self.modes[mode]["button2"]

        self.button1_action_type.setCurrentText(button1_data["type"])
        getattr(self.button1_stacked_input.widget(0), "setText")(button1_data["action"])
        getattr(self.button1_stacked_input.widget(1), "setText")(button1_data["action"])

        self.button2_action_type.setCurrentText(button2_data["type"])
        getattr(self.button2_stacked_input.widget(0), "setText")(button2_data["action"])
        getattr(self.button2_stacked_input.widget(1), "setText")(button2_data["action"])

        self.update_input_type()

    def save_mode_data(self):
        """Сохраняет введенные данные в словарь."""
        mode = self.mode_selector.currentText()
        self.modes[mode]["button1"]["type"] = self.button1_action_type.currentText()
        self.modes[mode]["button1"]["action"] = self.button1_stacked_input.currentWidget().text()

        self.modes[mode]["button2"]["type"] = self.button2_action_type.currentText()
        self.modes[mode]["button2"]["action"] = self.button2_stacked_input.currentWidget().text()

    def on_generate_code_clicked(self):
        """Генерация файла .ino при нажатии кнопки."""
        self.save_mode_data()
        check = generate_ino_file(self.modes)

        if check:
            QMessageBox.information(self, "Success", "File generated successfully.")
        else:
            QMessageBox.warning(self, "Error", "Error generating file.")

    def on_upload_code_clicked(self):
        """Генерация файла .ino при нажатии кнопки."""
        self.save_mode_data()
        check = upload_ino_file("kurs.ino")

        if check:
            QMessageBox.information(self, "Success", "File generated successfully.")
        else:
            QMessageBox.warning(self, "Error", "Error generating file.")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoCodeGenerator()
    window.show()
    sys.exit(app.exec_())
