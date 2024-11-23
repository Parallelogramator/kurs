import os
import subprocess
import serial.tools.list_ports

def find_leonardo_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if "Leonardo" in port.description or "Arduino" in port.description:
            return port.device
    return None

def upload_ino_file(ino_path):
    try:
        # Проверка, что файл существует
        if not os.path.exists(ino_path):
            raise FileNotFoundError(f"Файл {ino_path} не найден.")

        # Определяем arduino-cli
        cli_path = os.path.expanduser("~/.arduino-cli/arduino-cli")

        subprocess.run([cli_path, "lib", "install", "HID-Project"], check=True)

        # Компиляция
        print("Компиляция...")
        build_dir = os.path.join(os.path.dirname(ino_path), "build")
        subprocess.run([cli_path, "compile", "--fqbn", "arduino:avr:leonardo", "--output-dir", build_dir, ino_path], check=True)

        # Поиск порта Arduino Leonardo
        port = find_leonardo_port()
        if not port:
            raise Exception("Arduino Leonardo не найден. Проверьте подключение.")

        # Загрузка
        print("Загрузка прошивки...")
        subprocess.run([cli_path, "upload", "-p", port, "--fqbn", "arduino:avr:leonardo", ino_path], check=True)

        print("Загрузка успешно завершена!")
        return 1
    except Exception as e:
        return e

if __name__ == "__main__":
    # Пример: путь к вашему .ino файлу
    ino_file = "kurs.ino"
    upload_ino_file(ino_file)
