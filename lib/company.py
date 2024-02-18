import dart_fss as dart
import os
import requests
import json
import pandas as pd
from dotenv import load_dotenv

load_dotenv(verbose=True)
api_key =  os.getenv("DART_API_KEY")

url_json = "https://opendart.fss.or.kr/api/list.json"
url_xml = "https://opendart.fss.or.kr/api/list.xml"

def get_rpt_code(corp_code) :
    params = {
        'crtfc_key' : api_key,
        'corp_code' : corp_code,
        'bgn_de' : '20190101',
        'end_de' : '20231231',
        'pblntf_ty' : 'A'
    }

    response = requests.get(url_json, params=params)
    data = response.json()

    data_list = data.get('list')
    df_list = pd.DataFrame(data_list)
    rcpt_no = "none"
    if len(df_list) > 0:
        rcpt_no = df_list['rcept_no'][0]

    return rcpt_no

def comp_code(name) :
    dart.set_api_key(api_key=api_key)
    all_corps = dart.api.filings.get_corp_code()
    df_listed = pd.DataFrame(all_corps)

    corp_code = "00000000"
    if sum(df_listed['corp_name'] == name) != 0 :
        corp_code = df_listed[df_listed['corp_name'] == name].iloc[0,0]

    return corp_code