def get_dart_finance(corp_code, corp_name):

    import OpenDartReader

    import pandas as pd
    import matplotlib.pyplot as plt
    import seaborn as sns
    import yfinance as yf
    import numpy as np
    import os

    import warnings
    warnings.filterwarnings("ignore")

    import matplotlib as mpl
    mpl.rc('font', family='Malgun Gothic')
    mpl.rc('axes', unicode_minus=False)

    api_key = ' ebb8f1391a48f6766cb70f3616e901e630e51939'  #25년 5월 31일 업데잇
    dart = OpenDartReader(api_key)


    #원하는 회사의 종목코드와 회사명 입력하기
    # corp_code ='005930'
    # corp_name='삼성전자'


    path = r"D:\python_PJT\01_Data_Mart_생성\05_종목별_Data"

    folder_list=os.listdir(path)

    # corp_name이 폴더리스트에 없으면 폴더 만들기
    if corp_name not in folder_list:
        os.makedirs(os.path.join(path, corp_name))

    folder_path = os.path.join(path, corp_name)
    print(f'폴더의 위치는{folder_path} 입니다.')

    # 지정한 회사의 재무제표를 fin_list에 담기

    fin_list=[] # 재무제표를 담을 리스트
    index_code=[] #인덱스에 사용할 년, 보고서 종류 담기
    year=list(range(2015,2026))
    rep_code = ['11013', '11012', '11014', '11011']

    for yr in year:
        for rp in rep_code:
            df_t=dart.finstate_all(corp_code, yr, reprt_code=rp)
            if not df_t.empty:
                fin_list.append(df_t)
                index_code.append(str(yr)+'_'+rp)
    
    #손익계산서 리스트로 모으기
    ic_list=[]  #손익계산서 list
    for i in range(len(fin_list)):
        df_t =fin_list[i][ fin_list[i]['sj_nm'].isin(['포괄손익계산서', '손익계산서'])]
        df_t =df_t[['account_nm', 'thstrm_amount','bsns_year','reprt_code']]
        # df_t.index=df_t['account_nm']
        # df_t.drop(columns=['account_nm'], inplace=True)
        ic_list.append(df_t)

    df_income = pd.concat(ic_list, ignore_index=True)

    #계정명을 표준계정명으로 변경하고, Filtering할 파일 만들기
    df_std= pd.read_excel(r'D:\python_PJT\01_Data_Mart_생성\02_Open_dart\income_nm_std.xlsx')
    df_std.dropna(axis=0, inplace=True)
    account_std_map=dict(zip(df_std['original'],df_std['std']))
    interest_items=list(set(account_std_map.values()))
    pattern = '|'.join(interest_items)
    

    #표준계정명으로 변경, 날짜 변경하기
    df_income['account_nm_std'] = df_income['account_nm'].replace(account_std_map)
    reprt_code_std = {'11011':'12-31','11013':'03-31', '11012':'06-30', '11014':'09-30'}
    df_income['reprt_code_std'] = df_income['reprt_code'].replace(reprt_code_std)
    df_income['issue_date'] = df_income['bsns_year'] + str('-') + df_income['reprt_code_std'] 
    df_income['issue_date']=pd.to_datetime(df_income['issue_date'])


    #계정명 빈칸 없애기, 수정을 위해 account_nm 엑셀 활용
    df_income['account_nm'] = df_income['account_nm'].str.strip().str.replace(' ', '', regex=False)

    # 원하는 계정명만 필터링하기
    df_income=df_income[df_income['account_nm_std'].isin(interest_items)]

    # 피벗테이블을 이용해 다시 정리하기
    df_pivot = df_income.pivot_table(
        index='issue_date',
        columns='account_nm_std',
        values='thstrm_amount',
        aggfunc='first'  # 또는 sum, mean 등 상황에 따라 선택
    )

    # 문자열을 숫자열로 변경하기
    for name in df_pivot.columns:
        df_pivot[name] = pd.to_numeric(df_pivot[name])

    #12월 연간데이터를 분기 데이터로 변경하는 사용자 함수
    def december_data_change(df_pivot):
        for i,idx in zip(range(len(df_pivot)), df_pivot.index):
            if idx.month==12 and i>3:
                for j in range(len(df_pivot.columns)):
                    df_pivot.iloc[i,j] =df_pivot.iloc[i,j] -df_pivot.iloc[i-1,j] -df_pivot.iloc[i-2,j] -df_pivot.iloc[i-3,j] 
            elif idx.month==12 and i<2:
                for j in range(len(df_pivot.columns)):
                    df_pivot.iloc[i,j] = df_pivot.iloc[i,j]/4

    december_data_change(df_pivot)

    df_pivot.to_excel(f'{folder_path}\\{corp_name}_손익계산서.xlsx')

    #재무상태표 리스트로 모으기
    ic_list=[]  
    for i in range(len(fin_list)):
        df_t =fin_list[i][ fin_list[i]['sj_nm'] =='재무상태표']
        df_t =df_t[['account_nm', 'thstrm_amount','bsns_year','reprt_code']]
        # df_t.index=df_t['account_nm']
        # df_t.drop(columns=['account_nm'], inplace=True)
        ic_list.append(df_t)
    df_income = pd.concat(ic_list, ignore_index=True)
    df_income['account_nm'] = df_income['account_nm'].str.strip().str.replace(' ', '', regex=False)

    #계정명을 표준계정명으로 변경하고, Filtering할 파일 만들기

    df_std= pd.read_excel(r'D:\python_PJT\01_Data_Mart_생성\02_Open_dart\bal_nm_std.xlsx')
    account_std_map=dict(zip(df_std['original'],df_std['std']))
    interest_items=list(set(account_std_map.values()))
    pattern = '|'.join(interest_items)

    #표준계정명으로 변경, 날짜 변경하기
    df_income['account_nm_std'] = df_income['account_nm'].replace(account_std_map)
    reprt_code_std = {'11011':'12-31','11013':'03-31', '11012':'06-30', '11014':'09-30'}
    df_income['reprt_code_std'] = df_income['reprt_code'].replace(reprt_code_std)
    df_income['issue_date'] = df_income['bsns_year'] + str('-') + df_income['reprt_code_std'] 
    df_income['issue_date']=pd.to_datetime(df_income['issue_date'])

    # 원하는 계정명만 필터링하기
    df_income=df_income[df_income['account_nm_std'].isin(interest_items)]
    # 피벗테이블을 이용해 다시 정리하기
    df_pivot = df_income.pivot_table(
        index='issue_date',
        columns='account_nm_std',
        values='thstrm_amount',
        aggfunc='first'  # 또는 sum, mean 등 상황에 따라 선택
    )

    df_pivot
    # 문자열을 숫자열로 변경하기
    for name in df_pivot.columns:
        df_pivot[name] = pd.to_numeric(df_pivot[name])
        
    df_pivot.to_excel(f'{folder_path}\\{corp_name}_재무상태표.xlsx') #저장하기

    #현금흐름표 리스트로 모으기
    ic_list=[]  #손익계산서 list
    for i in range(len(fin_list)):
        df_t =fin_list[i][ fin_list[i]['sj_nm'] =='현금흐름표']
        df_t =df_t[['account_nm', 'thstrm_amount','bsns_year','reprt_code']]
        # df_t.index=df_t['account_nm']
        # df_t.drop(columns=['account_nm'], inplace=True)
        ic_list.append(df_t)
    df_income = pd.concat(ic_list, ignore_index=True)
    df_income['account_nm'] = df_income['account_nm'].str.strip().str.replace(' ', '', regex=False)

    df_income['account_nm'].unique()

    #계정명을 표준계정명으로 변경하고, Filtering할 파일 만들기
    df_std= pd.read_excel(r"D:\python_PJT\01_Data_Mart_생성\02_Open_dart\cash_nm_std.xlsx")
    account_std_map=dict(zip(df_std['original'],df_std['std']))
    interest_items=list(set(account_std_map.values()))
    pattern = '|'.join(interest_items)

    #표준계정명으로 변경, 날짜 변경하기
    df_income['account_nm_std'] = df_income['account_nm'].replace(account_std_map)
    reprt_code_std = {'11011':'12-31','11013':'03-31', '11012':'06-30', '11014':'09-30'}
    df_income['reprt_code_std'] = df_income['reprt_code'].replace(reprt_code_std)
    df_income['issue_date'] = df_income['bsns_year'] + str('-') + df_income['reprt_code_std'] 
    df_income['issue_date']=pd.to_datetime(df_income['issue_date'])

    # 원하는 계정명만 필터링하기
    df_income=df_income[df_income['account_nm_std'].isin(interest_items)]

    # 피벗테이블을 이용해 다시 정리하기
    df_pivot = df_income.pivot_table(
        index='issue_date',
        columns='account_nm_std',
        values='thstrm_amount',
        aggfunc='first'  # 또는 sum, mean 등 상황에 따라 선택
    )
    # 문자열을 숫자열로 변경하기
    for name in df_pivot.columns:
        df_pivot[name] = pd.to_numeric(df_pivot[name])
    #12월 연간데이터를 분기 데이터로 변경하는 사용자 함수
    def december_data_change(df_pivot):
        for i,idx in zip(range(len(df_pivot)), df_pivot.index):
            if idx.month==12 and i>3:
                for j in range(len(df_pivot.columns)):
                    df_pivot.iloc[i,j] =df_pivot.iloc[i,j] -df_pivot.iloc[i-1,j] -df_pivot.iloc[i-2,j] -df_pivot.iloc[i-3,j] 
            elif idx.month==12 and i<2:
                for j in range(len(df_pivot.columns)):
                    df_pivot.iloc[i,j] = df_pivot.iloc[i,j]/4

    december_data_change(df_pivot)
    df_pivot
    
    df_pivot.to_excel(f'{folder_path}\\{corp_name}_현금흐름표.xlsx')


if __name__ == "__main__":
    corp_name ='큐렉소'
    corp_code = '060280'  
    get_dart_finance(corp_code, corp_name)

