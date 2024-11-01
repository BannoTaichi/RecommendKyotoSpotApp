# conda install transformers
# pip install torch
# pip install scipy

# conda activate language

import requests
from bs4 import BeautifulSoup
import re
import pandas as pd

url = "https://www.jalan.net/kankou/260000/"
res = requests.get(url)
soup = BeautifulSoup(res.content, "html.parser")

# これしないと文字化け
soup = BeautifulSoup(res.content.decode("Shift-JIS", "ignore"), "html.parser")

elems = soup.find_all(href=re.compile("/kuchikomi"))
pickup_links = [elem.attrs["href"] for elem in elems]

df = pd.DataFrame()
count = 0

# テキストの前処理
table = {
    "\n": "",  # 改行を削除
    "\r": "",  # 改行を削除
    "(": "（",  # 全角に変更
    ")": "）",  # 全角に変更
    "[": "［",  # 全角に変更
    "]": "］",  # 全角に変更
    '"': "”",  # 全角に変更
    "'": "’",  # 全角に変更
}

# 一覧のリンクを順に処理-------------
for elem, pickup_link in zip(elems, pickup_links):

    # 口コミ数20件以上なかったらスキップ------------
    if int(re.findall(r"\d+", elem.contents[0])[-1]) <= 20:
        continue

    # requests.get(): Pickupリンクへ移動してページ１の情報取得の準備-----
    page1_res = requests.get("https:" + pickup_link)
    page1_soup = BeautifulSoup(page1_res.text, "html.parser")
    page1_soup = BeautifulSoup(
        page1_res.content.decode("Shift-JIS", "ignore"), "html.parser"
    )
    # ページ２へ移動して、情報取得の準備--------------
    page2_elem = page1_soup.find(href=re.compile("/page_2/"))
    page2_link = page2_elem.attrs["href"]
    page2_res = requests.get(page2_link)
    page2_soup = BeautifulSoup(page2_res.text, "html.parser")
    page2_soup = BeautifulSoup(
        page2_res.content.decode("Shift-JIS", "ignore"), "html.parser"
    )
    # ページ３へ移動して、情報取得の準備----------
    page3_elem = page1_soup.find(href=re.compile("/page_3/"))
    page3_link = page3_elem.attrs["href"]
    page3_res = requests.get("https://www.jalan.net" + page3_link)
    page3_soup = BeautifulSoup(page3_res.text, "html.parser")
    page3_soup = BeautifulSoup(
        page3_res.content.decode("Shift-JIS", "ignore"), "html.parser"
    )
    # 各ページのsoupを格納---------------
    soups = [page1_soup, page2_soup, page3_soup]

    # 観光地の名前----------------
    spot_path = page1_soup.find("p", class_="detailTitle")
    spot = spot_path.contents[0]
    print("\nSightseeingSpot: ", spot)
    count += 1

    # その観光地の名前、タイトル・スコア・口コミをまとめたリスト----
    new_list = [[spot] * 20, [], [], []]

    # 各ページについてスクレイピング
    for page_soup in soups[:-1]:
        # titles: 口コミタイトル----------
        titles = page_soup.find_all("p", class_="reviewCassette__title", limit=10)
        if len(titles) == 0:
            titles = page_soup.find_all("p", class_="item-title", limit=10)
            for title in titles:
                new_list[1].append(title.contents[0].contents[0])
                # print(title.contents[0].contents[0])
        else:
            for title in titles:
                new_list[1].append(title.contents[0])
                # print(title.contents[0])

        # scores: 口コミスコア----------
        scores = page_soup.find_all(class_="reviewPoint", limit=11)
        for score in scores[1:]:
            new_list[2].append(score.contents[0])

        # comments: 口コミ内容-------------
        comments = page_soup.find_all("p", class_="reviewCassette__comment", limit=10)
        if len(comments) == 0:
            comments = page_soup.find_all("div", class_="item-reviewTextInner")
        for comment in comments:
            try:
                text = comment.contents[0].translate(str.maketrans(table))
            except:
                text = comment.contents[0].contents[0].translate(str.maketrans(table))
            print(text)
            new_list[3].append(text)
            # print(comment.contents[0])

    # new_df: 現在のループの観光地の名前、口コミをまとめたデータフレーム------
    new_df = pd.DataFrame(data=new_list)
    new_df = new_df.T
    df = df._append(new_df)

    # 観光地が30か所集まったらスクレイピング終了
    if count == 30:
        print("break!")
        break

df = df.reset_index()
del df["index"]
df.columns = ["Spot", "reviewTitle", "reviewScore", "reviewComment"]
df.to_csv("output.csv", index=False, encoding="utf-8")

# df
