from shiny import App, render, reactive, ui
from shiny.types import FileInfo
from shinywidgets import output_widget, render_widget, render_plotly

import faicons as fa
import pandas as pd
import numpy as np
# from datetime import datetime, timedelta

import plotly.express as px
# import plotly.graph_objects as go

import helpers as hp

# from forex_python.converter import CurrencyRates
# import requests

ICONS = {
    'wallet': fa.icon_svg('wallet'),
    'currency_eur': fa.icon_svg('euro-sign'),
    'currency_gbp': fa.icon_svg('sterling-sign')
}

MONTHS = hp.MONTHS

finance = reactive.Value()
finance.set(hp.import_data())


app_ui = ui.page_navbar(
    ui.nav_panel(
        'Plots',
        ui.layout_columns(
            ui.row(
                ui.column(3,ui.output_ui('summary_boxes')),
                ui.column(
                    9,
                    ui.card(
                        ui.card_header(ui.HTML('<h1>Monthly Balance</h1>')),
                        ui.row(
                            ui.column(4, ui.output_ui('select_account'),),
                            ui.column(4, ui.output_ui('select_year'),),
                        ),
                        output_widget('plot_monthly_balance'),
                        output_widget('plot_monthly_in_out'),
                        full_screen=True
                    ),
                    ui.card(
                        ui.card_header(ui.HTML('<h1>Category percentage</h1>')), 
                        ui.row(
                            ui.column(4, ui.output_ui('select_year_2')),
                            ui.column(4, ui.output_ui('select_month')),
                        ),
                        ui.row(
                            ui.column(
                                6,
                                output_widget('pcg_category_plot'),
                                full_screen=True
                            ),
                            ui.column(
                                6,
                                ui.output_data_frame('category_table')
                            )
                        ),
                    ),
                ),
            )
                
            # col_widths=(3,9)
        ),
    ),
    ui.nav_panel(
        'Data',
        ui.layout_columns(
            ui.row(
                ui.column(
                    3,
                    ui.row(
                        ui.output_ui('table_year_filter'),
                        ui.output_ui('table_account_filter'),
                    ),
                    ui.markdown('Add | Delete | Edit'),
                    ui.markdown('Modify the table only on UNFILTERED data'),## to fix and remove
                    ui.row(
                        ui.column(4, ui.tooltip(ui.output_ui('add_btn'),'Add', placement='top')),
                        ui.column(4, ui.tooltip(ui.output_ui('delete_btn'),'Delete', placement='top')),
                        ui.column(4, ui.tooltip(ui.output_ui('edit_btn'), 'Edit', placement='top')),
                    )
                ),
                ui.column(
                    9,
                    ui.output_data_frame('data_grid'),
                )
            )
        )
    ),

    title='Personal Finance',
    fillable=True
)

