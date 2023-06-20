import requests,os,json
import pandas as pd
from bs4 import BeautifulSoup

# os.environ['https_proxy'] = 'http://127.0.0.1:7890'
# os.environ['http_proxy'] = 'http://127.0.0.1:7890'

headers = {
    'referer': 'https://www.bloomberg.com/oddlots',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
}

def fetchOddLots(url,title):
    print(url)
    docs = requests.get(url,headers=headers).content
    doc = BeautifulSoup(docs,features='lxml')
    doc1 = BeautifulSoup(json.loads(doc.find('script',{'data-component-props':"ArticleBody"}).string)['story']['body'],features='lxml')
    # doc1.find(class_="thirdparty-embed__container").decompose()
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

    date = url.split('/')[5]
    df_odd = pd.DataFrame(data={'date':date,'title':title,'link':url,'content':html},index=[0])

    return df_odd

def genHTML(df_odd):

    df_odd = df_odd.sort_values('date',ascending=False)
    
    item = ''
    for idx in df_odd.index:
        date = df_odd.loc[idx,'date']
        link = df_odd.loc[idx,'link']
        html = df_odd.loc[idx,'content']
        title = df_odd.loc[idx,'title']
        name = link.split('/')[-1].split('?')[0]
        item = item+"""<ul class="LI"><li><a class="title" href="./html/{name}.html">[{date}] {title}</a></li></ul>""".format(date=date,name=name,title=title)
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

if __name__ == "__main__":
    df_odd = pd.read_pickle('oddlots.pkl')
    doc = requests.get('https://www.bloomberg.com/lineup/api/lazy_load_paginated_module?id=more_articles_list&offset=0&page=oddlots&zone=switch',headers=headers).content
    link_title = list(set([(a['href'], a.text) for a in BeautifulSoup(json.loads(doc)['html'],features='lxml').findAll('a') if '\n\n' not in a.text])) #if 'transcript' in a['href'] ))
    for link, title in link_title:
        df = fetchOddLots('https://www.bloomberg.com'+link, title)
        df_odd = pd.concat([df, df_odd], ignore_index=True)
    df_odd = df_odd.loc[df_odd.content.str.contains('Odd Lots')].drop_duplicates(subset=['link']).reset_index(drop=True)
    genHTML(df_odd)
    df_odd.to_pickle('oddlots.pkl')
