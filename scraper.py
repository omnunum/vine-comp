# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 22:18:28 2014

@author: sunshine
"""

import pandas as pd
import json, urllib
import os

def get_top_pages(pages):
    comp = pd.DataFrame()
    for page in xrange(1, pages + 1):
        response =  urllib.urlopen('https://api.vineapp.com/timelines/popular?page=%d' % page)
        vines = json.loads(response.read())
        #the meat of the response we're looking for, vine entries
        df = pd.DataFrame.from_dict(vines['data']['records'])
        if pages == 1:
            comp = df.copy()
        else:
            comp = pd.concat([df, comp], ignore_index=True)
    #expands the loops object into count and velocity columns
    loops = comp['loops'].apply(lambda x: pd.Series(x)).unstack().unstack().T[['count', 'velocity']]
    #concats the new columns to the previous page composite
    comp = pd.concat([comp.reset_index(), loops.reset_index()], axis=1)
    #takes just the columns we need
    subset = comp[['count', 'velocity', 'videoUrl', 'permalinkUrl', 'description']]
    #sorts the rows by the loop count, drop duplicates, and resets the index (because we're returning a table ofter sorting)
    sort = subset.sort(columns=['count']).drop_duplicates(subset='permalinkUrl').reset_index()
    return sort.copy()
    
#rewrite to use the dataframe not just a list of urls, need to use the permalink
#to name the file better
def download_vines(urls):
    for url in urls:
        # Split on the rightmost / and take everything on the right side of that
        name = url.rsplit('/', 1)[-1]    
        # Combine the name and the downloads directory to get the local filename
        filename = os.path.join(os.path.dirname('__file__'), 'cache/' + name)      
        # Download the file if it does not exist
        if not os.path.isfile(filename):
            urllib.urlretrieve(url, filename)