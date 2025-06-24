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
        print("  p — только парсинг")
        print("  o — только обработка")
        print("  b — и парсинг, и обработка")
        print("  q — выход")
        choice = input("Выбор (p/o/b/q): ").strip().lower()

        if choice == "p":
            parse_fkko_pages()
        elif choice == "o":
            process_fkko()
        elif choice == "b":
            parse_fkko_pages()
            process_fkko()
        elif choice == "q":
            print("Выход.")
        else:
            print("Неизвестная команда. Завершение.")

if __name__ == "__main__":
    main()
