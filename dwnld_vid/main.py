from down import download_from_url

if __name__ == '__main__':
    urls = [
        "https://www.youtube.com/watch?v=F7XAQNRn638",
        # "https://www.tiktok.com/@hcc1957/video/7522456723186109714"
    ]

    for url in urls:
        download_from_url(url)
