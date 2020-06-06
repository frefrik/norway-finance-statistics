import json
import pandas as pd
import requests
from datetime import date, timedelta, datetime
from os import path

def write_df(desc, df):
    caller = desc
    df.to_csv('./data/no_' + caller + '.csv', encoding='utf-8', index=False)
    try:
        print('DataFrame updated: {}'.format(caller))
    except:
        pass

def get_dates(lastdate):
    date_today = date.today()
    delta_date = date_today - timedelta(days=(date_today - lastdate).days)
    delta_days = (date_today - lastdate).days

    return date_today, delta_date, delta_days

def nibor():
    if path.exists('./data/no_nibor_panel.csv') == True:
        df_panel = pd.read_csv('./data/no_nibor_panel.csv', parse_dates=['Date'])
        date_last = max(df_panel['Date']).date() + timedelta(days=1)
    else:
        df_panel = pd.DataFrame()
        date_last = datetime(2020, 1, 1).date()
        df_hms = pd.read_excel('https://www.norges-bank.no/globalassets/marketdata/hms/data/nibor.xlsx', sheet_name='Daily', skiprows=6, usecols='A,C,E:H')
        df_hms.rename(columns={'Unnamed: 0':'Date',
                            '1 week':'1 Week',
                            '1 month':'1 Month',
                            '2 month':'2 Months',
                            '3 month':'3 Months',
                            '6 month':'6 Months'}, 
                         inplace=True)
        df_hms = df_hms.loc[(df_hms['Date'] > '1986-01-01') & (df_hms['Date'] <= '2013-12-06')].iloc[::-1]

    delta = get_dates(date_last)

    if delta[2] > 0:
        for i in range(delta[2]):
            day = date_last + timedelta(days=i)
            res = requests.post('https://rates.referanserenter.no/submit.php', data={'market':'NIBOR', 'date':day})
            load = json.loads(res.content)

            if load['status'] == 'ok':
                print(day, 'Fetching new data')
                array = load['results']
                df_panel_new = pd.DataFrame(array)
                df_panel_new.insert(0, "Date", day)
                df_panel = df_panel.append(df_panel_new)
            elif load['message'] == 'Invalid request date':
                print(day, 'No rates published on this date, skipping')
                pass
            else:
                print(day, 'Unknown error, skipping')
                pass
        
        df_panel['Date'] = pd.to_datetime(df_panel['Date'])
        df_fixed = df_panel.pivot(index='Date', columns='Tenor', values='Fixing Rate').reset_index()
        df_fixed = df_fixed.reindex(columns=['Date','1 Week','1 Month','2 Months', '3 Months', '6 Months']).rename_axis(None, axis=1)

        if date_last == date(2020, 1, 1):
            df_fixed = df_fixed.append(df_hms, ignore_index=True)
            df_fixed = df_fixed.sort_values(by='Date', ignore_index=True)

        write_df('nibor', df_fixed)
        write_df('nibor_panel', df_panel)
    else:
        print('Data already up to date: nibor')

def keyPolicyRate():
    if path.exists('./data/no_keyPolicyRate.csv') == True:
        df = pd.read_csv('./data/no_keyPolicyRate.csv', parse_dates=['Date'])
        date_last = max(df['Date']).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(1991, 1, 1).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        df_new = pd.read_csv('https://data.norges-bank.no/api/data/IR/B.KPRA.SD.?format=csv&startPeriod={}&endPeriod={}&locale=en'.format(delta[1], delta[0]),
                            parse_dates=['TIME_PERIOD'],
                            delimiter=';',
                            thousands=',',
                            usecols=['TIME_PERIOD','OBS_VALUE'])

        df_new.rename(columns={'TIME_PERIOD':'Date',
                            'OBS_VALUE':'Rate'}, 
                         inplace=True)

        df = df.append(df_new, ignore_index=True)
        write_df('keyPolicyRate', df)
    else:
        print('Data already up to date: keyPolicyRate')

def nowa():
    if path.exists('./data/no_nowa.csv') == True:
        df = pd.read_csv('./data/no_nowa.csv', parse_dates=['Date'])
        date_last = max(df['Date']).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(2011, 9, 30).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        df_new = pd.read_csv('https://data.norges-bank.no/api/data/IR/B.NOWA..?format=csv&startPeriod={}&endPeriod={}&locale=en'.format(delta[1], delta[0]),
                        parse_dates=['TIME_PERIOD'],
                        delimiter=';',
                        thousands=',',
                        usecols=['TIME_PERIOD',
                                'Unit of Measure',
                                'OBS_VALUE',
                                'Calculation Method'])

        df_new.rename(columns={'TIME_PERIOD':'Date',
                                'OBS_VALUE': 'Value',
                                'Calculation Method': 'Qualifier'},
                     inplace=True)
                     
        qualifier = df_new[['Date', 'Qualifier']].loc[df_new['Unit of Measure'] == 'Rate']
        df_pivot = pd.pivot_table(df_new, index='Date', columns='Unit of Measure', values='Value')
        df_new = pd.merge(df_pivot, qualifier, how='right', on=['Date'])
        df_new = df_new.reindex(columns=['Date','Rate','Volume','Qualifier','Banks lending', 'Banks borrowing', 'Transactions']).replace('Alternative method', 'Alternative').fillna(0)
        
        df = df.append(df_new, ignore_index=True)
        write_df('nowa', df)
    else:
        print('Data already up to date: nowa')

