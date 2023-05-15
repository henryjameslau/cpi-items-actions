# cpi-items-actions
This repo uses Github actions to format CPIH data for the [Shopping Prices Comparison Tool](https://www.ons.gov.uk/economy/inflationandpriceindices/articles/shoppingpricescomparisontool/2023-05-03).

To prepare the metadata, copy the columns from the unchained sheet. Set the `AVERAGE_PRICE` column to a number (to remove £) and to 3dp. 

To prepare the unchained values, remove the metadata columns except the `ITEM_ID` column. Remove any columns before the reference year.

There are two reference values in the python script, the reference month for average prices when the timeseries starts for items which is normally 5 years, so in 2023 the start was Jan 2018.

You can run the action to manually get the script to run and update files through the actions tab.

