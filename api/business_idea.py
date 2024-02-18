from fastapi import APIRouter
from mysql.connector import connect
from dotenv import load_dotenv
import os

from lib import finance as fin
from lib import crawling as cr
from lib import llm
import lib.database as db
from api.classes import IdeaInput
from lib.modify import modify_result1, modify_result3, modify_result4

load_dotenv(verbose=True)

router = APIRouter(
    prefix='/idea',
    tags=['idea'])

@router.get('/')
async def main():
    print('idea')
    return {'message':'idea input'}

# idea input 리스트
@router.post('/')
async def idea_input(input:IdeaInput):
    try:

        #docker에서 접속시 inspect의 IPAddress 사용 가능
        connection = connect(
            host = os.getenv('HOST'),
            port = os.getenv('PORT'),
            user = os.getenv('DB_USER_NAME'),
            password = os.getenv('PASSWORD'),
            auth_plugin = 'mysql_native_password',
            db = os.getenv('DB'),
            charset = 'utf8'
        )

        print('connection success')
    except:
        print('connection failed')


    total_idea = '1. 사업분야\n' + input.area + '\n2. 사업 참여 인원 구성 정보 (팀(인원수))\n' + input.member + '\n3. 사업 배경, 목표\n' + input.background + '\n4. 기술성\n' + input.technology + '\n5. 기타\n' + input.others
    print(total_idea)
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

    result_market = modify_result1(market, keywords)

    print('result1 success')

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

    print('result2 success')

    # 3. SWOT 분석
    context3 = total_idea + '\n' + '6. 시장상황 \n' + market[5]
    question3 = "위의 사업 아이디어의 SWOT을 분석해줘. 결과를 각 항목 3개씩 ===를 항목이름 위 아래에 붙여서 구분해서 출력해줘"
    result3 = llm.get_llm_result(context3, question3)
    swot = result3.split("===")

    result_swot = modify_result3(swot)

    print('result3 success')

    # 4. 스탠스 분석
    context4 = result3
    question4 = "이러한 SWOT을 갖는 사업을 진행하는 팀이 가져야하는 스탠스를 SO, ST, WO, WT의 관점에서 분석해줘. 결과를 각 항목 3개씩 ===를 항목이름 위 아래에 붙여서 구분해서 출력해줘"
    result4 = llm.get_llm_result(context4, question4)
    stance = result4.split("===")

    result_stance = modify_result4(stance)

    print('result4 success')

    return {
        'market': result_market,
        'competitor': corp,
        'swot': result_swot,
        'stance': result_stance
    }
