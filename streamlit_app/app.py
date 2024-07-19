import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

st.title("Personal Finance App")

@st.cache_data()
def import_data(filename):
    df = pd.read_csv(filename)
    df['date'] = pd.to_datetime(df.date)
    df = df.set_index(df.date)
    df.drop('date', axis=1, inplace=True)

    return df

# @st.experimental_fragment
@st.cache_data(show_spinner='Creating database...')
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

@st.cache_data
def account_balance(account_df):
    return account_df.groupby(['year', 'month', 'account', 'currency']).agg({'in':'sum', 'out':'sum', 'in_out':'sum', 'balance':'last'}).reset_index()

@st.cache_data
def calculate_category_pcg(df):
    pt = df.pivot_table(index=['year','month'], columns='category', values=['in','out'], aggfunc='sum')

    grouped_df = df.groupby(['year','month']).count().reset_index()
    grouped_df['wants_pcg'] = (pt[('out','wants')]/pt[('in','income')]*100).to_list()
    grouped_df['needs_pcg'] = (pt[('out','needs')]/pt[('in','income')]*100).to_list()
    grouped_df['savings_pcg'] = (pt[('out','savings')]/pt[('in','income')]*100).to_list()

    grouped_df = grouped_df.drop(['date','account','category','description','currency','in','out'],axis=1).fillna(0.0)
    return grouped_df

### TO DO ###
# Add currency information in the hover text
@st.experimental_fragment
def plot_account_balance(account_df, years):
    dfs=[]
    for y in years:
        dfs.append(account_df[account_df.year == y])
    df = pd.concat(dfs)
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

@st.experimental_fragment
def plot_account_inout(account_df, year):
    df = account_df[account_df.year == year]
    account_name = df.account.iloc[0]

    title = f'Monthly in/out | {account_name.upper()} | Year {df.year.iloc[0]}'
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

@st.cache_data
def create_summary(df):
    summary = []
    for account in df.account.unique():
        account_df = create_account_df(account, df)
        summary.append(
            {
                'account':account, 
                'currency':account_df.currency.iloc[-1], 
                'date':account_df.index[-1].strftime("%b %d, %Y"),
                'balance':account_df.balance.iloc[-1]
            }
        )
    
    return summary


filename = st.sidebar.file_uploader(label='Upload your data file', key='filename')

if filename:
    df = import_data(filename)
    st.session_state['df'] = df
elif 'df' in st.session_state:
    df = st.session_state.df

try:
    # st.dataframe(df)
    st.html('<h3>Summary</h3>')
    for d in create_summary(df):
        st.write(f'{d["account"].upper()}: {d["balance"]:.2f} {d["currency"]} as of {d["date"]}')
    accounts = ['all']
    for a in df.account.unique():
        accounts.append(a)

    selected_account = st.sidebar.selectbox(
        label='Account(s)',
        options=accounts,
        key='account_dropdown'
    )

    if selected_account != 'all':
        account_df = create_account_df(selected_account, df)
        # st.sidebar.write(f'Balance as of {account_df.date.iloc[-1].strftime("%b %d, %Y")}: {account_df.balance.iloc[-1]:.2f} {account_df.currency.iloc[-1]}')
        st.sidebar.write(f'Balance as of {account_df.index[-1].strftime("%b %d, %Y")}: {account_df.balance.iloc[-1]:.2f} {account_df.currency.iloc[-1]}')
        st.html(f'<h3>Complete financial records for {selected_account.upper()} account</h3>')
        # st.write(f'Complete financial records for {selected_account.upper()} account')
        
        st.dataframe(account_df)
        selected_years = st.sidebar.multiselect(label='Year', options=account_df.year.unique(), default=max(account_df.year))
        st.plotly_chart(plot_account_balance(account_balance(account_df), selected_years))
        for year in selected_years:
            st.plotly_chart(plot_account_inout(account_balance(account_df), year))

except:
    st.sidebar.write('Please upload a file or select a previous version from the list below.')
    ### TO DO ###
    # Add last versions of database previously saved


