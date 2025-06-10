import serial.tools.list_ports
import time


def find_pro_micro_port():
    ports = serial.tools.list_ports.comports()
    for port in ports:
        print("Найдено устройство:", port.description)
        if "USB" in port.description or "COM5" in port.description:
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
    time.sleep(3)
    ports = serial.tools.list_ports.comports()
    for port in ports:
        if port.device != old_port:
            print(f"Новый загрузочный порт: {port.device}")
            return port.device
    return None


def upload_ino_file(ino_path):
    try:
        import pyduinocli

        arduino = pyduinocli.Arduino(r"tools/arduino-cli.exe")

        boards = arduino.board.list()
        if not boards['result']:
            return "Платы не найдены. Проверьте подключение."
        print(boards)
        port = boards['result']['detected_ports'][0]['port']['address']
        fqbn = boards['result']['detected_ports'][0]['matching_boards'][0]['fqbn']

        compile_result = arduino.compile(sketch=ino_path, fqbn=fqbn)
        print(compile_result)
        if not compile_result['result']['success']:
            print(compile_result['result']['compiler_err'])
            return compile_result['result']['compiler_err']

        upload_result = arduino.upload(sketch=ino_path, fqbn=fqbn, port=port)
        print(upload_result)
        if 'Found programmer' in upload_result['result']['stderr']:
            print("Загрузка успешна")
        else:
            print(upload_result['result']['stderr'])
            return upload_result['result']['stderr']
        return 1
    except Exception as e:
        return e


if __name__ == "__main__":
    ino_file = "kurs.ino"
    result = upload_ino_file(ino_file)
    if result != 1:
        print("Ошибка:", result)
