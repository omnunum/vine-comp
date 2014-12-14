# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 22:18:28 2014

@author: sunshine
"""

import pandas as pd
import os.path as osp
import sys
import requests as rq


#sorts the rows by the loop count, drop duplicates, and resets the index
def sort_clean(data):
    data_sorted = data.sort(columns=['count'], ascending=False)
    data_cleaned = data_sorted.drop_duplicates(subset='permalinkUrl')
    data_reindex = data_cleaned.reset_index(drop=True)
    return data_reindex


#gets the absolute path of the directory and append the path to it
def append_path(path):
    return osp.join(osp.dirname(osp.abspath(sys.argv[0])), path)


#checks all the id's of the vines to see if there is a corresponding file
#in the specified directory, if wrong directory method returns empty DataFrame
def vine_exists(data, directory):
    if directory in ['cache', 'render']:
        #filter lambda for the dataframe
        is_file = lambda vineid: osp.isfile(append_path(directory + '/' + str(vineid) + '.mp4'))
        datav = data[data['id'].map(is_file)]
        return datav
    else:
        return pd.DataFrame()


def get_top_pages(pages):
    #composite dataframe to hold all the compiled information
    comp = pd.DataFrame()
    #api page index starts at 1
    for page in range(1, pages + 1):
        url = 'https://api.vineapp.com/timelines/popular?page=%d' % page
        #vine object is the json object returned from the vine api
        vines = rq.get(url).json()
        #the meat of the json object we're looking for, vine entries
        df = pd.DataFrame.from_dict(vines['data']['records'])
        #if this is the first page, start comp as a copy of the page
        if page == 1:
            comp = df.copy()
        #else add current page to the comp
        else:
            comp = pd.concat([df, comp], ignore_index=True)
    #expands the loops column's objects into count and velocity columns
    loops = comp['loops'].apply(lambda x: pd.Series(x))
    unstacked = loops.unstack().unstack().T[['count', 'velocity']]
    #adds the new columns to the previous page composite
    comp[['count', 'velocity']] = unstacked
    #takes the columns we need
    subset = comp[['count', 'velocity', 'videoUrl',
                   'permalinkUrl', 'description', 'username']].copy()
    get_id = lambda x: x.rsplit('/', 1)[-1]
    subset['id'] = [get_id(perma) for perma in subset['permalinkUrl']]
    sort = sort_clean(subset)
    return sort


def download_vines(data):
    #zip the data we need so we can run through with one loop
    zipped = zip(data['videoUrl'], data['id'], data['description'])
    for url, perma, desc in zipped:
        name = perma
        filename = append_path('cache/' + name + '.mp4')
        # Download the file if it does not exist
        if not osp.isfile(filename):
            print('downloading ' + perma + ': ' + desc)
            with open(filename, 'wb') as fd:
                for chunk in rq.get(url, stream=True).iter_content(5000):
                    fd.write(chunk)


def update_records(data):
    #gets real path of file
    filename = append_path('records.csv')
    #if the file exsts, combine file with new data
    if osp.isfile(filename):
        records = pd.read_csv(filename, encoding='utf-8')
        comp = sort_clean(pd.concat([data, records], ignore_index=True))
        comp.to_csv(filename, index=False, encoding='utf-8')
    #9f file doesn't exist, save it for the first time
    else:
        data.to_csv(filename, index=False, encoding='utf-8')

if __name__ == "__main__":
    data = get_top_pages(2)
    download_vines(data)
    update_records(data)
