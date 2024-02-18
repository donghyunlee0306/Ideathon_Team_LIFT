import datetime
import lib.sector as sc

"""
Database initialize / reset 모듈

db에 들어가는 table인 firm, finance, outline을 생성하고, 
DART에 상장된 기업들의 기업 코드, 기업명, 산업 분야를 firm table에 입력한다.
"""

def initialize_db(connection):
    TABLES = {}
    TABLES['firm'] = (
        "CREATE TABLE IF NOT EXISTS `firm` ("
        "   `firm_ID` INT NOT NULL,"
        "   `firm_name` VARCHAR(255) NOT NULL,"
        "   `sector` VARCHAR(255),"
        "   `recent_update` DATE,"
        "   PRIMARY KEY (`firm_ID`)"
        ") ENGINE = InnoDB"
    )
    TABLES['finance'] = (
        "CREATE TABLE IF NOT EXISTS `finance` ("
        "   `firm_ID` INT NOT NULL,"
        "   `year` INT NOT NULL,"
        "   `total_equity` BIGINT," # 자본총계
        "   `total_assets` BIGINT," # 자산총계
        "   `revenue` BIGINT," # 매출액
        "   `profit` BIGINT," # 영업이익
        "   `net_income` BIGINT," # 당기순이익
        "   PRIMARY KEY (`firm_ID`, `year`),"
        "   CONSTRAINT `finance_ibfk_1` FOREIGN KEY (`firm_ID`)"
        "       REFERENCES `firm` (`firm_ID`) ON DELETE CASCADE"
        ") ENGINE = InnoDB"
    )
    TABLES['outline'] = (
        "CREATE TABLE IF NOT EXISTS `outline` ("
        "   `firm_ID` INT NOT NULL,"
        "   `outline` VARCHAR(4095),"
        "   PRIMARY KEY (`firm_ID`),"
        "   CONSTRAINT `outline_ibfk_1` FOREIGN KEY (`firm_ID`)"
        "       REFERENCES `firm` (`firm_ID`) ON DELETE CASCADE"
        ") ENGINE = InnoDB"
    )

    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")
    for table_name in TABLES.keys():
        cursor.execute(TABLES[table_name])

    cnt = 0

    initialize_info = sc.get_sector()
    for dict in initialize_info:
        firm_ID = dict['corp_code']
        name = dict['corp_name']
        sector = dict['sector']

        query = "INSERT INTO firm (firm_ID, firm_name, sector) VALUES (%s, %s, %s)"
        cursor.execute(query, (firm_ID, name, sector))

        cnt += 1
        if cnt % 500 == 0:
            connection.commit()
        
    connection.commit()
    cursor.close()

def reset_db(connection):
    if input('Are you sure? (y/n): ') != 'y':
        return

    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")
    cursor.execute("DROP TABLE IF EXISTS outline")
    cursor.execute("DROP TABLE IF EXISTS finance")
    cursor.execute("DROP TABLE IF EXISTS firm")
    cursor.close()

    initialize_db(connection)

"""
백엔드에서 사용하는 모듈
"""

"""
Database update 모듈

기업 코드, 기업명, 최신 사업보고서 날짜, 사업개요, 재무 관련 지표를 입력받아 db에 업데이트한다.
- 해당 기업이 db에 존재하지 않을 때는 firm, finance, outline에 모두 insert (실제 백엔드에서 생기면 안되는 일)
- 해당 기업이 db에 존재하고, 최신 사업보고서 날짜가 firm table의 recent_update와 일치하면 업데이트하지 않음 (실제 백엔드에서 생기면 안되는 일)
- 해당 기업이 db에 존재하지만, recent_update가 null이거나 최신 사업보고서 날짜와 다를 때 firm, finance, outline 모두 update

Arguments
    firm_ID: corp code (기업 코드)
    name: corp name (기업 이름)
    update_date: 사업 보고서 날짜. 입력 형식: string ex) "20240216"
    outline: 사업 개요 요약
    financial_info: 각 연도에 따른 지표들. 입력 형식: dictionary ex) {연도:[지표 list], 연도:[지표 list], ...}
"""

def insert_firm(firm_ID, name, update_date, cursor):
    query = "INSERT INTO firm (firm_ID, firm_name, recent_update) VALUES (%s, %s, %s)"
    cursor.execute(query, (firm_ID, name, update_date))

