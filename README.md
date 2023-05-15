# cpi-items-actions
This repo uses Github actions to format CPIH data for the [Shopping Prices Comparison Tool](https://www.ons.gov.uk/economy/inflationandpriceindices/articles/shoppingpricescomparisontool/2023-05-03). The action is set to run at 7:01 every week day between the 14 and 22 of each month. It then runs the [python script](https://github.com/henryjameslau/cpi-items-actions/blob/main/postprocess.py). 

To prepare the metadata file from the excel sheet provided by the business area, copy the columns from the unchained sheet. Set the `AVERAGE_PRICE` column to a number (to remove £) and to 3dp. 

To prepare the unchained values, remove the metadata columns except the `ITEM_ID` column. Remove any columns before the reference year.

There are two reference values in the python script, the reference month for average prices when the timeseries starts for items which is normally 5 years, so in 2023 the start was Jan 2018.

You can run the action to manually get the script to run and update files through the actions tab.

# How it works
The script reads the unchained file to read the latest month. It then goes to the ONS website to the [prices and indices dataset](https://www.ons.gov.uk/economy/inflationandpriceindices/datasets/consumerpriceindicescpiandretailpricesindexrpiitemindicesandpricequotes) and find the first link that contains some keywords and then downloads that file. It looks at the month in that file and compares it to the latest month from the unchained.csv file. 

If the month is different, it adds on that column to the unchained file. If it's January, it chains it onto December. Once the unchained file is updated, the script run through and created the chained indices, average prices, monthly growth and annual growth. 

The datadownload file then gets updated with the metadata, chained, average prices, monthly and annual growth. And the individual csv files are saved. 
