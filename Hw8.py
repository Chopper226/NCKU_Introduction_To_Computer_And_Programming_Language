import requests
import pandas as pd

#https://data.gov.tw/dataset/40448

url = 'https://data.epa.gov.tw/api/v2/aqx_p_432?api_key=e8dd42e6-9b8b-43f8-991e-b3dee723a52d&limit=1000&sort=ImportDate%20desc&format=JSON'
data = requests.get(url)             
data_json = data.json()   
output = [['county','sitename','aqi','pm2.5','空氣品質']] 


for i in data_json['records']:      
    output.append([i['county'],i['sitename'],i['aqi'],i['pm2.5'],i['status']])

pd.set_option('display.unicode.ambiguous_as_wide' , True)
pd.set_option('display.unicode.east_asian_width' , True)
print( pd.DataFrame(output[1:] , columns=output[0]) )