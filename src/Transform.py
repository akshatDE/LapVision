import pandas as pd
from bs4 import BeautifulSoup
import os

def get_data():
    """
    This function reads the html files from the data folder and extracts the title, price, rating, disk_size, ram and link of the laptops.
    """
    data_dict ={'title':[],'price':[],'rating':[],'disk_size':[],'ram':[],'link':[]}

    for file in os.listdir('data'):
        try:
            with open(f'data/{file}','r') as file:
                data = file.read()
            soup = BeautifulSoup(data,'html.parser')
            title = soup.find_all('h2')[0].text
            price = soup.find_all('span',attrs={"class":'a-offscreen'})[0].text
            rating  = soup.find_all('span',attrs = { "class":"a-icon-alt"})[0].text.split()[0]
            disk_size = soup.find_all('span',attrs = {"class":"a-text-bold"})[-3].text
            ram = soup.find_all('span',attrs = {"class":"a-text-bold"})[-2].text
            tags = soup.find('a')
            link  = "https://amazon.com/" + tags['href']
            data_dict['title'].append(title)
            data_dict['price'].append(price)
            data_dict['rating'].append(rating)
            data_dict['disk_size'].append(disk_size)
            data_dict['ram'].append(ram)
            data_dict['link'].append(link)
        except Exception as e:
            print(e)
    return pd.DataFrame(data_dict)

def load_data():
    """
    This function loads the data from the csv file if it exists else it calls the get_data function to extract the data from the html files.
    """
    if os.path.exists('data.csv'):
        return pd.read_csv('data.csv')
    else:
        data = get_data()
        data.to_csv('laptop.csv',index=False)
        return data
if __name__ == '__main__':
    data = load_data()
    print(data.head())
    print(data.info())
