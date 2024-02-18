import OpenDartReader
import os
import pandas as pd
import numpy as np
import pandas as pd
from lib import llm
import re
import lib.xml_parser as xp
from lib import database as db
import lib.company as cp
from dotenv import load_dotenv

load_dotenv(verbose=True)
api_key =  os.getenv("DART_API_KEY")

dart = OpenDartReader(api_key)

def check_nan(num) :
    if np.isnan(num) :
        return 0
    else :
        return int(num // 1000000)

def find_financial_indicators(stock_name, year, indicators) :
    try :
        report = dart.finstate(stock_name, year)
        if report is None :
            data = [[stock_name, year] + [np.nan] * len(indicators)]
            data = [[stock_name, year-1] + [np.nan] * len(indicators)]
            data = [[stock_name, year-2] + [np.nan] * len(indicators)]

            return pd.DataFrame(data, columns = ["기업", "연도"] + indicators)
    
        else :
            report = report.loc[report['account_nm'].isin(indicators)]
            if sum(report['fs_nm'] == "연결재무제표") > 0 :
                report = report.loc[report['fs_nm'] == "연결재무제표"]
            else :
                report = report.loc[report['fs_nm'] == "재무제표"]
        
            data = []
            for y, c in zip([year, year-1, year-2], ['thstrm_amount', 'frmtrm_amount', 'bfefrmtrm_amount']) :
                record = [stock_name, y]
                for indic in indicators :
                    if sum(report['account_nm'] == indic) > 0 :
                        value = report.loc[report['account_nm'] == indic, c].iloc[0]
                    else :
                        value = np.nan
                
                    record.append(value)
            
                data.append(record)
        
            return pd.DataFrame(data, columns = ["기업", "연도"] + indicators)
    except :
        pass

indicators = ['자산총계', '부채총계', '자본총계', '매출액', '영업이익', '당기순이익']

def str_to_float(value) :
    if type(value) == float :
        return value
    elif value == '-' :
        return 0
    else :
        return float(value.replace(',', ''))

def calculate_stat(data) :
    try:
        for indc in indicators :
            data[indc] = data[indc].apply(str_to_float)
        data.sort_values(by = ['기업', '연도'], inplace = True)

        return data
    
    except :
        return pd.DataFrame(columns = ["기업", "연도"] + indicators)

def get_fin_state(corp_name, year) :
    data = find_financial_indicators(corp_name, year, indicators)
    return calculate_stat(data).loc[:,["연도", "자본총계", "자산총계", "영업이익", "매출액", "당기순이익"]]

def get_BalanceSheet(fin_state, current_year) :
    financial_info = {current_year-3: [], current_year-2: [], current_year-1: []}
    if len(fin_state) >= 3 :
        year = [2, 1, 0]
        for i in year:
            total_equity = check_nan(fin_state.iloc[i]['자본총계'])
            total_assets = check_nan(fin_state.iloc[i]['자산총계'])
            profit = check_nan(fin_state.iloc[i]['매출액'])
            revenue = check_nan(fin_state.iloc[i]['영업이익'])
            net_income = check_nan(fin_state.loc[i]['당기순이익'])
            financial_info[2022-i] = [total_equity, total_assets, profit, revenue, net_income]
    
    return financial_info

def get_corp_info(corp_list, num, connection) :
    corp = [dict(), dict(), dict()]
    checked = ''
    failed = ''
    cnt = num
    for i in range(5) :
        corp_code = cp.comp_code(corp_list[i])
        context2_1 = "None"
        result2_1 = "None"
        date = "None"
        financial_info = dict()
        current_year = 2023
        if corp_code != "00000000" and cnt < 3:
            rcpt_num = cp.get_rpt_code(str(corp_code))
            if rcpt_num != "none" :
                context2_1 = xp.comp_info(rcpt_num)
                date = str(rcpt_num)[0:8]
                current_year = int(date[0:4])
                
        if db.firm_exists(corp_code, connection) and cnt < 3 and date == re.sub(r'-', '', str(db.get_update(corp_code, connection))):
            result2_1 = db.get_outline(corp_code, connection)
            financial_info = db.get_finance(corp_code, connection)
            roe = round(financial_info[current_year-1][4] / financial_info[current_year-1][0] * 100, 2)
            roa = round(financial_info[current_year-1][4] / financial_info[current_year-1][1] * 100, 2)
            debt_ratio = round((financial_info[current_year-1][1] - financial_info[current_year-1][0]) / financial_info[current_year-1][1] * 100, 2)
            result2_1 = result2_1 + '\nROE : ' + str(roe) + '%\nROA : ' + str(roa) + '%\n부채비율 : ' + str(debt_ratio)
            corp[cnt] = {'name': corp_list[i], 'article': result2_1, 'data' : financial_info}
            cnt = cnt + 1
            checked = checked + corp_list[i] + ' '
        elif corp_code != "00000000" and cnt < 3 and rcpt_num != "none":
            financial_info = {current_year-3: [], current_year-2: [], current_year-1: []}
            question2_2 = "해당 사업의 개요를 5가지로 요약해줘"
            result2_1 = llm.get_llm_result(context2_1, question2_2)
            result2_1 = re.sub(r'\*', '', result2_1)
            fin_state = get_fin_state(corp_list[i], current_year-1)
            if len(fin_state) >= 3 :
                financial_info = get_BalanceSheet(fin_state, current_year)

            if len(financial_info[current_year-1]) != 0:
                db.update_db(corp_code, corp_list[i], date, result2_1, financial_info, connection)
                roe = round(financial_info[current_year-1][4] / financial_info[current_year-1][0] * 100, 2)
                roa = round(financial_info[current_year-1][4] / financial_info[current_year-1][1] * 100, 2)
                debt_ratio = round((financial_info[current_year-1][1] - financial_info[current_year-1][0]) / financial_info[current_year-1][1] * 100, 2)
                result2_1 = result2_1 + '\nROE : ' + str(roe) + '%\nROA : ' + str(roa) + '%\n부채비율 : ' + str(debt_ratio)
                corp[cnt] = {'name': corp_list[i], 'article': result2_1, 'data' : financial_info}
                cnt = cnt + 1
                checked = checked + corp_list[i] + ' '
            else : 
                failed = failed + corp_list[i] + ' '
        else :
            failed = failed + corp_list[i] + ' '
    return {'corp': corp, 'checked' : checked, 'failed' : failed, 'cnt' : cnt}