import json
import sys

from PyQt5.QtGui import QRegularExpressionValidator
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QLabel,
    QLineEdit, QPushButton, QComboBox, QGridLayout, QMessageBox, QStackedWidget, QHBoxLayout, QInputDialog
)
from PyQt5.QtCore import Qt, QRegularExpression
import qdarkstyle

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

            if Qt.Key_A <= key <= Qt.Key_Z:
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
            elif Qt.Key_0 <= key <= Qt.Key_9:
                keys.append(chr(key))
            self.captured_keys.update(keys)

            def sort_key(item):
                if item in ["Ctrl", "Shift", "Alt", "Space", "Backspace", "Delete", "Enter", "Tab", "Escape"]:
                    return (0, item)
                else:
                    return (1, item)

            self.setText("+".join(sorted(self.captured_keys, key=sort_key)))
        else:
            super().keyPressEvent(event)

    def keyReleaseEvent(self, event):
        """Обрабатывать отпускание клавиш."""
        if not self.recording:
            super().keyReleaseEvent(event)


class ArduinoCodeGenerator(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.setWindowTitle("Arduino Code Generator")
        self.setGeometry(100, 100, 1000, 700)

        self.num_standard_buttons = 4
        self.num_dropdown_buttons = 1

        self.modes = {}

        self.setup_ui()

    def setup_ui(self):
        """Создание интерфейса."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Селектор режимов
        self.mode_selector = QComboBox()
        self.mode_selector.currentIndexChanged.connect(self.update_mode)
        main_layout.addWidget(QLabel("Select Mode:"))
        main_layout.addWidget(self.mode_selector)

        # Кнопки управления режимами
        mode_control_layout = QHBoxLayout()
        add_mode_button = QPushButton("Add Mode")
        add_mode_button.clicked.connect(self.add_mode)
        remove_mode_button = QPushButton("Remove Mode")
        remove_mode_button.clicked.connect(self.remove_mode)
        rename_mode_button = QPushButton("Rename Mode")
        rename_mode_button.clicked.connect(self.rename_mode)
        mode_control_layout.addWidget(add_mode_button)
        mode_control_layout.addWidget(remove_mode_button)
        mode_control_layout.addWidget(rename_mode_button)
        main_layout.addLayout(mode_control_layout)

        self.standard_buttons_layout = QGridLayout()
        main_layout.addWidget(QLabel("Standard Buttons:"))
        main_layout.addLayout(self.standard_buttons_layout)

        for i in range(self.num_standard_buttons):
            self.create_standard_button_ui(f"Button {i + 1}", i)

        self.dropdown_buttons_layout = QGridLayout()
        main_layout.addWidget(QLabel("Dropdown Buttons:"))
        main_layout.addLayout(self.dropdown_buttons_layout)

        for i in range(self.num_dropdown_buttons):
            self.create_dropdown_button_ui(f"Dropdown Button {i + 1}", i)

        self.save_button = QPushButton("Save Changes")
        self.save_button.clicked.connect(self.save_mode_data)
        main_layout.addWidget(self.save_button)

        self.generate_button = QPushButton("Upload .ino File")
        self.generate_button.clicked.connect(self.on_upload_code_clicked)
        main_layout.addWidget(self.generate_button)

        try:
            with open("modes.json", "r+") as f:
                try:
                    self.modes = json.load(f)
                    self.update_mode_selector()
                except json.JSONDecodeError:
                    self.modes = {}
                    self.add_mode()
        except FileNotFoundError:
            self.modes = {}
            self.add_mode()

    def update_mode_selector(self):
        """Обновляет QComboBox mode_selector на основе данных self.modes."""
        self.mode_selector.clear()
        for mode_name in self.modes.keys():
            self.mode_selector.addItem(mode_name)
        if self.mode_selector.count() > 0:
            self.mode_selector.setCurrentIndex(0)
            self.update_mode()

    def create_standard_button_ui(self, label, index):
        """Создаёт интерфейс для настройки кнопок."""
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

        self.standard_buttons_layout.addWidget(QLabel(f"{label} Action Type:"), index, 0)
        self.standard_buttons_layout.addWidget(action_type, index, 1)
        self.standard_buttons_layout.addWidget(stacked_input, index, 2)
        self.standard_buttons_layout.addWidget(clear_button, index, 3)

        setattr(self, f"standard_button{index + 1}_action_type", action_type)
        setattr(self, f"standard_button{index + 1}_stacked_input", stacked_input)

    def create_dropdown_button_ui(self, label, index):
        """Создаёт интерфейс для кнопок с выпадающими списками."""
        dropdown_selector = QComboBox()
        dropdown_selector.addItems(["Nothing", "Volume"])

        self.dropdown_buttons_layout.addWidget(QLabel(f"{label}:"), index, 0)
        self.dropdown_buttons_layout.addWidget(dropdown_selector, index, 1)

        setattr(self, f"dropdown_button{index + 1}_selector", dropdown_selector)

    def add_mode(self):
        """Добавление нового режима."""
        new_mode_name = f"Mode {len(self.modes) + 1}"
        self.modes[new_mode_name] = {
            "standard_buttons": {
                f"button{i + 1}": {"type": "Print Text", "action": ""} for i in range(self.num_standard_buttons)
            },
            "dropdown_buttons": {
                f"dropdown_button{i + 1}": "Nothing" for i in range(self.num_dropdown_buttons)
            }
        }
        self.mode_selector.addItem(new_mode_name)
        self.mode_selector.setCurrentIndex(self.mode_selector.count() - 1)

    def remove_mode(self):
        """Удаление текущего режима."""
        current_mode = self.mode_selector.currentText()
        if current_mode and len(self.modes) > 1:
            del self.modes[current_mode]
            self.mode_selector.removeItem(self.mode_selector.currentIndex())

    def rename_mode(self):
        """Переименовывает текущий режим с ограничением на ввод."""
        current_mode = self.mode_selector.currentText()
        if current_mode:
            regex = QRegularExpression("^[a-zA-Z][a-zA-Z0-9]*$")
            validator = QRegularExpressionValidator(regex)

            input_dialog = QInputDialog(self)
            input_dialog.setInputMode(QInputDialog.TextInput)
            input_dialog.setWindowTitle("Rename Mode")
            input_dialog.setLabelText("Enter new name for the mode (must start with a letter):")
            line_edit = input_dialog.findChild(QLineEdit)
            line_edit.setValidator(validator)

            if input_dialog.exec_() == QInputDialog.Accepted:
                new_name = input_dialog.textValue().strip()
                if new_name and new_name not in self.modes:
                    self.modes[new_name] = self.modes.pop(current_mode)
                    index = self.mode_selector.currentIndex()
                    self.mode_selector.setItemText(index, new_name)
                else:
                    QMessageBox.warning(self, "Error", "Name is invalid or already exists.")

    def update_mode(self):
        """Обновляет интерфейс для текущего режима."""
        current_mode = self.mode_selector.currentText()
        if current_mode in self.modes:
            mode_data = self.modes[current_mode]
            for i in range(self.num_standard_buttons):
                button_data = mode_data["standard_buttons"][f"button{i + 1}"]
                action_type = getattr(self, f"standard_button{i + 1}_action_type")
                stacked_input = getattr(self, f"standard_button{i + 1}_stacked_input")
                action_type.setCurrentText(button_data["type"])
                stacked_input.widget(0).setText(button_data["action"])
                stacked_input.widget(1).setText(button_data["action"])
            for i in range(self.num_dropdown_buttons):
                dropdown_value = mode_data["dropdown_buttons"][f"dropdown_button{i + 1}"]
                dropdown_selector = getattr(self, f"dropdown_button{i + 1}_selector")
                dropdown_selector.setCurrentText(dropdown_value)

    def update_input_type(self):
        """Обновляет видимость полей ввода."""
        for i in range(self.num_standard_buttons):
            action_type = getattr(self, f"standard_button{i + 1}_action_type").currentText()
            stacked_input = getattr(self, f"standard_button{i + 1}_stacked_input")
            stacked_input.setCurrentIndex(0 if action_type == "Print Text" else 1)

    def clear_field(self, stacked_input):
        """Очищает поля ввода."""
        for i in range(stacked_input.count()):
            stacked_input.widget(i).clear()

    def save_mode_data(self):
        """Сохраняет текущие данные режима."""
        current_mode = self.mode_selector.currentText()
        if current_mode in self.modes:
            for i in range(self.num_standard_buttons):
                action_type = getattr(self, f"standard_button{i + 1}_action_type").currentText()
                stacked_input = getattr(self, f"standard_button{i + 1}_stacked_input")
                action_text = stacked_input.currentWidget().text()
                self.modes[current_mode]["standard_buttons"][f"button{i + 1}"] = {"type": action_type,
                                                                                  "action": action_text}

            for i in range(self.num_dropdown_buttons):
                dropdown_selector = getattr(self, f"dropdown_button{i + 1}_selector")
                dropdown_value = dropdown_selector.currentText()
                self.modes[current_mode]["dropdown_buttons"][f"dropdown_button{i + 1}"] = dropdown_value
        with open("modes.json", "w") as f:
            json.dump(self.modes, f, indent=4)

    def on_upload_code_clicked(self):
        """Генерация файла .ino при нажатии кнопки."""
        self.save_mode_data()
        check = generate_ino_file(self.modes, self.num_standard_buttons, self.num_dropdown_buttons)

        if check == 1:
            check = upload_ino_file("kurs.ino")

            if check == 1:
                QMessageBox.information(self, "Success", "Drive upload successfully.")
            else:
                QMessageBox.warning(self, "Error", str(check))
        else:
            QMessageBox.warning(self, "Error", str(check))


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ArduinoCodeGenerator()
    window.show()
    sys.exit(app.exec_())