def server(input, output, session):

    @render.ui
    def summary_boxes():
        data = finance.get()

        boxes_acc = []
        boxes_values = []
        boxes_curr = []

        balances = hp.calculate_account_balance(data)
        total_wealth = f'{hp.calculate_total_wealth(data):,.2f}'
        boxes_acc.append('Total Wealth')
        boxes_values.append(total_wealth)
        boxes_curr.append('EUR')

        for i in range(len(balances)):
            boxes_acc.append(balances[i][2].upper())
            boxes_values.append(f'{balances[i][1]:,.2f}')
            boxes_curr.append(balances[i][0])
        
        boxes = []
        for row in range(len(boxes_acc)):
            boxes.append(
                ui.value_box(
                    title=boxes_acc[row],
                    value=boxes_values[row],
                    showcase=ICONS['currency_eur'] if boxes_curr[row] == 'EUR' else ICONS['currency_gbp']
                )                 
            )

        return boxes

    @render.ui
    def select_account():
        data = finance.get()
        return ui.input_select(
            'select_account_',
            'Filter by account:',
            choices=[acc for acc in data.account.unique()],
            selected='sella'
        )

    @render.ui
    def select_year():
        data = finance.get()
        account = input.select_account_()
        data = data[data.account == account]
        return ui.input_select(
            'select_year_',
            'Filter by year:',
            choices=[int(yr) for yr in data.date.dt.year.unique()],
            selected=max(data.year)
        )
    
    @render.ui
    def select_year_2():
        data = finance.get()
        # account = input.select_account_()
        # data = data[data.account == account]
        return ui.input_select(
            'select_year_2_',
            'Filter by year:',
            choices=[int(yr) for yr in data.date.dt.year.unique()],
            selected=max(data.year)
        )
    
    @render.ui
    def select_month():
        data = finance.get()
        data = data[data.year == int(input.select_year_2_())]
        # print(data.iloc[-1].month)
        months = [int(month) for month in sorted(data.date.dt.month.unique())]
        return ui.input_select(
            'select_month_',
            'Filter by month:',
            choices= months,
            selected=max(months)
        )
    
    @render_widget
    def plot_monthly_balance():
        data = finance.get()
        data = data[data.account == input.select_account_()]
        data = data.sort_values(['date'])
        data['in_out'] = data['in'] - data['out']
        data['balance'] = round(data.in_out.cumsum(), 2)

        data = data.groupby(['year', 'month', 'account', 'currency']).agg({'in':'sum', 'out':'sum', 'in_out':'sum', 'balance':'last'}).reset_index()

        balance_df = data[data.year == int(input.select_year_())]
        title = f'Monthly balance | {input.select_account_().upper()} | {input.select_year_()}'

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
    def plot_monthly_in_out():
        data = finance.get()
        data = data[data.account == input.select_account_()]
        data = data.sort_values(['date'])
        data['in_out'] = data['in'] - data['out']
        data['balance'] = round(data.in_out.cumsum(), 2)


        data = data.groupby(['year', 'month', 'account', 'currency']).agg({'in':'sum', 'out':'sum', 'in_out':'sum', 'balance':'last'}).reset_index()

        balance_df = data[data.year == int(input.select_year_())]
        balance_df['color'] = balance_df.in_out.apply(lambda x: 'red' if x <= 0 else 'green')
        title = f'Net Savings | {input.select_account_().upper()} | {input.select_year_()}'

        fig = px.bar(
            data_frame=balance_df,
            x='month',
            y='in_out',
            color='color',
            color_discrete_map={'red':'red', 'green':'green'},
            title=title
        )

        fig.update_xaxes(title=None, labelalias=dict(zip([1,2,3,4,5,6,7,8,9,10,11,12], MONTHS)))
        fig.update_yaxes(title='Net Savings')
        fig.update_layout(showlegend=False)

        return fig

    @render_widget
    def pcg_category_plot():
        data = finance.get()
        df = hp.calculate_monthly_category(data, input.select_year_2_())
        df = df[df.month==int(input.select_month_())]

        title = f'Percentage of total in/out by category | {MONTHS[int(input.select_month_())-1].capitalize()}, {input.select_year_2_()}'

        df['color'] = np.where(df.pcg_in_out < 0, 'red', 'green')
        df = df[(df.pcg_in_out != 0)].sort_values(by='pcg_in_out', ascending=False)
        fig = px.bar(
            data_frame=df,
            x=['pcg_in','pcg_out'],#'pcg_in_out',
            y='category',
            # barmode='stack',
            text_auto='.2%',
        )

        fig.update_layout(xaxis_tickformat='.0%', title=title, xaxis_title='', yaxis_title='')
        # fig.update_traces(marker_color=df.color)#df[(df.pcg_in_out != 0)].color)
        fig.update_layout(showlegend=False)

        return fig
    
    @render.data_frame
    def category_table():
        data = finance.get()
        df = hp.calculate_monthly_category(data, input.select_year_2_())
        df = df[df.month==int(input.select_month_())]
        df = df.drop(['year','month'], axis=1)
        df['pcg_in_out'] = round(df.pcg_in_out * 100,2)
        df['pcg_in'] = round(df.pcg_in * 100,2)
        df['pcg_out'] = round(df.pcg_out * 100,2)

        return render.DataTable(
            data=df.sort_values(by='pcg_in_out', ascending=False),
            width='fit-content'
        )

    @render.ui
    def table_year_filter():
        data = finance.get()
        data['date'] = pd.to_datetime(data.date, dayfirst=True, errors='raise', format='%d/%m/%Y')
        years = [int(yr) for yr in data.date.dt.year.unique()]
        years.append('All')
        return ui.input_select(
            id='table_year_filter_',
            label='Filter by year:',
            choices=years,#[int(yr) for yr in data.date.dt.year.unique()],
            selected='All'#max(data.date.dt.year)
        )
    
    @render.ui
    def table_account_filter():
        data = finance.get()
        accounts = [a for a in data.account.unique()]
        accounts.append('All')
        return ui.input_select(
            id='table_account_filter_',
            label='Filter by account:',
            choices=accounts,
            selected='All'#data.iloc[-1].account
        )

    @render.ui
    def add_btn():
        return ui.input_action_button(
            id='add_btn_',
            label='',
            class_='btn btn-success',
            icon=fa.icon_svg('square-plus')
        )
    
    @reactive.effect
    @reactive.event(input.add_btn_)
    def _():
        # data = finance.get()
        add_form = ui.modal(
            hp.ADD_TRANSACTION['date'],
            hp.ADD_TRANSACTION['account'],
            hp.ADD_TRANSACTION['category'],
            hp.ADD_TRANSACTION['description'],
            hp.ADD_TRANSACTION['currency'],
            hp.ADD_TRANSACTION['in'],
            hp.ADD_TRANSACTION['out'],
            ui.div(
                ui.input_action_button('add_submit', 'Submit', class_='btn btn-primary'),
                class_='d-flex justify-content-end'
            ),
            title='Add transaction',
            easy_close=True,
            footer=None
        )
        ui.modal_show(add_form)

    @reactive.effect
    @reactive.event(input.add_submit)
    def _():
        data = finance.get()
        try:
            new_row = pd.DataFrame([{k:input[f'add_{k}']() for k in hp.ADD_TRANSACTION.keys()}])
            new_row = new_row.reindex(columns=data.columns)
            new_row['date'] = pd.to_datetime(new_row.date, dayfirst=True, errors='raise', format='%d/%m/%Y')
            updated_data = pd.concat([data, new_row], ignore_index=True)
            updated_data = updated_data.sort_values(by='date', ascending=False)

            finance.set(updated_data)
            ui.notification_show(f'Added new transaction for account {new_row.iloc[0].account.upper()}, thank you!', type='message')
            hp.save_data_to_file(updated_data)
        except Exception as e:
            ui.notification_show(f'Oops, something went wrong: {e}', type='error')

    @render.ui
    def delete_btn():
        return ui.input_action_button(
            id='delete_btn_',
            label='',
            class_='btn btn-danger',
            icon=fa.icon_svg('square-minus')
        )
    
    @reactive.effect
    @reactive.event(input.delete_btn_)
    def _():
        ## get the index of the selected row(s)
        selected_rows = data_grid.cell_selection()['rows']
        if not selected_rows:
            ui.notification_show('Please select one or more rows to be deleted', type='error')
            return
        
        ## Get the filtered dataframe view
        filtered_df = data_grid.data_view()

        ## Map the selected row indices from the filtered view to the original dataframe indices
        selected_original_indices = filtered_df.iloc[[int(r) for r in selected_rows]].index.tolist()

        ## Get the original dataframe and remove the selected rows using their original indices
        updated_data = finance.get().drop(selected_original_indices)
        finance.set(updated_data)
        hp.save_data_to_file(updated_data)
        ui.notification_show(f'Removing the following row(s): {[id for id in selected_original_indices]}', type='message')
        
        # ## get the index of the selected row(s)
        # selected_rows = data_grid.cell_selection()['rows']
        # tmp = data_grid.data_view()#pd.DataFrame(data_grid.data_view())
        # ids_in_selected_rows = set(tmp.iloc[[int(r) for r in selected_rows]].index)

        # if selected_rows:
        #     original_df = data_grid.data()
        #     rows_to_drop = original_df[original_df.index.isin(ids_in_selected_rows)].index
        #     updated_data = finance.get().drop(rows_to_drop, axis=0)
        #     finance.set(updated_data)
        #     hp.save_data_to_file(updated_data)
        #     ui.notification_show(f'Removing the following row(s): {[id for id in ids_in_selected_rows]}', type='message')
        # else:
        #     ui.notification_show(f'Please select one or more rows to be deleted', type='error')

    @render.ui
    def edit_btn():
        return ui.input_action_button(
            id='edit_btn_',
            label='',
            class_='btn btn-warning',
            icon=fa.icon_svg('pen-to-square')
        )

    @reactive.effect
    @reactive.event(input.edit_btn_)
    def _():
        selected_rows = data_grid.cell_selection()['rows']
        if len(selected_rows) != 1:
            ui.notification_show('Please select at least one and only one row for editing', type='error')
            return
        
        edit_form = ui.modal(
            hp.ADD_TRANSACTION['date'],
            hp.ADD_TRANSACTION['account'],
            hp.ADD_TRANSACTION['category'],
            hp.ADD_TRANSACTION['description'],
            hp.ADD_TRANSACTION['currency'],
            hp.ADD_TRANSACTION['in'],
            hp.ADD_TRANSACTION['out'],
            ui.div(
                ui.input_action_button('edit_submit', 'Submit', class_='btn btn-primary'),
                class_='d-flex justify-content-end'
            ),
            title='Edit transaction',
            easy_close=True,
            footer=None
        )

        # tmp = data_grid.data_view()
        # id_in_selected_row = tmp.iloc[[selected_row[0]]].index
        # original_df = data_grid.data()
        # row_to_edit = original_df[original_df.index.isin(id_in_selected_row)]
        
        ## Get the filtered dataframe view and map to original index
        filtered_df = data_grid.data_view()
        original_index = filtered_df.iloc[int(selected_rows[0])].name

        ## Get the original row data using the mapped index
        original_df = finance.get()
        row_to_edit = original_df.loc[[original_index]]

        ui.update_date('add_date', value=row_to_edit.date.iloc[0])
        ui.update_select('add_account', selected=row_to_edit.account.iloc[0])
        ui.update_select('add_category', selected=row_to_edit.category.iloc[0])
        ui.update_text('add_description', value=row_to_edit.description.iloc[0])
        ui.update_radio_buttons('add_currency', selected=row_to_edit.currency.iloc[0])
        ui.update_numeric('add_in', value=row_to_edit['in'].iloc[0])
        ui.update_numeric('add_out', value=row_to_edit['out'].iloc[0])

        ui.modal_show(edit_form)

    @reactive.effect
    @reactive.event(input.edit_submit)
    def _():
        ui.modal_remove()
        # selected_row = data_grid.cell_selection()['rows']
        # tmp = data_grid.data_view()
        # id_in_selected_row = tmp.iloc[[selected_row[0]]].index
        # original_df = data_grid.data()
        # row_to_edit = original_df[original_df.index.isin(id_in_selected_row)]

        selected_rows = data_grid.cell_selection()['rows']
        filtered_df = data_grid.data_view()
        original_index = filtered_df.iloc[int(selected_rows[0])].name

        ## Update specific row using original index
        updated_row = pd.DataFrame([{k:input[f'add_{k}']() for k in hp.ADD_TRANSACTION.keys()}])
        original_df = finance.get()
        updated_row = updated_row.reindex(columns=original_df.columns)
        updated_row.index = [original_index]

        try:
            # updated_row = pd.DataFrame([{k:input[f'add_{k}']() for k in hp.ADD_TRANSACTION.keys()}])
            # updated_row = updated_row.reindex(columns=original_df.columns)
            # updated_row.set_index(row_to_edit.index, inplace=True)
            original_df.update(updated_row)
            tmp = original_df.copy()
            tmp['year'] = original_df.date.dt.year
            tmp['month'] = original_df.date.dt.month
            finance.set(tmp)

            hp.save_data_to_file(original_df)
            # ui.notification_show(f'Updated entry for {row_to_edit.iloc[0].account.upper()}, thank you!', type='message')
            ui.notification_show(f'Updated entry, thank you!', type='message')   
        except Exception as e:
            ui.notification_show(f'Oops, something went wrong. Retry!\n{e}', type='error')

    @render.data_frame
    def data_grid():
        df = finance.get()
        data = df.copy()
        data = data.drop(['month','year'], axis=1)
        # ## filter by account
        # data = data if input.table_account_filter_()=='All' else data[data.account == input.table_account_filter_()]
        # ## filter by year
        # data = data if input.table_year_filter_()=='All' else data[data.date.dt.year == int(input.table_year_filter_())]

        ## Apply filters while preserving original indices
        if input.table_account_filter_() != 'All':
            data = data[data.account == input.table_account_filter_()]
        if input.table_year_filter_() != 'All':
            data = data[data.date.dt.year == int(input.table_year_filter_())]
        
        data['date'] = pd.to_datetime(data.date, dayfirst=True, errors='raise', format='%d/%m/%Y')#data.date.dt.strftime('%d/%m/%Y')
        return render.DataGrid(
            data,#.sort_values(by='date', ascending=False),
            width='fit-content',
            selection_mode='rows'
        )


app = App(app_ui, server)