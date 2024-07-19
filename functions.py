import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

import warnings
warnings.filterwarnings('ignore')

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

def create_account_registry(filename):
    accounts = pd.read_excel(filename, sheet_name='accounts')

    return accounts

def create_main_in_out_df(filename):
    '''
    Import data from excel file and return the main dataframe

    year | month | account | category | description | date | currency | in | out
    '''
    incomes = pd.read_excel(filename, sheet_name='incomes')
    expenses = pd.read_excel(filename, sheet_name='expenses')

    expenses['out'] = expenses.amount
    incomes['in'] = incomes.amount

    df = pd.concat([incomes,expenses])
    df['month'] = df.date.dt.month
    df['year'] = df.date.dt.year

    return df.groupby(['year', 'month', 'account', 'category', 'description']).agg({'date':'last','currency':'last','in':'sum','out':'sum'}).reset_index()

def create_account_df(account_name, df):
    '''
    Create a dataframe for the given account name with the addition of a balance field

    year | month | account | category | description | date | currency | in | out | in_out | balance
    '''
    df = df[df.account == account_name]
    df = df.sort_values(['date'])
    df['in_out'] = df['in'] - df['out']
    df['balance'] = round(df.in_out.cumsum(),2)
    df['account'] = account_name

    return df

def account_balance(account_df):
    return account_df.groupby(['year', 'month', 'account', 'currency']).agg({'in':'sum', 'out':'sum', 'in_out':'sum', 'balance':'last'}).reset_index()

def account_balance_by_categories(account_df):
    return account_df.groupby(['year', 'month', 'account', 'currency', 'category']).agg({'in_out':'sum'}).reset_index()

def create_monthly_summary(account_df, year, month):
    '''
    Return summary of in/out per year and month
    '''
    df = account_df[(account_df.month == month) & (account_df.year == year)]
    balance = df.balance.iloc[-1]
    income = df[df.category == 'income'].amount.iloc[0] if 'income' in df.category.unique() else 0.0
    wants = df[df.category == 'wants'].amount.iloc[0] if 'wants' in df.category.unique() else 0.0
    needs = df[df.category == 'needs'].amount.iloc[0] if 'needs' in df.category.unique() else 0.0
    savings = df[df.category == 'savings'].amount.iloc[0] if 'savings' in df.category.unique() else 0.0
    expenses = wants + needs + savings
    wants_pcg = abs(wants / income * 100) if income > 0 else 0.0
    needs_pcg = abs(needs / income * 100) if income > 0 else 0.0
    savings_pcg = abs(savings / income * 100) if income > 0 else 0.0

    summary = {
        'year': year,
        'month': month,
        'account_name': df.account.iloc[0],
        'currency': df.currency.iloc[0],
        'balance': balance,
        'in': income,
        'out': expenses,
        'wants': wants,
        'needs': needs,
        'savings': savings
    }
    
    return summary

def create_categories_dropdown(df):
    return df.category.unique()

def create_description_dropdown(df):
    return df.description.unique()

def create_account_dropdown(df):
    return df.account.unique()

def create_year_dropdown(df):
    return df.year.unique()

def create_month_dropdown(df):
    return df.month.unique()

def plot_account_balance(account_df, year='all'):
    df = account_df if year=='all' else account_df[account_df.year == year]
    account_name = df.account.iloc[0]

    title = f'Monthly balance | {account_name.upper()}'

    # transform the year column into a string so that can group the bar plot
    df['year'] = df.year.astype('str')

    fig = px.bar(
        data_frame=df,
        x='month',
        y='balance',
        color='year',
        barmode='group',
        title=title
    )

    fig.update_xaxes(title=None, labelalias=dict(zip([1,2,3,4,5,6,7,8,9,10,11,12], MONTHS)))
    fig.update_yaxes(title='Balance')

    return fig

def plot_account_inout(account_df, year):
    df = account_df[account_df.year == year]
    account_name = df.account.iloc[0]

    title = f'Monthly in/out | {account_name.upper()}'
    df['total'] = df['in'] + df['out']
    df['pcg_in'] = (df['in']/df['total']) * 100
    df['pcg_out'] = (df['out']/df['total']) * 100

    fig = px.bar(
        data_frame=df,
        x='month',
        y=['pcg_in', 'pcg_out'],
        title=title,
        color_discrete_sequence=['green', 'red'],
    )

    custom_data=['in', 'out']
    labels={'pcg_in': 'incomes', 'pcg_out': 'expenses'}

    fig.for_each_trace(lambda t: t.update(name=labels[t.name]))
    fig.update_xaxes(title=None, labelalias=dict(zip([1,2,3,4,5,6,7,8,9,10,11,12], MONTHS)))
    fig.update_yaxes(title='Percentage Incomes-Expenses')

    for i, trace in enumerate(fig.data):
        fig.data[i]['customdata'] = df[custom_data[i]]
        fig.data[i]['hovertemplate'] = '%{customdata:.2f}' + f' {df.currency.iloc[0]}'

    return fig

