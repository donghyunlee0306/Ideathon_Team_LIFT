import dart_fss as dart
import pandas as pd
import os

# Open DART API KEY 설정
api_key = os.getenv("DART_API_KEY")
dart.set_api_key(api_key=api_key)

# 회사정보, 코드, 섹터(있다면) 정보를 담은 Dictionary로 slicing
def slice_dictionary(dict):
    try:
        dict['sector']
    except KeyError:
        dict['sector'] = None
    
    keyword = ['corp_code', 'corp_name', 'sector']
    mod_dict = {key:dict[key] for key in keyword}
    return mod_dict

def get_sector() :
    # DART 에 공시된 회사 리스트 불러오기
    corp_list = dart.get_corp_list()

    # 사라진 회사들을 걸러내기 위해 최신 공시 정보가 23년 이후인 회사들만 추려내기 (개수: 28557)
    corp_modified = [corp_list[i] for i in range(len(corp_list))
                 if int(corp_list[i]._info['modify_date']) > 20230101]

    # 회사의 분야는 코스피, 코스닥, 코넥스에 상장된 회사들만 정리되이 있기에 다시 추리기 (개수: 1931)
    corp_stock = [corp_modified[i] for i in range(len(corp_modified)) 
              if corp_modified[i]._info['stock_code'] is not None]

    # Dart에 정리된 sector 정리 (종류: 149개); 상장되었지만 sector 분류가 되어있지 않은 회사도 존재 (개수: 160개)
    sector = []
    sector_none = []
    for i in range(len(corp_stock)):

        try:
            sector.append(corp_stock[i]._info['sector'])
        except:
            sector_none.append(i)

    sector_set = set(sector)
    comp_stock_tidy = [slice_dictionary(corp_stock[i]._info) for i in range(len(corp_stock))]
    
    return comp_stock_tidy