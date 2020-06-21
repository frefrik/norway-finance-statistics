import pandas as pd
import altair as alt
from os import path

def keyPolicyRate():
    print('Generating graph: keyPolicyRate ...', end='', flush=True)
    filename = './img/keyPolicyRate.png'

    if path.exists('./data/no_keyPolicyRate.csv') == True:
        df = pd.read_csv('./data/no_keyPolicyRate.csv', parse_dates=['Date'])

    chart = alt.Chart(df, title='Key policy rate, 1991 - 2020').mark_line().encode(
        x=alt.X('year(Date):O', title='Dato'),
        y=alt.Y('Rate:Q', title='Key policy rate')
    ).properties(
        width=1200,
        height=600
    )

    chart.save(filename)
    print('[OK]')

def nibor():
    print('Generating graph: NIBOR ...........', end='', flush=True)
    filename = './img/nibor.png'

    if path.exists('./data/no_nibor.csv') == True:
        df = pd.read_csv('./data/no_nibor.csv', parse_dates=['Date'])

    df = df.melt(id_vars=['Date'], var_name='Tenor', value_name='Rate')
    df = df[df.Date >= '2020-01-02'].dropna()

    chart = alt.Chart(df, title='NIBOR - YTD (2020)').mark_line().encode(
        x=alt.X('monthdate(Date):T', title='Date'),
        y=alt.Y('Rate:Q', title='Rate',
                scale=alt.Scale(zero=False),
                axis=alt.Axis(orient='right', format='.2f')),
        color=alt.Color('Tenor', legend=alt.Legend(orient='left'))
    ).properties(
        width=1200,
        height=600
    )

    chart.save(filename)
    print('[OK]')

def nibor_panel_3m():
    print('Generating graph: NIBOR_panel_3m ..', end='', flush=True)
    filename = './img/nibor_panel_3m.png'
    
    if path.exists('./data/no_nibor_panel.csv') == True:
        df = pd.read_csv('./data/no_nibor_panel.csv', parse_dates=['Date'], index_col=['Date'], usecols=['Date', 'Tenor', 'DNBB', 'DSKE', 'HAND', 'NORD', 'SEBB', 'SWED'])
    
    df = df.loc[df['Tenor'] == '3 Months'].last('60D').reset_index()
    df = df.melt(id_vars=['Date', 'Tenor'], var_name='Bank', value_name='Rate').dropna()

    chart = alt.Chart(df, title='NIBOR Panel Banks (3 Months) - Last 60 days').mark_line().encode(
        x=alt.X('monthdate(Date):T', title='Date'),
        y=alt.Y('Rate:Q', title='Rate',
                scale=alt.Scale(zero=False),
                axis=alt.Axis(orient='right', format='.2f')),
        color=alt.Color('Bank', legend=alt.Legend(orient='left'))
    ).properties(
        width=1200,
        height=600
    )

    chart.save(filename)
    print('[OK]')

def exchangeRates():
    print('Generating graph: exchangeRates ...', end='', flush=True)
    filename = './img/exchangeRates.png'

    if path.exists('./data/no_exchangeRates.csv') == True:
        df = pd.read_csv('./data/no_exchangeRates.csv', parse_dates=['Date'])

    df = df.melt(id_vars=['Date', 'Quote Currency'], value_vars=['EUR', 'USD', 'GBP'], var_name='Currency', value_name='Rate')
    df = df[df.Date >= '2020-01-01']

    chart = alt.Chart(df, title='Exchange Rates - YTD (2020)').mark_line().encode(
        x=alt.X('monthdate(Date):T', title='Date'),
        y=alt.Y('Rate:Q', title='Rate',
                scale=alt.Scale(zero=False),
                axis=alt.Axis(orient='right')),
        color=alt.Color('Currency', legend=alt.Legend(orient='left'))
    ).properties(
        width=1200,
        height=600
    )

    chart.save(filename)
    print('[OK]')

def treasuryBills():
    print('Generating graph: treasuryBills ...', end='', flush=True)
    filename = './img/treasuryBills.png'

    if path.exists('./data/no_treasuryBills.csv') == True:
        df = pd.read_csv('./data/no_treasuryBills.csv', parse_dates=['Date'])

    df = df.melt(id_vars=['Date'], var_name='Tenor', value_name='Rate')
    df = df[df.Date >= '2020-01-01']

    chart = alt.Chart(df, title='Treasury bills - YTD (2020)').mark_line().encode(
        x=alt.X('monthdate(Date):T', title='Date'),
        y=alt.Y('Rate:Q', title='Rate',
                scale=alt.Scale(zero=False),
                axis=alt.Axis(orient='right')),
        color=alt.Color('Tenor', legend=alt.Legend(orient='left'))
    ).properties(
        width=1200,
        height=600
    )

    chart.save(filename)
    print('[OK]')

def governmentBonds():
    print('Generating graph: governmentBonds .', end='', flush=True)
    filename = './img/governmentBonds.png'

    if path.exists('./data/no_governmentBonds.csv') == True:
        df = pd.read_csv('./data/no_governmentBonds.csv', parse_dates=['Date'])

    df = df.melt(id_vars=['Date'], var_name='Tenor', value_name='Rate')
    df = df[df.Date >= '2020-01-01']

    chart = alt.Chart(df, title='Government bonds - YTD (2020)').mark_line().encode(
        x=alt.X('monthdate(Date):T', title='Date'),
        y=alt.Y('Rate:Q', title='Rate',
                scale=alt.Scale(zero=False),
                axis=alt.Axis(orient='right')),
        color=alt.Color('Tenor', legend=alt.Legend(orient='left'))
    ).properties(
        width=1200,
        height=600
    )

    chart.save(filename)
    print('[OK]')

if __name__ == "__main__":
    keyPolicyRate()
    nibor()
    nibor_panel_3m()
    exchangeRates()
    treasuryBills()
    governmentBonds()