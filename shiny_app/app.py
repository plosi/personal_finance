from shiny import App, render, reactive, ui
from shiny.types import FileInfo
from shinywidgets import output_widget, render_widget, render_plotly

import faicons as fa
import pandas as pd
import numpy as np

import plotly.express as px
import plotly.graph_objects as go

# from forex_python.converter import CurrencyRates
# import requests


ICONS = {
    'wallet': fa.icon_svg('wallet'),
    'currency_eur': fa.icon_svg('euro-sign'),
    'currency_gbp': fa.icon_svg('sterling-sign')
}

MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']


app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_file(
            id='data_file',
            label='Load csv data file',
            accept=['.csv'],
            multiple=False
        ),
        ui.output_ui('account'),
        ui.output_ui('year'),
        ui.output_ui('month')
    ),
    
    ui.layout_columns(
        ui.output_ui('balance'),
        ui.card(
            'Graphs',
            ui.card(
                # ui.card_header('Monthly balance'),
                output_widget('monthly_balance_plot'),
                full_screen=True,
            ),
            ui.card(
                # ui.card_header('Percentage in/out by category'),
                output_widget('pcg_category_plot'),
                full_screen=True,
            ),
        ),
        col_widths=(3,9)
    ),

    title='Personal Finance',
    fillable=True
)

