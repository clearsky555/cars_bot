from datetime import datetime
import requests
from bs4 import BeautifulSoup
from db.database import manager
from multiprocessing import Pool


manager = manager


def get_html(URL):
    # Делать запрос по ссылке и возвращать html код этой страницы
    response = requests.get(URL)
    return response.text


def get_posts_links(html):
    links = []
    soup = BeautifulSoup(html, "html.parser")
    table_data = soup.find("div", {"class":"search-results-table"})
    data = table_data.find("div", {"class":"table-view-list"})
    posts = data.find_all("div", {"class":"list-item"})
    for p in posts:
        href=p.find("a").get("href")
        full_url = "https://www.mashina.kg"+href
        links.append(full_url)
    return links # возвращает ссылки на детальную страницу постов


def get_detail_post(html, post_url):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", {"class":"details-wrapper"})
    detail = content.find("div",{"class":"details-content"})
    title = detail.find("div", {"head-left"}).find("h1").text #if detail.find("div", {"head-left"}) else 'none'
    som = detail.find("div", {"class":"sep main"}).find("div",{"class":"price-som"}).text #if detail.find("div", {"class":"sep main"}) else '0 сом'
    dollar = detail.find("div", {"class":"sep main"}).find("div",{"class":"price-dollar"}).text# if detail.find("div", {"class":"sep main"}) else '0 $'
    add_price = detail.find("div",{"class":"sep addit"}).find_all("div") #if detail.find("div",{"class":"sep addit"}) else 'no data'
    tenge = add_price[1].text
    ruble = add_price[0].text
    mobile = detail.find("div",{"class":"details-phone-wrap"}) #if detail.find("div",{"class":"details-phone-wrap"}) else 'no data'
    mobile = mobile.find("div",{"class":"number"}).text# if detail.find("div",{"class":"details-phone-wrap"}) else 'no data'
    description = detail.find("h2", {"class":"comment"}).text #if detail.find("h2", {"class":"comment"}) else 'no data'
    som = int(som.replace("сом", "").strip().replace(" ", ""))
    dollar = int(dollar.replace("$", "").strip().replace(" ", ""))
    data = {
        "title":title,
        "som":som,
        "dollar":dollar,
        "mobile":mobile,
        "description":description,
        'link': post_url
    }
    return data


def get_lp_number(html):
    soup = BeautifulSoup(html, "html.parser")
    content = soup.find("div", {"class":"search-results-table"})
    ul = content.find("ul", {"class":"pagination"})
    lp = ul.find_all("a", {"class":"page-link"})[-1]
    n=lp.get("data-page")
    return int(n)


def write_data(data): # Запись в базу
    result = manager.insert_car(data)
    return result


# def check_broken_post(html):
#     soup = BeautifulSoup(html, "html.parser")
#     content = soup.find("div", {"class":"wrapper"})
#     detail = content.find("div",{"class":"wrap"})
#     error_page = detail.find('h1').text
#     if error_page == 'Страница не найдена':
#         return True
#     else:
#         return False

def get_parse_page(page):
    passed_posts = 0
    URL_MAIN = "https://www.mashina.kg/search/all/all/"
    filter = "?currency=2&price_to=10000&region=1&sort_by=upped_at+desc&steering_wheel=1&town=2"
    FULL_URL = URL_MAIN + filter
    print(f"Парсинг страницы:{page}")
    FULL_URL += f"&page={page}"
    html = get_html(FULL_URL)
    post_links = get_posts_links(html)
    for link in post_links:
        post_html = get_html(link)
        if not manager.check_car_in_db(link):
            post_data = get_detail_post(post_html, post_url=link)
            # print(post_data)
            write_data(data=post_data)
        else:
            passed_posts += 1
    print(f'Количество пропущенных постов: {passed_posts}')


def main():
    start = datetime.now()
    URL_MAIN = "https://www.mashina.kg/search/all/all/"
    filter = "?currency=2&price_to=10000&region=1&sort_by=upped_at+desc&steering_wheel=1&town=2"
    FULL_URL = URL_MAIN + filter
    last_page = get_lp_number(get_html(FULL_URL))
    # 20 threads provide stable parsing, 40 threads cause BrokenPipeError
    with Pool(20) as p:
        p.map(get_parse_page, range(1, last_page+1))

    end = datetime.now()
    print('Время выполнения: ', end-start)


if __name__ == "__main__":
    manager.create_table()
    main()