import streamlit as st
import pandas as pd

st.title('Add transaction')

if 'tmp' not in st.session_state:   
    st.session_state.tmp = pd.DataFrame()
   
def add(date, account, description, amount, category, income):
    date = pd.to_datetime(date, format="%Y-%m-%d")
    data = {
        'date': date,
        'year': date.year,
        'month': date.month,
        'account': account,
        'category': category,
        'description': description,
        'currency': df[df.account == selected_account].currency.iloc[0],
        'in': amount if income == 'Income' else 0.,
        'out': amount if income == 'Expense' else 0.,
    }

    data_df =  pd.DataFrame.from_dict([data])
    data_df = data_df.set_index(data_df.date)
    data_df.drop('date', axis=1, inplace=True)
    
    st.session_state['tmp'] = pd.concat([st.session_state['tmp'], data_df], ignore_index=False)


if 'df' not in st.session_state:
    st.warning('Please upload a data file from previous page.')
else:
    df = st.session_state.df


    col1, col2, col3 = st.columns([4,4,4])

    with col1:
        selected_account = st.selectbox(
            label='Account',
            options=df.account.unique(),
            key='account'
        )
        description = st.text_input(
            label='Description', 
            key='description'
        )

    with col2:
        date = st.date_input(
            label='Date',
            value='default_value_today',
            format='YYYY/MM/DD',
            key='date'
        )
        amount = st.number_input(
            label=f'Amount in {df[df.account == selected_account].currency.iloc[0]}',
        )
    
    with col3:
        selected_in_out = st.radio(
            label='In or Out',
            options=['Income', 'Expense'],
            horizontal=True,
            key='in_out'
        )
        selected_category = st.selectbox(
            label='Category',
            options=['income'] if selected_in_out == 'Income' else ['needs', 'wants', 'savings', 'transfer']
        ) 

    if st.button('Add'):
        add(date, selected_account, description, amount, selected_category, selected_in_out)

    ## display the new data
    st.dataframe(st.session_state.tmp)
    # st.data_editor(st.session_state.tmp, num_rows='dynamic', key='updated_tmp')
    ### TO DO: add the possibility to remove a row

    if st.button('Save'):
        st.session_state.df = pd.concat([st.session_state.df, st.session_state.tmp], ignore_index=False)
        st.session_state.df.to_csv('output.csv')

        ## reset the dataframe to empty
        st.session_state.tmp = pd.DataFrame()
        st.rerun()
    
    if st.button('Cancel'):
        ## reset the dataframe to empty
        st.session_state.tmp = pd.DataFrame()
        st.rerun()

    ## display the updated dataframe
    st.dataframe(df[df.account==selected_account].tail(5))