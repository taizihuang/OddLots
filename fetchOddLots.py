import requests,os,json,platform
import pandas as pd
from bs4 import BeautifulSoup


type_dict = {
    'document': 'body',
    'paragraph': 'p',
    }

headers = {
    'referer': 'https://www.bloomberg.com/oddlots',
    'user-agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1'
}

def formatSingle(data_dict):
    type = data_dict['type']
    if type == 'text':
        t = data_dict['value']
        if 'attributes' in data_dict.keys():
            if 'strong' in data_dict['attributes'].keys():
                t = f'<br><b>{t}</b><br>'
            elif 'emphasis' in data_dict['attributes'].keys():
                t = f'<b>{t}</b>'
        return t
    elif type == 'br':
        return '<br>'
    elif type == 'embed':
        if 'iframeData' in data_dict.keys():
            return data_dict['iframeData']['html']
        else:
            return f'<div style="left: 0; width: 100%; height: 180px; position: relative;"><iframe src="{data_dict["href"]}" style="top: 0; left: 0; width: 100%; height: 100%; position: absolute; border: 0;" allowfullscreen></iframe></div>'
    elif type in type_dict.keys():
        return f'<{type_dict[type]}>{data_dict["value"]}</{type_dict[type]}>'
    else:
        return '' 

def format(data_dict):
    body = ''
    type = data_dict['type']
    if 'content' in data_dict.keys():
        for content in data_dict['content']:
            body += format(content)
        if type in type_dict.keys():
            body = f'<{type_dict[type]}>{body}</{type_dict[type]}>'
        elif type == 'link':
            body = f'<a href={data_dict["data"]["href"]}>{body}</a>'
    else:
        body = formatSingle(data_dict)

    return body

def fetchOddLots(url):
    print(url)
    docs = requests.get(url,headers=headers).content
    doc = BeautifulSoup(docs,features='lxml')
    story = json.loads(doc.find('script',{'id':"__NEXT_DATA__"}).string)['props']['pageProps']['story']
    title = story['seoTitle']
    body = story['body']
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
        <h2>{title}</h2>
    '''.format(title=title)
    body = format(body).replace('<body>','').replace('<br><br>','<br>').replace('<p><br>','<p>')
    html = html+body+'</body></html>'

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

    if platform.system() == 'Windows':
        os.environ['https_proxy'] = 'http://127.0.0.1:7890'
        os.environ['http_proxy'] = 'http://127.0.0.1:7890'

    df_odd = pd.read_pickle('oddlots.pkl')
    doc = requests.get('https://www.bloomberg.com/lineup/api/lazy_load_paginated_module?id=more_articles_list&offset=0&page=oddlots&zone=switch',headers=headers).content
    link_title = list(set([(a['href'], a.text) for a in BeautifulSoup(json.loads(doc)['html'],features='lxml').findAll('a') if '\n\n' not in a.text])) #if 'transcript' in a['href'] ))
    for link, title in link_title:
        df = fetchOddLots('https://www.bloomberg.com'+link)
        df_odd = pd.concat([df, df_odd], ignore_index=True)
    df_odd = df_odd.loc[df_odd.content.str.contains('Odd Lots')].drop_duplicates(subset=['link']).reset_index(drop=True)
    genHTML(df_odd)
    df_odd.to_pickle('oddlots.pkl')
