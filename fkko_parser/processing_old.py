import csv
from openpyxl import load_workbook

def format_fkko_code(code):
    if len(code) != 11 or not code.isdigit():
        return code  # не форматируем, если что-то не так
    return f"{code[0]} {code[1:3]} {code[3:6]} {code[6:8]} {code[8:10]} {code[10]}"

def process_fkko():
    input_csv = "output/fkko_full.csv"
    template_xlsx = "output/FKKO_template.xlsx"
    output_xlsx = "output/FKKO_2025.xlsx"

    # Считываем CSV
    data = []
    with open(input_csv, encoding="utf-8") as f:
        for line in f:
            code = line[:11].strip()
            name = line[12:].strip()
            if code and name and code.isdigit():
                formatted = format_fkko_code(code)
                data.append((formatted, code, name))

    # Загружаем шаблон Excel
    wb = load_workbook(template_xlsx)
    sheet_order = {
        "4": wb.worksheets[0],
        "5": wb.worksheets[1],
        "3": wb.worksheets[2],
        "2": wb.worksheets[3],
        "1": wb.worksheets[4],
        "0": wb.worksheets[5],
        "all": wb.worksheets[6],
    }

    # Записываем данные
    for formatted, code, name in data:
        last_digit = code[-1]
        sheet = sheet_order.get(last_digit, sheet_order["0"])
        sheet.append([formatted, code, name])
        sheet_order["all"].append([formatted, code, name])

    # Сохраняем
    wb.save(output_xlsx)
    print(f"Файл {output_xlsx} успешно создан.")