def update_firm(firm_ID, update_date, cursor):
    query = "UPDATE firm SET recent_update = %s WHERE firm_ID = %s"
    cursor.execute(query, (update_date, firm_ID))

def insert_outline(firm_ID, outline, cursor):
    query = "INSERT INTO outline VALUES (%s, %s)"
    cursor.execute(query, (firm_ID, outline))

def update_outline(firm_ID, outline, cursor):
    query = "UPDATE outline SET outline = %s WHERE firm_ID = %s"
    cursor.execute(query, (outline, firm_ID))

def insert_finance(firm_ID, year, info_list, cursor):
    if len(info_list) == 0:
        query = "INSERT INTO finance(firm_ID, year) VALUES (%s, %s)"
        cursor.execute(query, (firm_ID, year))
    
    else:
        total_equity = info_list[0]
        total_assets = info_list[1]
        revenue = info_list[2]
        profit = info_list[3]
        net_income = info_list[4]

        query = "INSERT INTO finance VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor.execute(query, (firm_ID, year, total_equity, total_assets, revenue, profit, net_income))

def update_finance(firm_ID, year, info_list, cursor):
    if len(info_list) == 0:
        query = (
            "UPDATE finance"
            "   SET total_equity = NULL, total_assets = NULL, revenue = NULL, profit = NULL, net_income = NULL"
            "   WHERE firm_ID = %s AND year = %s"
        )
        cursor.execute(query, (firm_ID, year))
        
    else:
        total_equity = info_list[0]
        total_assets = info_list[1]
        revenue = info_list[2]
        profit = info_list[3]
        net_income = info_list[4]

        query = (
            "UPDATE finance"
            "   SET total_equity = %s, total_assets = %s, revenue = %s, profit = %s, net_income = %s"
            "   WHERE firm_ID = %s AND year = %s"
        )
        cursor.execute(query, (total_equity, total_assets, revenue, profit, net_income, firm_ID, year))

def delete_finance(firm_ID, year, cursor):
    query = "DELETE FROM finance WHERE firm_ID = %s AND year = %s"
    cursor.execute(query, (firm_ID, year))

