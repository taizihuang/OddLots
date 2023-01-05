import requests,os,json
import pandas as pd
from bs4 import BeautifulSoup
#os.environ['https_proxy'] = 'http://127.0.0.1:7890'
#os.environ['http_proxy'] = 'http://127.0.0.1:7890'


def fetchOddLots(url,title):
    headers = {
        'referer': 'https://www.bloomberg.com/oddlots',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
    docs = requests.get(url,headers=headers).content
    doc = BeautifulSoup(docs,features="lxml")
    body = json.loads(doc.find('script',{'data-component-props':"LeaderboardAd"}).string)
    if 'story' in body:
        doc1 = BeautifulSoup(body['story']['body'],features="lxml")
        if doc1.find(class_="thirdparty-embed__container"):
            doc1.find(class_="thirdparty-embed__container").decompose()
    else:
        doc1 = ''
    html = '''
    <!DOCTYPE html>
    <html>

    <head>
        <meta content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no" name=viewport>
        <meta charset=utf-8>
        <meta name="referrer" content="no-referrer">
        <link rel="stylesheet" href="./init.css">
        <title>{title}</title>
    </head>

    <body>
        <div class="BODY">
            <div class="REPLY_LI">
                <h2>{title}</h2>
    '''.format(title=title)
    html = html+str(doc1)+'</body></html>'

    df_odd = pd.DataFrame(columns=['date','title','link','content'])
    date = url.split('/')[5]
    df_odd = df_odd.append({'date':date,'title':title,'link':url,'content':html},ignore_index=True)

    return df_odd

def genHTML(df_odd):

    item = ''
    for idx in df_odd.index:
        date = df_odd.loc[idx,'date']
        link = df_odd.loc[idx,'link']
        html = df_odd.loc[idx,'content']
        title = df_odd.loc[idx,'title']
        name = link.split('/')[-1].split('?')[0]
        item = item+"""<ul class="LI"><li><a class="title" href="./html/{name}.html">[{date}] {title}</a></li></ul>""".format(date=date, name=name,title=title)
        with open('./html/{}.html'.format(name),'w',encoding='utf8') as f:
            f.write(html)

    indexHTML = """    
        <!DOCTYPE html><html><head><meta content="width=device-width,initial-scale=1,maximum-scale=1,user-scalable=no" name=viewport>
        <meta charset=utf-8><link rel="stylesheet" href="./html/init.css">
        <style>.LI li {list-style-type: disc;}
            .LI li {margin-bottom: 8px;}
            .LI a {text-decoration: none;}
            .LI .title {color: #000;}
            .LI .title:hover {color: #f40;}
            .LI .date {font-size: 12px;color: #999;float: right;}
        </style>
        <title>Odd Lots</title>
    </head>

    <body>
        <div class="BODY">
            <h1>Odd Lots</h1>
            <br><br>
        """
    indexHTML = indexHTML+item+"</div></body></html>"
    with open('./index.html','w',encoding='utf8') as f:
        f.write(indexHTML)

url = 'https://www.bloomberg.com/oddlots'
headers = {
    'referer': 'https://www.bloomberg.com/oddlots',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36'}
doc = BeautifulSoup(requests.get(url,headers=headers).content, features="lxml")
print(doc)

df_odd = pd.read_pickle('oddlots.pkl')
#df_odd = pd.DataFrame(columns=['date','title','link','content'])
for item in doc.findAll(class_='story-list-story__info__headline-link'):
    if 'Transcript' in item.text:
        title = item.text
        print(title)
        link = 'https://www.bloomberg.com' + item['href']
        df_odd_new = fetchOddLots(link,title=title)
        df_odd = df_odd_new.append(df_odd,ignore_index=True)
        df_odd = df_odd.drop_duplicates(['title'])
df_odd = df_odd.sort_values(by=['date'],ascending=False)        
genHTML(df_odd)
df_odd.to_pickle('oddlots.pkl')