def plot_account_category_pcg(account_df, year, month):
    df = account_df[(account_df.year == year) & (account_df.month == month)]
    # df = account_df[account_df.year == year]
    # df = pd.pivot(
    #     df,
    #     index=['year', 'month', 'account', 'currency'],
    #     columns='category',
    #     values='in_out',
    # ).reset_index()
    
    # for column in df.columns:
    #     if column not in ['year', 'month', 'account', 'currency', 'income']:
    #         df[f'{column}_pcg'] = abs(df[column]/df.income) * 100

    income = df[df.category == 'income']['in_out'].iloc[0] if 'income' in df.category.unique() else 0.
    needs = abs(df[df.category == 'needs']['in_out'].iloc[0]/income)*100 if 'needs' in df.category.unique() else 0.
    wants = abs(df[df.category == 'wants']['in_out'].iloc[0]/income)*100 if 'wants' in df.category.unique() else 0.
    savings = abs(df[df.category == 'savings']['in_out'].iloc[0]/income)*100 if 'savings' in df.category.unique() else 0.

    # thresholds = {'needs_pcg':50, 'wants_pcg':30, 'savings_pcg':20}

    pcg_df = pd.DataFrame({'cat':['needs', 'wants', 'savings'], 'val':[needs,wants,savings]})#[abs(needs/income)*100, abs(wants/income)*100, abs(savings/income)*100]})

    fig = go.Figure(
        data=[
            go.Pie(
                labels=pcg_df.cat,
                values=pcg_df.val,
                hole=.4
            )
        ]
    )
    months = dict(zip([1,2,3,4,5,6,7,8,9,10,11,12], MONTHS))
    title = f'Percentage of expenses by main categories | {df.account.iloc[0].upper()} | {months[df.month.iloc[0]]} {df.year.iloc[0]}'

    fig.update_layout({'title':title})

    # fig = px.pie(
    #     data_frame=pcg_df,
    #     values='val',
    #     names='cat'
    # )
    return fig

def plot_categories(account_df, year, month):
    summary = create_monthly_summary(account_df, year, month)
    
    needs = abs(summary['needs']/summary['in'])*100
    wants = abs(summary['wants']/summary['in'])*100
    savings = abs(summary['savings']/summary['in'])*100

    df = pd.DataFrame({'category': ['needs', 'wants', 'savings'], 'value': [needs, wants, savings], 'threshold': [50, 30, 20]})

    fig = px.bar(
        data_frame=df,
        x='category',
        y=['value', 'threshold'],
        barmode='overlay',
        title=f'{summary["account_name"].upper()} | {MONTHS[int(month) - 1]}, {year}'
    )

    return fig


### Testing ###

filename = 'personal_finance.xlsx'
account_df = create_account_registry(filename)
df = create_main_in_out_df(filename)
# print(df)
accounts = account_df.name.unique()

data = create_account_df('sella', df)
print('\nAccount df\n')
print(data)
print('\nAccount balance\n')
print(account_balance(data))
print('\nAccount balance by category\n')
print(account_balance_by_categories(data))

# print(data[(data.year == 2023) | (data.year == 2024)])
# print(data)

# plot_account_balance(account_balance(data), 2024).show()
# plot_account_inout(account_balance(data), 2023).show()
plot_account_category_pcg(account_balance_by_categories(data), 2024, 3).show()


# summary = create_monthly_summary(data, 2024, 3)

# text = f"Monthly Summary, {summary['account_name'].upper()} - {MONTHS[int(summary['month']) - 1]}, {summary['year']}\n"
# text += f"Balance: {summary['balance']:.2f} {summary['currency']}\n"
# text += f"Total income: {summary['in']:.2f} {summary['currency']}\n"
# text += f"Total expenses: {summary['out']:.2f} {summary['currency']}\n"
# text += f"Needs: {abs(summary['needs']/summary['in'])*100:.2f} % - of 50%\n"
# text += f"Wants: {abs(summary['wants']/summary['in'])*100:.2f} % - of 30%\n"
# text += f"Savings: {abs(summary['savings']/summary['in'])*100:.2f} % - of 20%\n"
# print(text)


# # plot_categories(data, 2024, 3).show()