import os
import re


def parse_pro_file(file_path):
    sources = []
    translations = []
    current_list = None

    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            line = line.strip()
            if line.startswith('SOURCES'):
                current_list = sources
                current_list.extend(re.findall(r'[\w/.]+\.py', line))
            elif line.startswith('TRANSLATIONS'):
                current_list = translations
                current_list.extend(re.findall(r'[\w/.]+\.ts', line))
            elif line.endswith('\\'):
                if current_list is not None:
                    current_list.extend(re.findall(r'[\w/\.]+', line))
            else:
                current_list = None

    return sources, translations


def generate_command(sources, translations):
    command = 'pyside6-lupdate ' + ' '.join(sources) + ' -ts ' + ' '.join(translations)
    return command


def main():
    pro_file_path = 'main.pro'
    sources, translations = parse_pro_file(pro_file_path)

    if sources and translations:
        command = generate_command(sources, translations)
        print(f"Executing command: {command}")
        os.system(command)
    else:
        print("No sources or translations found in the .pro file.")

    os.system('pyside6-lrelease app/resource/i18n/app.zh_CN.ts  -qm app/resource/i18n/app.zh_CN.qm')
    os.system('pyside6-rcc app/resource/resource.qrc -o app/common/resource.py')


if __name__ == "__main__":
    main()
