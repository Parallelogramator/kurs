import os
import subprocess
import platform
import zipfile


def install_dependencies():
    system = platform.system().lower()
    arch = platform.machine()

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

    project_dir = os.getcwd()
    work_dir = os.path.join(project_dir, "tools")
    os.makedirs(work_dir, exist_ok=True)

    cli_archive = os.path.join(work_dir, os.path.basename(cli_url))
    if not os.path.exists(cli_archive):
        print("Скачивание arduino-cli...")
        subprocess.run(["curl", "-L", cli_url, "-o", cli_archive], check=True)

    if cli_url.endswith(".zip"):
        with zipfile.ZipFile(cli_archive, 'r') as zip_ref:
            zip_ref.extractall(work_dir)
    else:
        subprocess.run(["tar", "-xzf", cli_archive, "-C", work_dir], check=True)

    cli_path = os.path.join(work_dir, cli_binary)

    print("Настройка arduino-cli...")
    subprocess.run(
        [cli_path, "config", "init", "--overwrite", "--additional-urls",
         "https://downloads.arduino.cc/packages/package_index.json"],
        check=True)

    print("Установка ядра для платы...")
    subprocess.run([cli_path, "core", "install", "arduino:avr"], check=True)

    print("arduino-cli успешно установлен и настроен в папке проекта!")


if __name__ == "__main__":
    install_dependencies()
