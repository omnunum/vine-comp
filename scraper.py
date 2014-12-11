# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 22:18:28 2014

@author: sunshine
"""

import pandas as pd
import json, urllib
import os
    
def sort_clean(data):
    return data.sort(columns=['count'], ascending=False).drop_duplicates(subset='permalinkUrl').reset_index(drop=True)
    
def append_path(path):
    return os.path.join(os.path.dirname('__file__'), path)
    
def get_top_pages(pages):
    comp = pd.DataFrame()
    for page in xrange(1, pages + 1):
        response =  urllib.urlopen('https://api.vineapp.com/timelines/popular?page=%d' % page)
        vines = json.loads(response.read())
        #the meat of the response we're looking for, vine entries
        df = pd.DataFrame.from_dict(vines['data']['records'])
        if page == 1:
            comp = df.copy()
        else:
            comp = pd.concat([df, comp], ignore_index=True)
    #expands the loops object into count and velocity columns
    loops = comp['loops'].apply(lambda x: pd.Series(x)).unstack().unstack().T[['count', 'velocity']]
    #adds the new columns to the previous page composite
    comp[['count', 'velocity']] = loops
    #takes just the columns we need
    subset = comp[['count', 'velocity', 'videoUrl', 'permalinkUrl', 'description']].copy()
    subset['id'] = [perma.rsplit('/', 1)[-1] for perma in subset['permalinkUrl']]
    #sorts the rows by the loop count, drop duplicates, and resets the index (because we're returning a table ofter sorting)
    sort = sort_clean(subset)
    return sort
    
def download_vines(data):
    for url, perma in zip(data['videoUrl'], data['id']):
        # Split on the rightmost / and take everything on the right side of that
        name = perma
        # Combine the name and the downloads directory to get the local filename
        filename = append_path('cache/' + name + '.mp4')      
        # Download the file if it does not exist
        if not os.path.isfile(filename):
            urllib.urlretrieve(url, filename)
    
def update_records(data):
    filename = append_path('records.csv')
    if os.path.isfile(filename):            
        records = pd.read_csv(filename, encoding='utf-8')
        comp = sort_clean(pd.concat([data, records], ignore_index=True))
        comp.to_csv(filename, index=False, encoding='utf-8')
    else:
        data.to_csv(filename, index=False, encoding='utf-8')
    
if __name__ == "__main__":
    data = get_top_pages(2)
    download_vines(data)
    update_records(data)