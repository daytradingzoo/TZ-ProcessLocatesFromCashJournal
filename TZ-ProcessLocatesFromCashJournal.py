import pandas as pd
import numpy as np

# SET PATH TO WHERE YOU STORE THE DOWNLOADED CASH JOURNAL CSV 
path = 'FILL IN YOUR PATH HERE'

# SET FILENAME OF THE CASH JOURNAL CSV 
file = 'FILL IN YOUR CSV SOURCE FILE HERE'

# READING SOURCE DATA
df_cj = pd.read_csv(path + file)

df_cj.rename(columns={'E/D':'Date'}, inplace=True)

# SET THE DATE COLUMN TO PROPER DATE TYPE
df_cj['Date'] = pd.to_datetime(df_cj['Date'])

# CLEANUP THE NOTE COLUMN SO WE CAN SPLIT IT INTO COLUMSN LATER ON
lstReplaceValues = ['Locate credit ', 'Locate ', 'Pre-Borrow ', 'per share']
for item in lstReplaceValues:
    df_cj['Note'].replace(item,'', regex=True, inplace=True)

df_cj['Note'] = df_cj['Note'].str.strip()

# DETERMINE IF IT'S A CREDIT OR A DEBIT ACTION
df_cj['Side'] = np.where(df_cj['Withdraw'] > 0, 'Debit', 'Credit')

# FILTER DOWN TO ONLY LOCATE ACTIONS
df_cj['IsLocate'] = 0
df_cj['IsLocate'] = np.where(df_cj['Note'].str.contains('@'), 1, df_cj['IsLocate'])
df_cj = df_cj[df_cj['IsLocate']==1]

# SPLIT THE NOTE VALUE INTO MULTIPLE COLUMNS
df_cj[['Shares', 'Ticker', 'PricePerShare']] = df_cj['Note'].str.split(' ', expand=True)[[0,1,3]]

df_cj['Shares'] = (pd.to_numeric(df_cj['Shares'], errors='coerce').fillna(0))

# SET DATATYPE FOR SHARES COLUMN TO FLOAT
dtype = {
        'Shares' : float, 
        }

for k, v in dtype.items():
    df_cj[k] = df_cj[k].astype(v)
    
# REMOVE COLUMNS WE DON'T NEED ANYMORE
df_cj.drop(columns=['Account','Name','Currency','Note','IsLocate','PricePerShare'], inplace=True)

# CREATE A DATAFRAME WITH THE DEBITS
df_cj_debit = df_cj[df_cj['Side']=='Debit']
df_cj_debit.drop(columns=['Deposit', 'Side'], inplace=True)
df_cj_debit.rename(columns={'Shares':'SharesDebit', 'Withdraw':'Debit'}, inplace=True)
df_cj_debit = df_cj_debit.groupby(['Date','Ticker']).sum().reset_index()

# CREATE A DATAFRAME WITH THE CREDITS
df_cj_credit = df_cj[df_cj['Side']=='Credit']
df_cj_credit.drop(columns=['Withdraw', 'Side'], inplace=True)
df_cj_credit.rename(columns={'Shares':'SharesCredit', 'Deposit':'Credit'}, inplace=True)
df_cj_credit = df_cj_credit.groupby(['Date','Ticker']).sum().reset_index()

# MERGE TWO DATAFRAMES TOGETHER
df = pd.merge(df_cj_debit, df_cj_credit, on=['Date','Ticker'], how='left', suffixes=('','_drop'))
df.drop([col for col in df.columns if 'drop' in col], axis=1, inplace=True)

# CALCULATE PRICES PER SHARE AND ROUND TO 4 DECIMALS
df['PerShareDebit'] = (df['Debit'] / df['SharesDebit']).round(4)
df['PerShareCredit'] = (df['Credit'] / df['SharesCredit']).round(4)

# SMALL CLEANUP ACTIONS
df['Debit'].fillna(0, inplace=True)
df['Credit'].fillna(0, inplace=True)

df['PerShareDebit'].fillna(0, inplace=True)
df['PerShareCredit'].fillna(0, inplace=True)

df['SharesCredit'].fillna(0, inplace=True)
df['SharesDebit'].fillna(0, inplace=True)

# CLEANUP
del df_cj_debit
del df_cj_credit
del df_cj
del dtype
del k
del path
del item
del lstReplaceValues
