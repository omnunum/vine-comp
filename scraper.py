# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 22:18:28 2014

@author: sunshine
"""

import pandas as pd
import json
import urllib
import os.path as osp


#sorts the rows by the loop count, drop duplicates, and resets the index
def sort_clean(data):
    sorted = data.sort(columns=['count'], ascending=False)
    cleaned = sorted.drop_duplicates(subset='permalinkUrl')
    reset = cleaned.reset_index(drop=True)
    return reset


#gets the absolute path of the directory and append the path to it
def append_path(path):
    return osp.join(osp.dirname(osp.abspath(__file__)), path)


def get_top_pages(pages):
    comp = pd.DataFrame()
    for page in xrange(1, pages + 1):
        url = 'https://api.vineapp.com/timelines/popular?page=%d' % page
        response = urllib.urlopen(url)
        vines = json.loads(response.read())
        #the meat of the response we're looking for, vine entries
        df = pd.DataFrame.from_dict(vines['data']['records'])
        if page == 1:
            comp = df.copy()
        else:
            comp = pd.concat([df, comp], ignore_index=True)
    #expands the loops object into count and velocity columns
    loops = comp['loops'].apply(lambda x: pd.Series(x))
    unstacked = loops.unstack().unstack().T[['count', 'velocity']]
    #adds the new columns to the previous page composite
    comp[['count', 'velocity']] = unstacked
    #takes just the columns we need
    subset = comp[['count', 'velocity', 'videoUrl',
                   'permalinkUrl', 'description']].copy()
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
            print'downloading ' + perma + ': ' + desc
            urllib.urlretrieve(url, filename)


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
