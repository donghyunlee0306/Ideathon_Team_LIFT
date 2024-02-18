import requests
import zipfile
import xml.etree.ElementTree as ET
import os
import re
import shutil
import dart_fss as dart
from dotenv import load_dotenv

load_dotenv(verbose=True)

api_key =  os.getenv("DART_API_KEY")
url = 'https://opendart.fss.or.kr/api/document.xml'

def request_data(rcept_no) :
    params = {
        'crtfc_key' : api_key,
        'rcept_no' : rcept_no,
    }
    output_dir = 'data/searched_data/' + rcept_no
    res = requests.get(url, params)

    if res.status_code==200:
        with open('report.zip',  'wb') as  file:
            file.write(res.content) 

    file_name = "./report.zip"

    if os.path.exists(output_dir):
        pass
    else:
        with zipfile.ZipFile(file_name, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
            file_list = zip_ref.namelist()
            for file in file_list:
                with open(f'{output_dir}/{file}', 'r', encoding='utf-8') as fp:
                    lines = fp.readlines()
                lines = [x.replace('&',  '&amp;') for x in lines]
                pattern_l = re.compile(r'<[가-힣]')
                lines = [re.sub(pattern_l, lambda x: ' &lt;' + x.group()[1:], line) for line in lines]
                pattern_r = re.compile(r'[가-힣]>')
                lines = [re.sub(pattern_r, lambda x: x.group()[1:] + '&gt; ', line) for line in lines]

                with open(f'{output_dir}/e_{file}', 'w',  encoding='utf-8') as fp:
                    fp.writelines(lines)

                os.remove(f'{output_dir}/{file}')
                shutil.move(f'{output_dir}/e_{file}', f'{output_dir}/{file}')


    file_path = f"{output_dir}/{rcept_no}.xml"

    return file_path


#xml 태그 제거
def remove_tags(text):
    cleaned_text = re.sub(r'<[^>]*>', '', text)

    return cleaned_text


#사업의 개요 - 주요 제품 및 서비스 부분 추출
def comp_info(rcept_no) :
    result = ''
    file_path = request_data(rcept_no)
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            xml_content = file.read()
            xml_content = remove_tags(xml_content)
            xml_content = re.sub(r'\n+', '\n ', xml_content)

            start_index = 0
            end_index = 0 

            for i in range(2):
                start_index = xml_content.find('\n 1. 사업의 개요\n', start_index)
                end_index = xml_content.find('\n 2. 주요 제품 및 서비스\n', end_index)

            result = xml_content[start_index:end_index]

    except FileNotFoundError:
        print(f"{file_path}를 찾을 수 없습니다.")
    except Exception as e:
        print(f"파일 열기 또는 XML 읽기 중 오류 발생: {e}")
    
    os.remove('report.zip')
    return result