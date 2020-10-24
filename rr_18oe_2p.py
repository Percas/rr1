# -*- coding: utf-8 -*-
"""
Date: Oct 19, 2020
Author: Anton Peeters
Name: rr_18oe_2p
Scope: this python programm helps you when playing online 18xx games.
Purpose1: give some advise which share to buy in an SR
Steps:
    1. Define where to get the data in google sheets
    2. Copy the data to pandas tables with info about players and companies:
        player_shares
        company_info
    3. Derive extra support variables and join tables
    4. Make the ouput
"""

import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
from gspread_dataframe import get_as_dataframe
import re

'''
----------------------Functions ----------------------------------------

'''
def fixtable1(a, b, l, str1, str2):
    ''' 
    if at position a,b in table1 there's a string str1 (first l char)
    then replace it with str2
    edit: dropped the condition. Just fix the cell
    '''
    global table1
    # if table1.iloc[a,b][:l] == str1:
    #    table1.iloc[a,b] = str2
    table1.iloc[a,b] = str2
    # else:
    #    print('Not fixed table1. In position', a, b, str1, 'not found')
 
def make_prev_cur(ll):
    prev_cur = pd.DataFrame(columns=['Event', 'PrevEvent'])
    for prev,cur in zip(ll, ll[1:]):
        # print('Appening: ', cur, prev)
        prev_cur = prev_cur.append({'Event': cur, 'PrevEvent': prev}, 
                                   ignore_index = True)
    # print('why is this empty: ', prev_cur)
    return prev_cur

def determine_table_position(axis, df, ll):
    ''' detetermine_tabel_position checks if all elements in list ll are 
    present in the first row (axis=0) or column (axis=1) of dataframe df. 
    It returns the missing values
    '''
    count = 0
    missing = []
    if axis == 0:
        for i in ll:
            if i in list(df.iloc[0,:]):
                count += 1
            else:
                missing.append(i)
    if axis == 1:
        for i in ll:
            if i in list(df.iloc[:,0]):
                count += 1
            else:
                missing.append(i)
    if missing:
        print('missing ', 1 - count/len(ll), ' part of the list')
    return missing
    
    
    
def determine_trainlen(trainstring, train_d):
    '''
        calculate the total train length (of a company) by adding the 
        length of its individual trains. For every train its length
        is stored in the input dictionary train_d
        
        all the trains are stored in an input string called
        trainstring, which migth be Nan. If Nan then the trainlength 0
        is returned
    '''
    if trainstring == str(trainstring):
        train_l = list(filter(None, re.split(',| ', trainstring)))
        trainlen = 0
        for t in train_l:
            trainlen = trainlen + train_d[t][0]
        return trainlen
    else:
        return 0
        
   
        
def make_comp_info(e, table1, company_l, train_d,
                            comp_c, Name18oe_l, MyName_l):
    '''
    make_comp_info: In worksheet e, proces the table defined bij the
    coordinates in comp_c. Horizantally are the companies in company_l.
    Vertically are the variables of the companies in Name18oe_l.
    Store them in a dataframe.
            c1 c2 
    var1   v11 v12
    var2   v21 v22
    var3   v31 v32
    
    becomes: 
    
        comp var1 var2 var3
        c1   v11  v21  v31
        
    where:
        the var1 var2 are translated to MyName_l
        the trains are translated to one trainlength
    '''
    global comp_info
    # print("make_comp_info for event", e, "...")
    table2 = table1.iloc[comp_c[0] : comp_c[1], 
                         comp_c[2] : comp_c[3]]
    # print(table2.columns, table2.iloc[:,0])
    missing = determine_table_position(1, table2, Name18oe_l)
    if missing:
        print('in ', e, 'missing: ', missing)
    val_d = {}                                  # dict for values
    for j in range(comp_c[3] - comp_c[2]-1):    # j: left to rigth
        comp = table2.iloc[0, j+1]              # bit ugly, offset is 1
        if comp in company_l:
            val_d.clear()                       # clear the dict
            val_d['Company'] = comp             # initialize with comp  
            val_d['Event'] = e
            for i in range(comp_c[1] - comp_c[0]): # i: top to bottom
                if table2.iloc[i,0] in Name18oe_l:
                    ii = Name18oe_l.index(table2.iloc[i,0])
                    val_d[MyName_l[ii]] = table2.iloc[i,j]
            if 'trainlength' in val_d:
                # print(val_d)
                val_d['trainlength'] = determine_trainlen(val_d['trainlength'], train_d)
            # else:
            #     print(val_d)
            comp_info = comp_info.append(val_d, ignore_index=True)




