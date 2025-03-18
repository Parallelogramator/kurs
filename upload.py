import os
import subprocess
import serial.tools.list_ports
import time

def find_pro_micro_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print("Найдено устройство:", port.description)
        if "Arduino Micro" in port.description or "COM6" in port.description:
            return port.device
    return None

def reset_pro_micro(port):
    try:
        with serial.Serial(port, baudrate=1200, timeout=1) as ser:
            ser.dtr = False
            time.sleep(0.1)
            ser.dtr = True
            time.sleep(0.1)
    except Exception as e:
        print(f"Ошибка при сбросе: {e}")

def find_bootloader_port(old_port):
    time.sleep(3)  # Увеличенная задержка для завершения сброса
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.device != old_port:
            print(f"Новый загрузочный порт: {port.device}")
            return port.device
    return None

def upload_ino_file(ino_path):
    try:
        if not os.path.exists(ino_path):
            raise FileNotFoundError(f"Файл {ino_path} не найден.")

        cli_path = os.path.expanduser("~/.arduino-cli/arduino-cli")

        # Установка библиотеки HID-Project
        subprocess.run([cli_path, "lib", "install", "HID-Project"], check=True)

        print("Компиляция...")
        build_dir = os.path.join(os.path.dirname(ino_path), "build")
        subprocess.run([cli_path, "compile", "--fqbn", "arduino:avr:micro", "--output-dir", build_dir, ino_path], check=True)

        port = find_pro_micro_port()
        if not port:
            raise Exception("Arduino Pro Micro не найден. Проверьте подключение.")

        print(f"Переводим {port} в режим загрузчика...")
        reset_pro_micro(port)
        time.sleep(1)  # Дополнительная задержка после сброса
        boot_port = find_bootloader_port(port)
        if not boot_port:
            raise Exception("Не удалось определить загрузочный порт.")

        print("Загрузка прошивки...")
        upload_cmd = [
            cli_path, "upload", "-p", boot_port, "--fqbn", "arduino:avr:micro", "-v", "--input-dir", build_dir
        ]
        print(f"Выполняется: {' '.join(upload_cmd)}")  # Для отладки
        subprocess.run(upload_cmd, check=True)

        print("Загрузка успешно завершена!")
        return 1
    except Exception as e:
        return e

if __name__ == "__main__":
    ino_file = "keyboard1/keyboard1.ino"
    result = upload_ino_file(ino_file)
    if result != 1:
        print("Ошибка:", result)