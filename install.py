import os
import subprocess
import platform
import zipfile

def install_dependencies():
    # Определяем ОС
    system = platform.system().lower()
    arch = platform.machine()

    # Определяем URL для загрузки arduino-cli
    if system == "windows":
        cli_url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Windows_64bit.zip"
        cli_binary = "arduino-cli.exe"
    elif system == "linux":
        cli_url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_Linux_64bit.tar.gz"
        cli_binary = "arduino-cli"
    elif system == "darwin":
        cli_url = "https://downloads.arduino.cc/arduino-cli/arduino-cli_latest_macOS_64bit.tar.gz"
        cli_binary = "arduino-cli"
    else:
        raise Exception("Unsupported operating system")

    # Создаем рабочую директорию
    work_dir = os.path.expanduser("~/.arduino-cli")
    os.makedirs(work_dir, exist_ok=True)

    # Скачиваем arduino-cli
    cli_archive = os.path.join(work_dir, os.path.basename(cli_url))
    if not os.path.exists(cli_archive):
        print("Скачивание arduino-cli...")
        subprocess.run(["curl", "-L", cli_url, "-o", cli_archive], check=True)

    # Распаковываем архив
    if cli_url.endswith(".zip"):
        with zipfile.ZipFile(cli_archive, 'r') as zip_ref:
            zip_ref.extractall(work_dir)
    else:
        subprocess.run(["tar", "-xzf", cli_archive, "-C", work_dir], check=True)

    # Добавляем arduino-cli в PATH
    cli_path = os.path.join(work_dir, cli_binary)
    os.environ["PATH"] += os.pathsep + work_dir
    print(os.pathsep, cli_path)

    # Настройка arduino-cli
    print("Настройка arduino-cli...")
    subprocess.run(
        [cli_path, "config", "init", "--additional-urls", "https://downloads.arduino.cc/packages/package_index.json"],
        check=True)

    # Устанавливаем ядро для платы Arduino Leonardo
    print("Установка ядра для платы...")
    subprocess.run([cli_path, "core", "install", "arduino:avr"], check=True)

    print("arduino-cli успешно установлен и настроен!")


if __name__ == "__main__":
    install_dependencies()
