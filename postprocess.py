import pandas as pd
import requests
import urllib.request, json 
import re
import io
import time
from datetime import datetime,date

# set average price reference month
avgpriceRefMonth=pd.Timestamp('2023-01-01 00:00:00')

# starting reference point
startref=pd.Timestamp('2018-01-01 00:00:00')

custom_date_parser = lambda x: datetime.strptime(x, "%Y%m")

#read in metadata
meta = pd.read_csv('./metadata.csv',index_col=0,parse_dates=['ITEM_START'],date_parser=custom_date_parser)

# define a function to split a string at a certain occurance of a separator

# https://stackoverflow.com/questions/36300158/split-text-after-the-second-occurrence-of-character
def split(strng, sep, pos):
    strng = strng.split(sep)
    return sep.join(strng[:pos]), sep.join(strng[pos:])

# read in unchained csv
unchained = pd.read_csv('unchained.csv')

#find the last month in the unchained file
latestmonth=datetime.strptime(unchained.columns[-1],"%Y-%m-%d %H:%M:%S")

# first get the data.json from the cpi items and prices page

with requests.Session() as s:
    r=s.get("https://corsproxy.io/?https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes/data",headers={'User-Agent': 'Mozilla/5.0'})
    data = r.json()
    datasets = data['datasets']


#go through the dataset and find the first one which doesn't contain the word framework, glossary or /pricequotes. The url includes pricesquotes so that slash is important. Save the index as the variable match  
for i,dataset in enumerate(datasets):
    match = i
    if('framework' not in dataset['uri'] and 'glossary' not in dataset['uri'] and '/pricequotes' not in dataset['uri']):
        break
    
#get the uri of the items dataset we want
items = data['datasets'][match]['uri']
print('dataset='+items)

#get the month and year from the uri
date=split(items,'itemindices',2)[1]
print('the date from url:'+date)

#parse it as a date
itemmonth=datetime.strptime(date,"%B%Y")

print(itemmonth,latestmonth,itemmonth!=latestmonth)
# check date to see if you need to download a file
if(itemmonth!=latestmonth):
    print('month from indices is different to latest month in unchained csv')
    # download the file
    with requests.Session() as s:
        r=s.get("https://corsproxy.io/?https://www.ons.gov.uk"+items+"/data",headers={'User-Agent': 'Mozilla/5.0'})
        itemspage = r.json()
        csv = itemspage['downloads'][0]['file']
    
    # get the csv of the latest indices

    with requests.Session() as s:
        download = s.get("https://corsproxy.io/?https://www.ons.gov.uk/file?uri="+items+"/"+csv,headers={'User-Agent': 'Mozilla/5.0'})
        df=pd.read_csv(io.StringIO(download.content.decode('utf-8')))
        
    #get the index date which is the first cell
    index_date=df.iloc[0,0]

    # parse columns as dates in unchained
    # https://stackoverflow.com/questions/42472418/parse-file-headers-as-date-objects-in-python-pandas
    columns = {}
    for col in unchained.columns:
        try:
            columns[col] = datetime.strptime(str(col), "%Y-%m-%d  %H:%M:%S")
        except ValueError:
            pass
    unchained.rename(columns=columns, inplace=True)
    
    #join it onto existing csv
    un=unchained.merge(df[['ITEM_ID','ALL_GM_INDEX']].rename(columns={"ALL_GM_INDEX": datetime.strptime(str(index_date),"%Y%m")}),on='ITEM_ID',how='left')
        
    #if last date is Jan, then chain it to december
    if(un.columns[-1].month == 1):
        print('chaining jan')
        jancol=un.columns[-1]
        prevdec=un.columns[-2]
        for index,value in un.iloc[:,-1].items():
            un.at[index,jancol]=un.loc[index,prevdec]*value/100
    
    un.set_index("ITEM_ID",inplace=True)
    
    #and save it
    un.to_csv('unchained.csv')

    #create a copy of unchained to create the chained indices
    chained = un.copy()

    for col in chained:
        for i, row_value in chained[col].items():
            # print(col,i,row_value,meta.loc[i,'ITEM_START'])
            if(col>=meta.loc[i,'ITEM_START']):
                if(col==startref):
                    chained.at[i,col]=100
                # elif(col==meta.loc[i,'ITEM_START']):
                #     sample.at[i,col]=row_value
                elif(col<=startref+pd.tseries.offsets.DateOffset(years=1)):
                    chained.at[i,col]=row_value
                else:
                    if(col.month==1 and col>startref+pd.tseries.offsets.DateOffset(years=1)):
                        chained.at[i,col]=float(row_value)*float(chained.loc[i][datetime(col.year-1,12,1)])/100
                    else:
                        chained.at[i,col]=float(row_value)*float(chained.loc[i][datetime(col.year,1,1)])/100
                        
            elif(col==meta.loc[i,'ITEM_START']-pd.tseries.offsets.DateOffset(months=1)):
                chained.at[i,col]=100
                
            else:
                chained.at[i,col]=None

    chained.to_csv('chained.csv')

    # Then calculate average prices
    avgprice=chained.copy()

    for col in avgprice:
        for i, row_value in avgprice[col].items():
            if(row_value==None):
                avgprice.at[i,col]=None
            else:
                avgprice.at[i,col]=float(row_value)/ \
                float(chained.loc[i,avgpriceRefMonth])* \
                float(meta.loc[i,'AVERAGE_PRICE'])

    avgprice.to_csv('avgprice.csv')

    # calculate annual growth
    annualgrowth=chained.copy()

    for col in annualgrowth:
        for i, row_value in annualgrowth[col].items():
            if(col<meta.loc[i,'ITEM_START']+pd.tseries.offsets.DateOffset(years=1)):
                annualgrowth.at[i,col]=None
            else:
                if(col<pd.Timestamp("2018-01-01 00:00:00")):
                    annualgrowth.at[i,col]=None
                else:
                    annualgrowth.at[i,col]=(float(row_value)- \
                    float(chained.loc[i,col-pd.tseries.offsets.DateOffset(years=1)])) * 100 / \
                    float(chained.loc[i,col-pd.tseries.offsets.DateOffset(years=1)])
                    
                    
    annualgrowth.to_csv('annualgrowth.csv')

    # calculate monthly growth
    monthlygrowth=chained.copy()

    for col in monthlygrowth:
        for i, row_value in monthlygrowth[col].items():
            if(col<meta.loc[i,'ITEM_START']+pd.tseries.offsets.DateOffset(months=1)):
                monthlygrowth.at[i,col]=None
            else:
                if(col<pd.Timestamp("2017-02-01 00:00:00")):
                    monthlygrowth.at[i,col]=None
                else:
                    monthlygrowth.at[i,col]=(float(row_value)- \
                    float(chained.loc[i,col-pd.tseries.offsets.DateOffset(months=1)])) * 100 / \
                    float(chained.loc[i,col-pd.tseries.offsets.DateOffset(months=1)])
                    
    monthlygrowth.to_csv('monthlygrowth.csv')

    #turn it into a excel datadownload file
    with pd.ExcelWriter("datadownload.xlsx") as writer:
        meta.to_excel(writer, sheet_name="metadata")  
        un.to_excel(writer, sheet_name="unchained")
        avgprice.to_excel(writer, sheet_name="averageprice")
        monthlygrowth.to_excel(writer, sheet_name="monthlygrowth")
        annualgrowth.to_excel(writer,sheet_name="annualgrowth")
    
