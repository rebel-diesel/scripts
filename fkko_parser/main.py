# main.py

import argparse
from parsing import parse_fkko_pages
from processing import process_fkko

def main():
    parser = argparse.ArgumentParser(description="FKKO Parser and Processor")
    parser.add_argument("--parse", action="store_true", help="Скачать и распарсить данные с сайта")
    parser.add_argument("--process", action="store_true", help="Обработать данные и создать Excel")

    args = parser.parse_args()
    if args.parse:
        parse_fkko_pages()
    if args.process:
        process_fkko()

    if not args.parse and not args.process:
        print("Ничего не указано. Что будем делать?")
        print("  1 — только парсинг")
        print("  2 — только обработка")
        print("  3 — и парсинг, и обработка")
        print("  4 — выход")
        choice = input("Выбор (1/2/3/4): ").strip().lower()

        if choice == "1":
            parse_fkko_pages()
        elif choice == "2":
            process_fkko()
        elif choice == "3":
            parse_fkko_pages()
            process_fkko()
        elif choice == "4":
            print("Выход.")
        else:
            print("Неизвестная команда. Завершение.")

if __name__ == "__main__":
    main()
