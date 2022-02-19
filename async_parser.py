import time
import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
import datetime
import fake_useragent
import json
import lxml
import os


class LabirintParser:
    def __init__(self) -> None:
        self.all_data = []
        self.domain = "https://www.labirint.ru"
        self.url_with_pages = "https://www.labirint.ru/genres/2308/?display=table&available=1&paperbooks=1&otherbooks=1&page={}"
        self.ua = fake_useragent.UserAgent()
        self.main_url = "https://www.labirint.ru/genres/2308/?display=table&available=1&paperbooks=1&otherbooks=1"
        self.now = datetime.datetime.now().strftime("%d_%m_%Y_%H_%M")
        self.headers = {
            "user-agent": self.ua.random,
            "accept": "*/*"
        }

    def get_last_page(self):
        response = requests.get(url=self.main_url, headers=self.headers)
        soup = BeautifulSoup(response.text, "lxml")
        last_page = soup.find("div", class_="pagination-numbers__right"
                              ).find_all("div", class_="pagination-number"
                                         )[-1].text.strip()

        return int(last_page)

    async def get_tasks(self):
        async with aiohttp.ClientSession() as session:
            last_page = self.get_last_page()
            tasks = []
            for page in range(1, last_page + 1):

                task = asyncio.create_task(
                    self.get_data(session=session, page=page))
                tasks.append(task)
            await asyncio.gather(*tasks)

    async def get_data(self, session, page):
        url = self.url_with_pages.format(page)
        async with session.get(url) as session_html:
            session_html_text = await session_html.text()
            soup = BeautifulSoup(session_html_text, "lxml")
            all_card = soup.find(
                "tbody", class_="products-table__body").find_all("tr")
            for book in all_card:
                try:
                    name_book = book.find("a", class_="book-qtip").text.strip()
                except:
                    name_book = ""

                try:
                    book_link = f'{self.domain}{book.find("a", class_="book-qtip").get("href")}'
                except:
                    book_link = ""
                try:
                    book_published = book.find(class_="products-table__pubhouse").find(
                        "div").text
                    book_published = " ".join(
                        i for i in book_published.split())
                except:
                    book_published = ""

                try:
                    new_price = int(
                        "".join(book.find("span", class_="price-val").text.strip().split()[:-1]))
                except:
                    new_price = 0
                try:
                    old_price = int(
                        book.find("span", class_="price-old").text.strip())
                except:
                    old_price = 0

                self.all_data.append(
                    {
                        "название книги": name_book,
                        "ссылка на книгу": book_link,
                        "издательсво": book_published,
                        "старая цена": old_price,
                        "новая цена": new_price
                    }
                )
            print(f"[INFO] Обработана стрница {page}")

    def json_recorder(self):
        if not os.path.exists("data"):
            os.mkdir("data")
        with open(f"data/{self.now}.json","w", encoding="utf-8") as file:
            json.dump(self.all_data, file, ensure_ascii=False, indent=4)

    def main(self):
        start_time = time.time()

        asyncio.run(self.get_tasks())
        self.json_recorder()
        print(
            f"[INFO] Время выполнения скрипта составило {time.time() - start_time}")


if __name__ == "__main__":
    LabirintParser().main()



