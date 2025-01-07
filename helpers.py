import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from shiny import ui
from datetime import datetime, timedelta

from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


app_dir = Path(__file__).parent
DATA_FILE = app_dir / 'data.csv'

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

ACCOUNTS = ['sella', 'generali', 'generali_SAV', 'revolut_EUR', 'revolut_GBP']

CATEGORY_INCOME = ['salary', 'rent', 'transfer', 'refund', 'interests']
CATEGORY_EXPENSES = ['wants', 'needs', 'rent', 'bills', 'transfer', 'subscription', 'savings', 'interests']

ADD_TRANSACTION = {
    'date': ui.input_date(
        id='add_date',
        label='Date',
        format='dd/mm/yyyy',
        min=datetime.today() - timedelta(weeks=52),
        max=datetime.today(),
    ),
    'account':ui.input_select(
        id='add_account',
        label='Account',
        choices=ACCOUNTS,
    ),
   'category': ui.input_select(
        id='add_category',
        label='Category',
        choices=CATEGORY_INCOME + CATEGORY_EXPENSES
    ),
    'description': ui.input_text(
        id='add_description',
        label='Description',
        placeholder='e.g., dinner out'
    ),
    'currency': ui.input_radio_buttons(
        id='add_currency',
        label='',
        choices=['EUR', 'GBP'],
        inline=True
    ),
    'in': ui.input_numeric(
        id='add_in',
        label='Income',
        value=0.0
    ),
    'out': ui.input_numeric(
        id='add_out',
        label='Expenses',
        value=0.0
    ),
}

def import_data():
    try:
        ## import from csv file
        data = pd.read_csv(DATA_FILE)
        ## convert dates to datetime
        data['date'] = pd.to_datetime(data.date, dayfirst=True, errors='raise', format='mixed')#'%d/%m/%Y')
        data['year'] = data.date.dt.year
        data['month'] = data.date.dt.month
        data = data.sort_values(by='date', ascending=False)
        return data
    except Exception as e:
        print(f'Oops, something went wrong\nException: {e}')
        return None

def save_data_to_file(data):
    if 'month' in data.columns and 'year' in data.columns:
        data = data.drop(['month', 'year'], axis=1)
    try:
        data.to_csv(DATA_FILE, index=False)
        ui.notification_show('File saved', type='message')
    except Exception as e:
        ui.notification_show(f'Error while trying to save to file: {e}', type='error')

def calculate_total_wealth(data):
    wealth = []
    for account in data.account.unique():
        account_df = data[data.account == account]
        account_df = account_df.sort_values(['date'])
        account_df['in_out'] = account_df['in'] - data['out']
        account_df['balance'] = round(account_df.in_out.cumsum(),2)

        wealth.append((account_df.currency.iloc[-1], account_df.balance.iloc[-1]))
    
    total_eur = sum([item[1] for item in wealth if item[0]=='EUR'])
    total_gbp = sum(item[1] for item in wealth if item[0]=='GBP') * 1.19 #CurrencyRates().get_rate('GBP', 'EUR')

    return(total_eur + total_gbp)

def calculate_account_balance(data):
    balance = []
    for account in data.account.unique():
        account_df = data[data.account == account]
        account_df = account_df.sort_values(['date'])
        account_df['in_out'] = account_df['in'] - account_df['out']
        account_df['balance'] = round(account_df.in_out.cumsum(),2)

        balance.append((account_df.currency.iloc[-1], account_df.balance.iloc[-1], account))
    return balance

def calculate_monthly_category(data, year):
    def exchange_in_out(df):
        if df.currency == 'GBP':
            rate = 1.19
        else:
            rate = 1
        
        df['in'] = df['in'] * rate
        df['out'] = df['out'] * rate

        return df
    
    ## need to exchange everything to EUR and then do the calculations
    cat_df = data[(data.apply(exchange_in_out, axis=1).year==int(year)) & (data.apply(exchange_in_out, axis=1).account != 'generali_SAV')].groupby(['year','month','category']).agg({'in':'sum', 'out':'sum'}).reset_index()

    tmp = cat_df.groupby(['year','month'])['in'].sum().reset_index()
    tmp = tmp.rename(columns={'in':'total_income'})

    merged = pd.merge(left=cat_df, right=tmp)

    merged['pcg_in_out'] = (merged['in'] - merged['out'])/merged.total_income #* 100
    merged['pcg_in'] = merged['in']/merged.total_income
    merged['pcg_out'] = -merged['out']/merged.total_income

    return merged