def make_players_shares_df(e, table1, player_list, company_list, xy):
    ''' 
        make a table like:
                  Event    Player Company Shares
            0     SR 1   Raymond      SB      2
            1     SR 1   Raymond     W-W      2
            2     SR 1   Raymond     MKV      2
            3     SR 1    Jasper     CHN      2
            4     SR 1    Jasper     KSS      2
            5     SR 1    Jasper    GSWR      2
            6     SR 1  Johannes     MZA      3
            7     SR 1  Johannes    SFAI      2
   '''
    global players_shares_df
    # print("make_players_shares_df in worksheet:", e, "...")
    table2 = table1.iloc[xy[0] : xy[1], xy[2] : xy[3]]
    missing = determine_table_position(0, table2, company_list)
    if missing:
        print('in ', e, 'missing: ', missing)
    missing = determine_table_position(1, table2, player_list)
    if missing:
        print('in ', e, 'missing: ', missing)
    for i in range(xy[1] - xy[0]):
        for j in range(xy[3] - xy[2]):
            val = table2.iloc[i,j]
            if val in range(11):
                p = table2.iloc[i,0]
                b = table2.iloc[0,j]
                if p in player_list and b in company_list:
                    # print(p, e, b, val)
                    r = {'Player': p, 'Event': e, 'Company': b, 'Shares': val}
                    players_shares_df = players_shares_df.append(r, ignore_index=True)
    


def make_players_cash_df(e, table1, player_list, xy):
    ''' 
        make a table like:
                  Player  Event Certs  Cash
            0    Raymond   SR 1    10   100
            1     Jasper   SR 1     8     0
            2   Johannes   SR 1     9     0
            3      Anton   SR 1     8     5
            4       Coen   SR 1     7     0
            5    Raymond  OR 1a    10   110
            6     Jasper  OR 1a     8    15
            7   Johannes  OR 1a     9    55
            8      Anton  OR 1a     8    20
            9       Coen  OR 1a     7    15
    '''
    global players_cash_df
    # print("make_players_cash_df in worksheet: ", e, "..." )
    table2 = table1.iloc[xy[0] : xy[1], xy[2] : xy[3]]
    missing = determine_table_position(1, table2, player_list)
    if missing:
        print('in ', e, 'missing: ', missing)
    for i in range(xy[1] - xy[0]):
        if table2.iloc[i,0] in player_list:
            r = {'Player' : table2.iloc[i,0],'Event' : e,
                 'Certs' : table2.iloc[i,1],
                 'BeginCash' : table2.iloc[i,2],
                 'Cash'  : table2.iloc[i,3]}
            players_cash_df = players_cash_df.append(r, ignore_index=True)

def fix1_18oe(str):
    if str[0:5] == 'Limit':
        return 'Limit'
         
'''
-----------------------------------------------------------------------
----------------------- START MAIN ------------------------------------
-----------------------------------------------------------------------
'''

'''
-----------------------------------------------------------------------
----------------------- Set 18oe specific values --------------------
-----------------------------------------------------------------------
'''
lastSR = 'SR 3'
lastOR = 'OR 2b'
# fn = 'vijver_SR3'       # the 18oe filename used in Google Sheets
fn = '18OE_CoenAnton_knopje'
fs = 'client_secret.json' # file containing secret hash and email
ar = 100                # ar: al rows; number of rows to read from each sheet
sr = 2                  # skiprows; skip two lines for headers on the info sheet
gi = 'Info'             # general info worksheet

player_cash_c = [2, 8, 1, 6] # searchhere(coord_player_cash, 'SR 1')
player_info_list = ['Players', '29', 'Cash', 'Sell/Buy'] # check_coordinates(event_list, coord_player_cash, player_list, player_info_list)
comp_c = [1, 33, 30, 84]  # coordinaties of the all company info
player_c = [1, 7, 30, 82] # coordinates of the player shares table

pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
'''
-----------------------------------------------------------------------
----------------------- Access Google Sheets -------------------------
-----------------------------------------------------------------------
'''
scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
creds = ServiceAccountCredentials.from_json_keyfile_name(fs, scope)
client = gspread.authorize(creds)
# give access in this Google sheet to the e-mail in secret file
GoogleSheet = client.open(fn)

'''
-----------------------------------------------------------------------
------------- Get general info like players companies trains-----------
-----------------------------------------------------------------------
'''
worksheet = GoogleSheet.worksheet(gi)
table1 = get_as_dataframe(worksheet, nrows = ar, skiprows = sr,
                          evaluate_formulas=True, headers=None)

player = table1.iloc[0:30, 0:1]
player_l = list(pd.Series.dropna(player['Player']))
# print('player.columns', player.columns)

company = table1.iloc[0:30, 1:3]
company_l = list(pd.Series.dropna(company['Company']))

train = table1.iloc[0:30, 3:5]
train.dropna(inplace = True)
train_l = list(pd.Series.dropna(train['Train']))
train_d = train.set_index('Train').T.to_dict('list')
event = table1.iloc[0:30, 5:7]
event_l = list(pd.Series.dropna(event['Event']))

marketvalue = table1.iloc[0:30, 7:9]
marketvalue.dropna(inplace=True)
marketvalue_l = list(pd.Series.dropna(marketvalue['marketvalue']))

# translate_comp = pd.DataFrame(columns = ['RowNameIn', 'RowName'])
translate_comp = table1.iloc[0:30, 9:11]
translate_comp.dropna(inplace=True)

Name18oe_l = list(pd.Series(translate_comp['Name18oe']))
MyName_l = list(pd.Series(translate_comp['MyName']))

'''
-----------------------------------------------------------------------
----- Make tables with company info, player shares ------------------
-----------------------------------------------------------------------
'''

comp_info = pd.DataFrame(columns = MyName_l)
players_shares_df = pd.DataFrame(columns = ['Event', 'Player', 
                                            'Company', 'Shares'])
players_cash_df = pd.DataFrame( columns = ['Player', 'Event', 
                                           'Certs', 'Cash'])
for e in event_l:
    print('Processing event ', e)
    worksheet = GoogleSheet.worksheet(e)
    table1 = get_as_dataframe(worksheet,
                              nrows=ar,
                              evaluate_formulas=True,
                              headers=None)
    fixtable1(19, 30, 6, "Limit ", 'Trains')
    make_comp_info(e, table1, company_l, 
                            train_d, comp_c, 
                            Name18oe_l, MyName_l)
    make_players_shares_df(e, table1, player_l, company_l, player_c)
    make_players_cash_df(e, table1, player_l, player_cash_c)

print('length compinfo: ',len(comp_info))
print('should be equal to: #comp * #events: ', len(company_l), '*', 
    len(event_l), '=', len(company_l) * len(event_l))   
print('players * shares: ', len(players_shares_df))
print(len(players_cash_df), '=', len(player_l), '*', len(event_l))


'''   
-----------------------------------------------------------------------
---------------- Join some stuff ----------------------------------
-----------------------------------------------------------------------
'''
# add average value of a city (depends on Event)
comp_all = comp_info.merge(event, on='Event', how='left')
print(len(comp_all), '=', len(comp_info))

comp_all['ExpectRunPS'] = comp_all['trainlength'] * comp_all['AvgCity'] / 10
print('1 comp_all still', len(comp_all))

# print(comp_all.columns)
# print(marketvalue.columns)
# print(marketvalue)
comp_all = comp_all.merge(marketvalue, on = 'marketvalue', how = 'left')
# print('2 comp_all still', len(comp_all))

comp_all['ShareInc'] = comp_all['NextMV'] - comp_all['marketvalue']
comp_all['ShareInc'] = comp_all['ShareInc'].fillna(0)
# print('3 comp_all still', len(comp_all))

comp_all['PercInc'] = 100 * (comp_all['ExpectRunPS'] + comp_all['ShareInc'])/comp_all['marketvalue']
comp_all.sort_values(by='PercInc', inplace=True, ascending = False)
print('4 comp_all still', len(comp_all))

