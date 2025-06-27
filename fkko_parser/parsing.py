from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
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

    log("Старт парсинга официального сайта ФККО", log_path)

    service = Service(ChromeDriverManager().install())
    options = webdriver.ChromeOptions()
    options.binary_location = r"c:\Program Files\Google\Chrome\Application\chrome.exe"
    options.add_argument("--headless")
    driver = webdriver.Chrome(service=service, options=options)

    with open(output_path, "w", encoding="utf-8") as f_out:
        f_out.write("Код;Наименование\n")
        for page in range(1, 456):
            if page == 1:
                url = "https://rpn.gov.ru/fkko/"
            else:
                url = f"https://rpn.gov.ru/fkko/nav-more-fkko/page-{page}/"

            log(f"Загрузка страницы {page}: {url}", log_path)
            driver.get(url)

            try:
                WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.CLASS_NAME, "registryCard__itemTableCol"))
                )
            except:
                log(f"⚠️ Страница {page}: не дождался данных, пропущено.", log_path)
                continue

            codes = wait_until_stable(driver, "_code")
            names = wait_until_stable(driver, "_name")

            if len(codes) != len(names):
                log(f"⚠️ Страница {page}: несовпадение кодов и наименований, пропущено.", log_path)
                continue

            count = 0
            for code, name in zip(codes, names):
                k = code.text.strip().replace(";", "/")
                n = name.text.strip().replace(";", "/")
                if k.lower() == "код" or n.lower() == "наименование":
                    continue
                if k and n:
                    f_out.write(f"{k};{n}\n")
                    count += 1
            log(f"✅ Страница {page}: добавлено {count} строк.", log_path)

    driver.quit()
    log(f"Завершено. Сохранено в {output_path}", log_path)

