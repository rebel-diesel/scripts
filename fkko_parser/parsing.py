from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import os
import time
from datetime import datetime


def log(message, log_path):
    timestamp = datetime.now().strftime("[%Y-%m-%d %H:%M:%S]")
    line = f"{timestamp} {message}"
    print(line)
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def wait_until_stable(driver, class_name, delay=0.5, max_wait=5):
    start = time.time()
    last_count = -1

    while time.time() - start < max_wait:
        elements = driver.find_elements(By.CLASS_NAME, class_name)
        current_count = len(elements)
        if current_count == last_count:
            return elements
        last_count = current_count
        time.sleep(delay)

    return driver.find_elements(By.CLASS_NAME, class_name)


def parse_fkko_pages(output_path="output/fkko_full.csv", log_path="output/fkko.log"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    open(log_path, "w").close()  # очищаем лог

    log("Старт парсинга ФККО", log_path)

    service = Service("driver/chromedriver-win64/chromedriver.exe")
    options = webdriver.ChromeOptions()
    options.binary_location = "C:/Program Files/BraveSoftware/Brave-Browser/Application/brave.exe"
    options.add_argument("--headless")

    driver = webdriver.Chrome(service=service, options=options)

    all_data = []

    for page in range(1, 39):
        if page == 1:
            url = "http://kod-fkko.ru/spisok-othodov/"
        else:
            url = f"http://kod-fkko.ru/spisok-othodov/page/{page}/"

        log(f"Загрузка страницы {page}: {url}", log_path)
        driver.get(url)

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "my_col1"))
            )
        except:
            log(f"⚠️ Страница {page}: не дождался данных, пропущено.", log_path)
            continue

        kod_elements = wait_until_stable(driver, "my_col1")
        name_elements = wait_until_stable(driver, "my_col2")

        if len(kod_elements) != len(name_elements):
            log(f"⚠️ Страница {page}: несовпадение кодов и наименований, пропущено.", log_path)
            continue

        count_before = len(all_data)
        for kod, name in zip(kod_elements, name_elements):
            k = kod.text.strip()
            n = name.text.strip()
            if k.lower().startswith("код") or n.lower().startswith("наименование"):
                continue
            if k and n:
                all_data.append(f"{k};{n}")
        count_after = len(all_data)
        log(f"✅ Страница {page}: добавлено {count_after - count_before} строк.", log_path)

    driver.quit()

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("Код;Наименование\n")
        for line in all_data:
            f.write(line + "\n")

    log(f"Завершено. Всего строк: {len(all_data)}. Сохранено в {output_path}", log_path)
