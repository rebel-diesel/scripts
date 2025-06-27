import csv
import os
from openpyxl import load_workbook

# Пути к справочникам и файлам
TEMPLATE_XLSX = "input/FKKO_template.xlsx"
TYPE_DICT_PATH = "input/dic_01_type.txt"
FORM_DICT_PATH = "input/dic_02_form.txt"
INPUT_CSV = "output/fkko_full.csv"
OUTPUT_XLSX = "output/FKKO_2025.xlsx"


# Загрузка справочников
def load_dictionary(file_path):
    d = {}
    with open(file_path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or ";" not in line:
                continue
            code, name = line.split(";", 1)
            d[code.replace(" ", "")] = name.strip()
    return d

def load_dictionaries():
    if not os.path.exists(TYPE_DICT_PATH) or not os.path.exists(FORM_DICT_PATH):
        raise FileNotFoundError("Отсутствуют справочники: dic_01_type.txt или dic_02_form.txt")
    return load_dictionary(TYPE_DICT_PATH), load_dictionary(FORM_DICT_PATH)

# Валидация и форматирование кода

def validate_and_extract_codes(code_str):
    code = code_str.replace(" ", "")
    if not code.isdigit() or len(code) != 11:
        return None
    return code

def format_fkko_code(code):
    return f"{code[0]} {code[1:3]} {code[3:6]} {code[6:8]} {code[8:10]} {code[10]}"

# Чтение и обогащение данных
def read_and_enrich_data(input_csv, type_dict, form_dict):
    enriched_data = []
    with open(input_csv, encoding="utf-8") as infile:
        reader = csv.reader(infile, delimiter=";")
        next(reader)  # заголовок

        for line_number, row in enumerate(reader, 2):
            if len(row) != 2:
                continue
            raw_code, name = row
            code = validate_and_extract_codes(raw_code)
            if not code:
                continue
            formatted = format_fkko_code(code)
            if code[:4] == '1790':
                sss = code[:4]
            type_name = type_dict.get(code[:4], f"!нет данных в справочнике типов отходов")
            if type_name == f"!нет данных в справочнике типов отходов":
                type_name = type_dict.get(code[:3], f"!нет данных в справочнике типов отходов")
            form_name = form_dict.get(code[8:10], f"!нет данных в справочнике агрегатных состояний")
            enriched_data.append((formatted, code, name.strip().capitalize(), type_name.capitalize(), form_name.capitalize()))
    return enriched_data

# Запись в Excel
def write_to_excel(enriched_data, template_path, output_path):
    wb = load_workbook(template_path)
    sheet_order = {
        "4": wb.worksheets[0],
        "5": wb.worksheets[1],
        "3": wb.worksheets[2],
        "2": wb.worksheets[3],
        "1": wb.worksheets[4],
        "0": wb.worksheets[5],
        "all": wb.worksheets[6],
    }

    headers = ["Код (форматированный)", "Код", "Наименование", "Тип отхода", "Агр. состояние"]
    for sheet in wb.worksheets:
        sheet.append(headers)

    for formatted, code, name, type_name, form_name in enriched_data:
        last_digit = code[-1]
        row = [formatted, code, name, type_name, form_name]
        sheet = sheet_order.get(last_digit, sheet_order["0"])
        sheet.append(row)
        sheet_order["all"].append(row)

    wb.save(output_path)

# Основной процесс
def process_fkko():
    try:
        print("Загрузка справочников...")
        type_dict, form_dict = load_dictionaries()

        print("Чтение и обогащение данных...")
        enriched_data = read_and_enrich_data(INPUT_CSV, type_dict, form_dict)

        print("Запись в Excel...")
        write_to_excel(enriched_data, TEMPLATE_XLSX, OUTPUT_XLSX)

        print(f"Готово. Результат: {OUTPUT_XLSX}")
    except Exception as e:
        print(f"Ошибка: {e}")