def update_db(firm_ID, name, update_date, outline, financial_info, connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")
    
    update_date = datetime.date(int(update_date[0:4]), int(update_date[4:6]), int(update_date[6:8]))
    select_query = "SELECT recent_update FROM firm WHERE firm_ID = %s"
    cursor.execute(select_query, (firm_ID,))
    date = cursor.fetchall()

    if len(date) > 0:
        if date[0]['recent_update'] == update_date:
            print(f"Firm {firm_ID} is already updated.")

            # outline, finance에 해당 기업에 대한 정보가 없으면 insert
            cursor.execute("SELECT * FROM outline WHERE firm_ID = %s", (firm_ID,))
            result1 = cursor.fetchall()

            cursor.execute("SELECT * FROM outline WHERE firm_ID = %s", (firm_ID,))
            result2 = cursor.fetchall()

            if (len(result1) == 0) or (len(result2) == 0):
                if len(result1) == 0:
                    insert_outline(firm_ID, outline, cursor)
                
                if len(result2) == 0:
                    for year in financial_info.keys():
                        insert_finance(firm_ID, year, financial_info[year], cursor)

                connection.commit()
        
        else:
            # firm update
            update_firm(firm_ID, update_date, cursor)
            
            # outline에 해당 기업 정보 있으면 update, 없으면 insert
            cursor.execute("SELECT * FROM outline WHERE firm_ID = %s", (firm_ID,))
            result = cursor.fetchall()

            if len(result) == 0:
                insert_outline(firm_ID, outline, cursor)

            else:
                update_outline(firm_ID, outline, cursor)

            # finance에 해당 기업 정보 있으면 insert/update/delete, 없으면 insert
            cursor.execute("SELECT year FROM finance WHERE firm_ID = %s", (firm_ID,))
            result = cursor.fetchall()

            if len(result) == 0:
                for year in financial_info.keys():
                    insert_finance(firm_ID, year, financial_info[year], cursor)

            else:
                year_before = [x['year'] for x in result]
                year_after = list(financial_info.keys())

                year_insert = [x for x in year_after if x not in year_before]
                year_update = [x for x in year_after if x in year_before]
                year_delete = [x for x in year_before if x not in year_after]

                for year in year_insert:
                    insert_finance(firm_ID, year, financial_info[year], cursor)
                for year in year_update:
                    update_finance(firm_ID, year, financial_info[year], cursor)
                for year in year_delete:
                    delete_finance(firm_ID, year, cursor)

            connection.commit()
    
    else:
        insert_firm(firm_ID, name, update_date, cursor)
        insert_outline(firm_ID, outline, cursor)
        for year in financial_info.keys():
            insert_finance(firm_ID, year, financial_info[year], cursor)  

        connection.commit()

    cursor.close()

"""
Get Sectors 모듈

db에 저장되어 있는 모든 사업 분야를 반환한다.
Return Type: list ex) [분야1, 분야2, ...]
"""
def get_sectors(connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")
    cursor.execute("SELECT distinct sector FROM firm")
    result = cursor.fetchall()
    cursor.close()
    return [x['sector'] for x in result if x['sector'] != None]

"""
Get Firms 모듈

사업 분야의 list를 입력받고, 해당하는 사업 분야의 기업들의 기업명 list를 반환한다.
Argument: sector_list (사업 분야 list)
Return Type: list ex) [기업명1, 기업명2, ...]
"""
def get_firms(sector_list, connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")

    firm_list = []
    for sector in sector_list:
        query = "SELECT firm_name FROM firm WHERE sector = %s"
        cursor.execute(query, (sector,))
        firm_list.extend([x['firm_name'] for x in cursor.fetchall()])
    
    cursor.close()
    return firm_list

"""
Firm Exists 모듈

해당 기업 코드의 기업이 db에 존재하는지 확인한다.
Argument: firm_ID (기업 코드)
Return Type: boolean
"""
def firm_exists(firm_ID, connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")

    query = "SELECT * FROM firm WHERE firm_ID = %s"
    cursor.execute(query, (firm_ID,))
    result = cursor.fetchall()

    cursor.close()
    return len(result) > 0

"""
Get Update Date 모듈

해당 기업의 recent_update를 반환한다.

Argument: firm_ID (기업 코드)
Return Type: date (단, recent_update가 NULL인 경우 빈 문자열 반환)
"""
def get_update(firm_ID, connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")

    query = "SELECT recent_update FROM firm WHERE firm_ID = %s"
    cursor.execute(query, (firm_ID,))
    result = cursor.fetchall()

    cursor.close()

    if len(result) == 0:
        return ""
    else:
        return result[0]['recent_update']

"""
Get Outline 모듈

해당 기업의 사업 개요 반환한다.
Argument: firm_ID (기업 코드)
Return Type: string
"""
def get_outline(firm_ID, connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")

    query = "SELECT outline FROM outline WHERE firm_ID = %s"
    cursor.execute(query, (firm_ID,))
    result = cursor.fetchall()

    cursor.close()

    outline = result[0]['outline']
    return outline

"""
Get Finance 모듈

해당 기업의 연도에 따른 지표를 반환한다.
Argument: firm_ID (기업 코드)
Return Type: dictionary. ex) {연도: [지표 list], 연도: [지표 list], ... }
"""
def get_finance(firm_ID, connection):
    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")

    query = "SELECT * FROM finance WHERE firm_ID = %s"
    cursor.execute(query, (firm_ID,))
    result = cursor.fetchall()

    cursor.close()

    finance_info = {}
    for dict in result:
        finance_info[dict['year']] = [dict['total_equity'], dict['total_assets'], dict['revenue'], dict['profit'], dict['net_income']]
    return finance_info

"""
예비용 모듈
"""

"""
Delete Firm 모듈

해당 기업의 정보를 firm, outline, finance table에서 전부 제거한다.
"""
def delete_firm(firm_ID, connection):
    if not firm_exists(firm_ID, connection):
        print(f"Firm {firm_ID} does not exist.")
        return

    cursor = connection.cursor(dictionary=True)
    cursor.execute("USE lift")

    query = "DELETE FROM firm WHERE firm_ID = %s"
    cursor.execute(query, (firm_ID,))

    connection.commit()
    cursor.close()

# Insert & Update를 각 table마다 할 수 있도록 모듈화가 필요할까?