def server(input, output, session):
    @reactive.calc
    def parsed_file():
        file: list[FileInfo] | None = input.data_file()
        if file is None:
            return pd.DataFrame()
        df = pd.read_csv(file[0]['datapath'])
        df['date'] = pd.to_datetime(df.date, dayfirst=True)
        return df

    @reactive.calc
    def get_total_wealth():
        df = parsed_file()

        if df.empty:
            return 0.0
        
        wealth = []
        for account in df.account.unique():
            account_df = df[df.account == account]
            account_df = account_df.sort_values(['date'])
            account_df['in_out'] = account_df['in'] - df['out']
            account_df['balance'] = round(account_df.in_out.cumsum(),2)

            wealth.append((account_df.currency.iloc[-1], account_df.balance.iloc[-1]))
        
        total_eur = sum([item[1] for item in wealth if item[0]=='EUR'])
        total_gbp = sum(item[1] for item in wealth if item[0]=='GBP') * 1.19 #CurrencyRates().get_rate('GBP', 'EUR')

        return(total_eur + total_gbp)

    @reactive.calc
    def get_account_balance():
        df = parsed_file()

        if df.empty:
            return 0.0
        
        balance = []
        for account in df.account.unique():
            account_df = df[df.account == account]
            account_df = account_df.sort_values(['date'])
            account_df['in_out'] = account_df['in'] - account_df['out']
            account_df['balance'] = round(account_df.in_out.cumsum(),2)

            balance.append((account_df.currency.iloc[-1], account_df.balance.iloc[-1], account))
        # print(balance)
        return balance

    @reactive.calc
    def get_account_dropdown():
        df = parsed_file()

        if df.empty:
            return []
        
        return [i for i in df.account.unique()]

    @reactive.calc
    def get_year_dropdown():
        df = parsed_file()
        
        if df.empty:
            return []
        
        df = df[df.account == input.account_select()]
        return [int(i) for i in df.year.unique()]

    @reactive.calc
    def get_month_dropdown():
        df = parsed_file()

        if df.empty:
            return []
        
        df = df[(df.account == input.account_select()) & (df.year == int(input.year_select()))]
        return [int(i) for i in df.month.unique()]

    @reactive.calc
    def get_account_monthly_balance():
        df = parsed_file()
        
        if df.empty:
            return pd.DataFrame()
        
        df = df[df.account == input.account_select()]
        df = df.sort_values(['date'])
        df['in_out'] = df['in'] - df['out']
        df['balance'] = round(df.in_out.cumsum(), 2)

        return df.groupby(['year', 'month', 'account', 'currency']).agg({'in':'sum', 'out':'sum', 'in_out':'sum', 'balance':'last'}).reset_index()

    @reactive.calc
    def get_monthly_category():
        df = parsed_file()

        if df.empty:
            return pd.DataFrame()

        def exchange_in_out(df):
            if df.currency == 'GBP':
                rate = 1.19
            else:
                rate = 1
            
            df['in'] = df['in'] * rate
            df['out'] = df['out'] * rate

            return df

        # need to exchange everything to EUR and then do the calculations
        cat_df = df[(df.apply(exchange_in_out, axis=1).year==int(input.year_select())) & (df.apply(exchange_in_out, axis=1).account != 'generali_SAV')].groupby(['year','month','category']).agg({'in':'sum', 'out':'sum'}).reset_index()

        tmp = cat_df.groupby(['year','month'])['in'].sum().reset_index()
        tmp = tmp.rename(columns={'in':'total_income'})

        merged = pd.merge(left=cat_df, right=tmp)

        # merged['pcg_in_out'] = (abs(merged['in'] - merged['out'])/merged.total_income) #* 100
        merged['pcg_in_out'] = (merged['in'] - merged['out'])/merged.total_income #* 100

        return merged

    @render.ui
    def balance():
        balances = get_account_balance()
        boxes = []
        total_wealth = f'{get_total_wealth():,.2f}'
        
        boxes.append(ui.value_box(
            'Total Wealth',
            value=total_wealth,#ui.output_ui('total_wealth'),
            showcase=ICONS['currency_eur']
            )
        )

        if balances:
            for i in range(len(balances)):
                boxes.append(ui.value_box(
                        title=balances[i][2].upper(),
                        value=f'{balances[i][1]:,.2f}',
                        showcase=ICONS['currency_eur'] if balances[i][0] == 'EUR' else ICONS['currency_gbp']
                    ))
            return boxes

    @render.ui
    def account():
        return ui.input_select(
            'account_select',
            'Account',
            choices=get_account_dropdown(),
            selected='sella'
        )

    @render.ui
    def year():
        return ui.input_select(
            'year_select',
            'Year',
            choices=get_year_dropdown(),
            selected='' if not get_year_dropdown() else get_year_dropdown()[-1]
        )
    
    @render.ui
    def month():
        return ui.input_select(
            'month_select',
            'Month',
            choices=get_month_dropdown(),
            selected='' if not get_month_dropdown() else get_month_dropdown()[-1]
        )
    
    @render_widget
    def monthly_balance_plot():
        df = get_account_monthly_balance()

        if not df.empty and input.year_select():

            balance_df = df[df.year == int(input.year_select())]

            title = f'Monthly balance | {input.account_select().upper()} | {input.year_select()}'

            fig = px.bar(
                data_frame=balance_df,
                x='month',
                y='balance',
                title=title
            )

            fig.update_xaxes(title=None, labelalias=dict(zip([1,2,3,4,5,6,7,8,9,10,11,12], MONTHS)))
            fig.update_yaxes(title='Balance')
   
            return fig
    
    @render_widget
    def pcg_category_plot():
        df = get_monthly_category()

        if not df.empty and input.month_select():
            
            df = df[df.month==int(input.month_select())]
            print(df)

            title = f'Percentage of total in/out by category | {MONTHS[int(input.month_select())-1].capitalize()}, {input.year_select()}'
            print(title)

            df['color'] = np.where(df.pcg_in_out < 0, 'red', 'green')
            fig = px.bar(
                data_frame=df[(df.pcg_in_out != 0)],
                x='pcg_in_out',
                y='category',
                barmode='stack',
                text_auto='.2%',
            )

            fig.update_layout(xaxis_tickformat='.0%', title=title, xaxis_title='', yaxis_title='')
            fig.update_traces(marker_color=df[(df.pcg_in_out != 0)].color)

            return fig

app = App(app_ui, server)