import os
from dotenv import load_dotenv

load_dotenv(verbose=True)

from lib import database as db
from lib import idea
from lib import crawling as cr
from lib import llm
from lib import finance as fin
from lib.modify import modify_result1, modify_result3, modify_result4
from mysql.connector import connect

connection = connect(
    host = os.getenv('HOST'),
    port = os.getenv('PORT'),
    user = os.getenv('DB_USER_NAME'),
    password = os.getenv('PASSWORD'),
    auth_plugin = 'mysql_native_password',
    db = os.getenv('DB'),
    charset = 'utf8'
)


total_idea = idea.get_input()

business_line = total_idea.split('\n')[1]
news_titles = cr.get_title(business_line, 100)
titles = ''
for news in news_titles:
    titles = titles + news['title'] + '\n'

# 1. 시장 상황 분석
context1 = titles + "이 기사 헤드라인들을 인지했니?"
question1 = "해당 기사 제목들을 통해 " + business_line + "의 시장상황을 긍정적으로 평가할 수 있을까? 결과를\n1. 항목 : 이유 \n2. 항목 : 이유 \n3. 항목 : 이유 \n4. 항목 : 이유 \n5. 항목 : 이유 \n6. 5줄 요약 : \n의 형식으로 뽑아줘"
question1_1 = "해당 텍스트에서 키워드를 추출하고 빈도수를 분석해줘 형식은 단어:빈도수 로 해주고 빈도수 순서로 나열해서 설명없이 20개만 뽑아줘"
result1 = llm.get_llm_result(context1, question1)
keywords = llm.get_llm_result(context1, question1_1)
market = result1.split('\n\n')

# 2. 기업 분석
context2_1 = ' / '.join(db.get_sectors(connection)) + " 이 사업 분야들을 인지했니?"
question2_1 = "해당 사업 분야들에서 " + business_line + "와 유사한 사업 분야 5개를 산업 분야만 일렬로 /로 구분해서 설명없이 나열해줘"
result2_1 = llm.get_llm_result(context2_1, question2_1)
sectors_list = result2_1.split(' / ')

corp_list = db.get_firms(sectors_list, connection)
context2_2 = ', '.join(corp_list) + " 이 기업들을 인지했니?"
question2_2 = "해당 기업들 중에서 " + business_line + " 사업을 진행하고 있는 한국 기업 5개를 기업 이름만 일렬로 쉼표로 구분해서 설명없이 나열해줘"
result2_2 = llm.get_llm_result(context2_2, question2_2)
result2_2 = result2_2.split(', ')

cnt = 0
corp = [dict(), dict(), dict()]
corp_info = fin.get_corp_info(result2_2, cnt, connection)
corp = corp_info['corp']

# 3. SWOT 분석
context3 = total_idea + '\n' + '6. 시장상황 \n' + market[5]
question3 = "위의 사업 아이디어의 SWOT을 분석해줘. 결과를 각 항목 3개씩 ===를 항목이름 위 아래에 붙여서 구분해서 출력해줘"

result3 = llm.get_llm_result(context3, question3)
swot = result3.split("===")

# 4. 스탠스 분석
context4 = result3
question4 = "이러한 SWOT을 갖는 사업을 진행하는 팀이 가져야하는 스탠스를 SO, ST, WO, WT의 관점에서 분석해줘. 결과를 각 항목 3개씩 ===를 항목이름 위 아래에 붙여서 구분해서 출력해줘"

result4 = llm.get_llm_result(context4, question4)
stance = result4.split("===")

connection.close()

print(modify_result1(market, keywords))
print('\n')
print(corp)
print('\n')
print(modify_result3(swot))
print('\n')
print(modify_result4(stance))