def treasuryBills():
    if path.exists('./data/no_treasuryBills.csv') == True:
        df = pd.read_csv('./data/no_treasuryBills.csv', parse_dates=['Date'])
        date_last = max(df['Date']).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(2003, 1, 8).date()
    
    delta = get_dates(date_last)

    if delta[2] > 0:
        df_new = pd.read_csv('https://data.norges-bank.no/api/data/IR/B.TBIL..?format=csv&startPeriod={}&endPeriod={}&locale=en'.format(delta[1], delta[0]),
                        parse_dates=['TIME_PERIOD'],
                        delimiter=';',
                        thousands=',',
                        usecols=['TIME_PERIOD',
                                'Tenor',
                                'OBS_VALUE'])

        df_new.rename(columns={'TIME_PERIOD':'Date',
                                'OBS_VALUE': 'Rate'},
                     inplace=True)

        df_new = pd.pivot_table(df_new, index='Date', columns='Tenor', values='Rate').reset_index()
        df_new = df_new.reindex(columns=['Date','3 months','6 months','9 months','12 months']).rename_axis(None, axis=1)

        df = df.append(df_new, ignore_index=True)
        write_df('treasuryBills', df)
    else:
        print('Data already up to date: treasuryBills')

def governmentBonds():
    if path.exists('./data/no_governmentBonds.csv') == True:
        df = pd.read_csv('./data/no_governmentBonds.csv', parse_dates=['Date'])
        date_last = max(df['Date']).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(1986, 1, 3).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        df_new = pd.read_csv('https://data.norges-bank.no/api/data/IR/B.GBON..?format=csv&startPeriod={}&endPeriod={}&locale=en'.format(delta[1], delta[0]),
                        parse_dates=['TIME_PERIOD'],
                        delimiter=';',
                        thousands=',',
                        usecols=['TIME_PERIOD',
                                'Tenor',
                                'OBS_VALUE'])

        df_new.rename(columns={'TIME_PERIOD':'Date',
                                'OBS_VALUE': 'Rate'},
                     inplace=True)

        df_new = pd.pivot_table(df_new, index='Date', columns='Tenor', values='Rate').reset_index()
        df_new = df_new.reindex(columns=['Date','3 years','5 years','10 years']).rename_axis(None, axis=1)

        df = df.append(df_new, ignore_index=True)

        write_df('governmentBonds', df)
    else:
        print('Data already up to date: governmentBonds')

def exchangeRates():
    if path.exists('./data/no_exchangeRates.csv') == True:
        df = pd.read_csv('./data/no_exchangeRates.csv', parse_dates=['Date'])
        date_last = max(df['Date']).date() + timedelta(days=1)
    else:
        df = pd.DataFrame()
        date_last = datetime(1980, 12, 10).date()

    delta = get_dates(date_last)

    if delta[2] > 0:
        df_new = pd.read_csv('https://data.norges-bank.no/api/data/EXR/B..NOK.SP?format=csv&startPeriod={}&endPeriod={}&locale=en'.format(delta[1], delta[0]),
                        parse_dates=['TIME_PERIOD'],
                        delimiter=';',
                        thousands=',',
                        usecols=['TIME_PERIOD',
                                'BASE_CUR',
                                'QUOTE_CUR',
                                'OBS_VALUE'])

        df_new.rename(columns={'TIME_PERIOD': 'Date',
                                'BASE_CUR': 'Base Currency',
                                'QUOTE_CUR': 'Quote Currency',
                                'OBS_VALUE': 'Rate'},
                     inplace=True)

        df_new = pd.pivot_table(df_new, index=['Date', 'Quote Currency'], columns='Base Currency', values='Rate').reset_index().rename_axis(None, axis=1)

        df = df.append(df_new, ignore_index=True)

        write_df('exchangeRates', df)
    else:
        print('Data already up to date: exchangeRates')

if __name__ == '__main__':
    nibor()
    keyPolicyRate()
    nowa()
    treasuryBills()
    governmentBonds()
    exchangeRates()