print("what company should i buy first: ")
print(comp_all.loc[comp_all['Event'] == lastOR][['Company', 
      'marketvalue', 'ExpectRunPS', 'ShareInc', 'PercInc']])


players_comp_all = players_shares_df.merge(comp_all, 
                                           on=['Company', 'Event'], 
                                           how='left',
                                           suffixes = [None, '_comp'])
print(len(players_comp_all))

players_comp_len = players_comp_all.groupby(['Player', 'Company', 'Event'])['trainlength'].sum().reset_index()
print(len(players_comp_len))

players_comp_all['ShareLength'] = players_comp_all['Shares'] * players_comp_all['trainlength']
players_comp_all['ShareLength'] = players_comp_all['ShareLength'].fillna(0)
# print(players_comp_all.loc[players_comp_all['Event'] == lastOR])

print('who is winning: ')
players_length = players_comp_all.groupby(['Player', 'Event'])['ShareLength'].sum().reset_index()
print(players_length[players_length['Event'] == lastSR])

'''
-----------------------------------------------------------------------------
------------------- Prepare comparing current SR with previous OR xb---------
-----------------------------------------------------------------------------
'''

# step 1: make a dataframe with previous and current event
prev_cur = make_prev_cur(event_l)
# print(prev_cur)

# step 2a: add the previous event to the players_cash
players_cash_info = players_cash_df.merge(prev_cur, on='Event', how='left')

# step2b: combine players cash for current and previous event
players_cash_info = players_cash_info[['Player', 'Event', 'PrevEvent', 
                                       'Cash', 'BeginCash']].merge(
        players_cash_df[['Player', 'Event', 'Cash']], 
        left_on = ['Player', 'PrevEvent'],
        right_on= ['Player', 'Event'], 
        suffixes=('','_prev'))
# print(players_cash_info)

# step 3a: add the previous event to the players_shares
player_share_info = players_shares_df.merge(prev_cur, on='Event', how='left')

#step 3b: combine players shares for current and previous event:
player_share_info = player_share_info[['Player', 'Company', 'Event',
                                       'PrevEvent', 'Shares']].merge(
        player_share_info[['Player', 'Company', 'Event', 'Shares']],
        left_on = ['Player', 'Company', 'PrevEvent'],
        right_on = ['Player', 'Company', 'Event'],
        suffixes = ['', '_prev'])
# print(player_share_info[player_share_info['Event'] == lastSR])
# print(player_share_info.columns)

# step 4a: add the previous event to the comp_info (to compare marketvalue)
comp_mv = comp_info[['Company', 'Event', 'marketvalue']].merge(prev_cur, 
                      on='Event', how='left')
# print(comp_info2)
comp_mv = comp_mv.merge(comp_mv[['Company', 'Event', 'marketvalue']], 
                              left_on=['Company', 'PrevEvent'],
                              right_on=['Company', 'Event'],
                              how='left',
                              suffixes=['', '_prev'])
# print(comp_mv)
'''
-----------------------------------------------------------------------------
---- Check if BeginCash, FinalCash in SR computes with shares bought---------
-----------------------------------------------------------------------------
'''
# step 1: shares and marketvalue for this and previous event per
# player * company on event
player_share_spent = player_share_info[['Player', 'Company', 
                                        'Event', 'Shares', 
                                        'Shares_prev']]\
                                        .merge(comp_mv[['Company', 
                                                        'Event', 'marketvalue', 
                                                        'marketvalue_prev']], 
on=['Company', 'Event'], how='left', suffixes=['','_prev'])
print(len(player_share_info), len(player_share_spent))

# step 2: amount of money spent per player, share in an event
player_share_spent['Spent'] = (player_share_spent['Shares'] \
             - player_share_spent['Shares_prev']) \
             * player_share_spent['marketvalue']
player_share_spent['Spent'] = player_share_spent['Spent'].fillna(0)
# print(player_share_spent)
# print(len(player_share_info), len(player_share_spent))

# step 3: amount of money spent per player on an event
player_spent = player_share_spent.groupby(['Player', 'Event'])['Spent'].sum().reset_index()
print(player_spent[['Player', 'Event', 'Spent']])

# step 4: compare with begincash and cash
player_cash_compare = players_cash_info.merge(player_spent, on=['Player', 'Event'],
                                             how='left')
print(player_cash_compare)


