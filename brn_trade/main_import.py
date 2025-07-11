from import_brn import init_db, load_bz_folder
import os

DB_PATH = r"C:\sqlite\brn.db"
BRN_FOLDER = r"D:\programming\python\scripts\brn_trade\input\brn"
BZ_FOLDER = r"D:\programming\python\scripts\brn_trade\input\bz"

if __name__ == '__main__':
    if not os.path.exists(DB_PATH):
        print("База не найдена. Создаю новую...")
        init_db()
    else:
        print("База найдена. Продолжаем...")

    load_bz_folder(BZ_FOLDER)