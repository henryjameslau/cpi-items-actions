[Now superseeded by a fork of this repo but on ONSvisual.](https://github.com/ONSvisual/cpi-items-actions)

# cpi-items-actions
This repo uses Github actions to format CPIH data for the [Shopping Prices Comparison Tool](https://www.ons.gov.uk/economy/inflationandpriceindices/articles/shoppingpricescomparisontool/2023-05-03). The action is set to run at 7:01 every week day between the 14 and 27 of each month. It then runs the [python script](https://github.com/henryjameslau/cpi-items-actions/blob/main/postprocess.py). 

To prepare the metadata file from the excel sheet provided by the business area, copy the columns from the unchained sheet. Set the `AVERAGE_PRICE` column to a number (to remove £) and to 3dp. 

To prepare the unchained values, remove the metadata columns except the `ITEM_ID` column. Remove any columns before the reference year. You'll probably have to resave the file with column renamed in the date format expected by python which is `YYYY-MM-DD`.

There are two reference values in the python script, the reference month for average prices when the timeseries starts for items which is normally 5 years, so in 2023 the start was Jan 2018.

You can run the action to manually get the script to run and update files through the actions tab.

# How it works
The script reads the unchained file to read the latest month. It then goes to the ONS website to the [prices and indices dataset](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes) and find the first link that contains some keywords and then downloads that file. It looks at the month in that file and compares it to the latest month from the unchained.csv file. 

If the month is different, it adds on that column to the unchained file. If it's January, it chains it onto December. Once the unchained file is updated, the script run through and created the chained indices, average prices, monthly growth and annual growth. 

The datadownload file then gets updated with the metadata, chained, average prices, monthly and annual growth. And the individual csv files are saved. 

# Manually running the action
It's likely the action won't run on time so you can trigger the action to run manually. Click on the action tab at the top, then python on the left, then the run workflow button. You'll have to run a new workflow rather than reuse an old one as it doesn't work for some reason. 
![image](https://github.com/henryjameslau/cpi-items-actions/assets/2945099/c441bd94-5e42-4b00-86da-635624d76e7a)
