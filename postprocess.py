import pandas as pd
import requests
# import urllib.request
import json 
import time
from datetime import datetime,date
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService 
from webdriver_manager.chrome import ChromeDriverManager 

# set average price reference month
avgpriceRefMonth=pd.Timestamp('2022-01-01 00:00:00')

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
latestmonth=datetime.strptime(unchained.columns[-1],"%d/%m/%Y  %H:%M")

# first get the data.json from the cpi items and prices page

# with urllib.request.urlopen("https://corsproxy.io/?https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes/data",headers={'User-Agent': 'Mozilla/5.0'}) as url:
#     data = json.load(url)
#     datasets=data['datasets']

with requests.Session() as s:
    r=s.get("https://corsproxy.io/?https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes/data",headers={'User-Agent': 'Mozilla/5.0'})
    data = r.json()
    datasets = data['datasets']
# print('preselenium')
# options = webdriver.ChromeOptions() 
# options.add_argument('--headless=new') 
# with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options) as driver: 
#     print('selenium1')
#     driver.get("https://corsproxy.io/?https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes/data")
    
#     time.sleep(1)
#     print(driver.title)
#     text= driver.find_element(By.TAG_NAME,'pre').text

#     data = json.loads(text)
#     datasets = data['datasets']
    
#     # closing browser
#     driver.close()

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
    with urllib.request.urlopen("https://corsproxy.io/?https://www.ons.gov.uk"+items+"/data",headers={'User-Agent': 'Mozilla/5.0'}) as itemsurl:
        itemspage = json.load(itemsurl)
        csv=itemspage['downloads'][0]['file']

    with requests.Session() as s:
        r=s.get("https://corsproxy.io/?https://www.ons.gov.uk"+items+"/data",headers={'User-Agent': 'Mozilla/5.0'})
        itemspage = r.json()
        csv = itemspage['downloads'][0]['file']
    # print('selenium2')
    # with webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options) as driver: 
    #     driver.get("https://corsproxy.io/?https://www.ons.gov.uk"+items+"/data")
        
    #     # the browser was opened indeed
    #     time.sleep(1)

    #     itemsurl= driver.find_element(By.TAG_NAME,'pre').text
    #     itemspage = json.loads(itemsurl)
    #     csv = itemspage['downloads'][0]['file']
       
    #     # closing browser
    #     driver.close()
    
    # get the csv of the latest indices
    # df = pd.read_csv("https://corsproxy.io/?https://www.ons.gov.uk/file?uri="+items+"/"+csv)
    with requests.Session() as s:
        download = s.get("https://corsproxy.io/?https://www.ons.gov.uk/file?uri="+items+"/"+csv,headers={'User-Agent': 'Mozilla/5.0'})
        
        df=pd.read_csv(io.StringIO(download.content.decode('utf-8')))
        
    #get the index date which is the first cell
    index_date=df.iloc[0,0]
    #join it onto existing csv
    un=unchained.merge(df[['ITEM_ID','ALL_GM_INDEX']].rename(columns={"ALL_GM_INDEX": index_date}),on='ITEM_ID',how='left')

        
    # parse columns as dates
    # https://stackoverflow.com/questions/42472418/parse-file-headers-as-date-objects-in-python-pandas
    columns = {}
    for col in un.columns:
        try:
            columns[col] = datetime.strptime(str(col), "%Y%m")
        except ValueError:
            pass
    un.rename(columns=columns, inplace=True)
    
    
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
                if(col==pd.Timestamp('2017-01-01 00:00:00')):
                    chained.at[i,col]=100
                # elif(col==meta.loc[i,'ITEM_START']):
                #     sample.at[i,col]=row_value
                elif(col<=pd.Timestamp('2018-01-01 00:00:00')):
                    chained.at[i,col]=row_value
                else:
                    if(col.month==1 and col>pd.Timestamp('2018-01-01 00:00:00')):
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