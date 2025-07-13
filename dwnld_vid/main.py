from down import download_from_url

if __name__ == '__main__':
    urls = [
        "https://youtu.be/nfWlot6h_JM?list=RDnfWlot6h_JM",
        "https://www.tiktok.com/@hcc1957/video/7522456723186109714"
        # Добавь сюда свои ссылки
    ]

    for url in urls:
        download_from_url(url)
