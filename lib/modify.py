import re
def modify_result1(result, keyword) :
    news = [dict()]*5
    summary = re.sub(r'6. 5줄 요약:', '', result[5])
    for i in range(5) :
        tmp = result[i].split('\n  ')
        title = re.sub(r'항목: ', '', tmp[0])
        article = re.sub(r'이유: ', '', tmp[1])
        news[i] = {'title': title, 'article' : article}

    key_tmp = keyword.split('\n')
    keywords = [dict()]*20
    for i in range(20):
        tmp = key_tmp[i].split(':')
        text = re.sub(r' +', '', tmp[0])
        value = int(re.sub(r'[^0-9]+', '', tmp[1]))
        keywords[i] = {'text' : text, 'value' : value}
    return {'news': news, 'summary' : summary, 'keyword' : keywords}

def modify_result3(swot) :
    strength = re.sub(r'\n\n', '\n', swot[2])
    weakness = re.sub(r'\n\n', '\n', swot[4])
    opportunities = re.sub(r'\n\n', '\n', swot[6])
    threats = re.sub(r'\n\n', '\n', swot[8])
    threats = re.sub(r'`', '', threats)
    return {'s': strength, 'w': weakness, 'o': opportunities, 't': threats}

def modify_result4(stance) :
    so = re.sub(r'\n\n', '\n', stance[2])
    st = re.sub(r'\n\n', '\n', stance[4])
    wo = re.sub(r'\n\n', '\n', stance[6])
    wt = re.sub(r'\n\n', '\n', stance[8])
    wt = re.sub(r'`', '', wt)
    return {'so': so, 'st': st, 'wo': wo, 'wt': wt}