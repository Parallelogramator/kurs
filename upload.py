import os
import subprocess
import serial.tools.list_ports

def find_pro_micro_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        # Ищем устройство по уникальному дескриптору или по общему описанию "Arduino"
        if "1234567" in port.description or "Arduino" in port.description:
            return port.device
    return None

def upload_ino_file(ino_path):
    try:
        # Проверка существования файла прошивки
        if not os.path.exists(ino_path):
            raise FileNotFoundError(f"Файл {ino_path} не найден.")

        # Определяем путь к arduino-cli (например, в домашней директории)
        cli_path = os.path.expanduser("~/.arduino-cli/arduino-cli")

        # Устанавливаем зависимость HID-Project
        subprocess.run([cli_path, "lib", "install", "HID-Project"], check=True)

        # Компиляция скетча для Arduino Pro Micro.
        # FQBN для Pro Micro: "arduino:avr:pro"
        print("Компиляция...")
        build_dir = os.path.join(os.path.dirname(ino_path), "build")
        subprocess.run([cli_path, "compile", "--fqbn", "arduino:avr:pro", "--output-dir", build_dir, ino_path], check=True)

        # Поиск порта, к которому подключён Arduino Pro Micro
        port = find_pro_micro_port()
        if not port:
            raise Exception("Arduino Pro Micro не найден. Проверьте подключение.")

        # Загрузка прошивки
        print("Загрузка прошивки...")
        subprocess.run([cli_path, "upload", "-p", port, "--fqbn", "arduino:avr:pro", ino_path], check=True)

        print("Загрузка успешно завершена!")
        return 1
    except Exception as e:
        return e

if __name__ == "__main__":
    ino_file = "kurs.ino"  # Укажите путь к вашему .ino файлу
    result = upload_ino_file(ino_file)
    if result != 1:
        print("Ошибка:", result)
