# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 22:18:28 2014

@author: sunshine
"""

import pandas as pd
import numpy as np
import os.path as osp
import sys
import getopt
from lxml import html
import requests as rq
from shared import *
from threading import Thread
from Queue import Queue
import datetime as dt

class ThreadWrite(Thread):
    def __init__(self, queue):
        self.q = queue
        Thread.__init__(self)
    
    def run(self):
        while True:
            data, file_path = self.q.get()
            try:
                update_records(data, file_path)
            except Exception as e:
                print(e)
            self.q.task_done()

class ThreadScrape(Thread):

    def __init__(self, queue):
        self.q = queue
        Thread.__init__(self)

    def run(self):
        while True:
            args = self.q.get()
            endpoint, term, feed, name, dir_path, pagelim, sq = args
            
            if not feed == '':
                feed = '/' + feed
            data = scrape(pagelim, 'timelines/' + endpoint, term=term + feed)

            if not data.empty:
                cutoff_date = (dt.datetime.now() - dt.timedelta(days=7)).isoformat()
                data = data[cutoff_date < data.created]
                sq.put((data, dir_path + '/' + name + '.csv'))
            else:
                print(term + ' came up empty')

            print(endpoint + ' ' + term + ' task completed')
            self.q.task_done()


class ThreadDLVines(Thread):
    """
        Threaded class to download vine video files using the requests library
        to chunk and save the data from the buffer.
    """
    def __init__(self, queue):
        self.q = queue
        Thread.__init__(self)

    def run(self):
        while True:
            #grab some data from the queue
            data, dir_path = self.q.get()
            url = data['videoUrl']
            vineid = str(data['id'])
            desc = data['description']

            if isinstance(desc, basestring) and not pd.isnull(desc):
                desc = enc_str(desc)
            else:
                desc = ''

            filename = dir_path + 'cache/' + vineid + '.mp4'

            # Download the file if it does not exist
            if not osp.isfile(filename):
                print('downloading ' + vineid + ': ' + desc)
                with open(filename, 'wb') as fd:
                    for chunk in rq.get(url, stream=True).iter_content(5000):
                        fd.write(chunk)

            self.q.task_done()


def scrape(pagelim, endpoint, term=''):
    """
        Retrieves all pages of the specified URL format up to the page limit.
        Most of this code is spent on the loop structure to make sure we can
        automatically get all the pages needed without storing empty data.
        The latter half of this function is dedicated to making sure all the data
        we need is typecasted correctly.
        
        pagelim
            Maximum number of pages to fetch
        endpoint
            API endpoint type, e.g. 'timelines/channels', 'timelines/users'
        term
            optional term to add onto url, e.g. 'comedy', '934940633704046592'
        
    """
    comp = pd.DataFrame()
    success = True
    page = 0
    url = 'https://vine.co/api/{0}/{1}'.format(endpoint, term)
    vines = ''

    while success:
        if page:
            url = url.split('?')[0] + '?page=' + str(page)
        else:
            print('Attempting to scrape: ' + url)

        try:
            vines = rq.get(url).json()
        except Exception as e:
            print(e)

        if vines['success']:
            if len(vines['data']['records']) > 0:
                #the meat of the json object we're looking for, vine entries
                df = pd.DataFrame.from_dict(vines['data']['records'])
                print('Scrape successful! Downloaded {0} entries'.format(len(df.index)))
                #if this is the first page, start comp as a copy of the page
                if page == 0:
                    comp = df.copy()
                #else add current page to the comp
                else:
                    comp = pd.concat([df, comp], ignore_index=True)

                #a pagelim of -1 means grab all the pages available/no limit
                if page < pagelim or pagelim == -1:
                    page += 1
                else:
                    print('Finished scraping at: ' + url)
                    success = False
            else:
                print('Finished scraping at: ' + url)
                success = False
        else:
            print('API request failed, {0}/{1} not valid'.format(endpoint, term))
            success = False

    if page:
        #expands the loops column's objects into count and velocity columns
        loops = comp['loops'].apply(lambda x: pd.Series(x))
        unstacked = loops.unstack().unstack().T[['count', 'velocity']]

        #takes the columns we need
        subset = comp[['videoUrl', 'permalinkUrl', 'username', 'created']].astype(basestring).copy()

        #adds the new columns to the previous page(s) composite
        subset['count'] = unstacked['count'].astype(int)
        subset['velocity'] = unstacked['velocity'].astype(float)
        subset['description'] = comp['description'].astype(basestring).map(enc_str)

        #extracts the vineid from the right side of the permalink
        get_id = lambda x: x.rsplit('/', 1)[-1]
        subset['id'] = [get_id(perma) for perma in subset['permalinkUrl']]
        sort = sort_clean(subset)

        return sort
    else:
        return pd.DataFrame()


def download_vines(data):
    """
        Creates a queue for downloading the vine video files, populates it with
        the passed DataFrame row data.
    """
    if isinstance(data, pd.DataFrame):
        q = Queue()
        thread_pool(q, 5, ThreadDLVines)
    
        #we need to pass in the root path so the thread doesn't get confused
        dir_path = ap('')
    
        for i, row in data.iterrows():
            q.put((row, dir_path))
    
        q.join()
    else:
        print('data for vine downloading not found')


def update_records(data, filepath):
    """
        Adds new passed data to the existing file

        data
            Pandas DataFrame: contains the vine metadata
        filepath
            filepath for csv record
    """

    #if the file exsts, combine file with new data
    if osp.isfile(filepath):
        records = pd.read_csv(filepath, encoding='utf-8')
        comp = sort_clean(pd.concat([data, records], ignore_index=True))
        comp.to_csv(filepath, index=False, encoding='utf-8')
    else:
        #save it for the first time
        data.to_csv(filepath, index=False, encoding='utf-8')


def get_trending_tags():
    """
        Retrieves currently trending tags
    """
    #grabs the static html page data
    explore_page = rq.get('https://vine.co/explore')

    #creates an html tree from the data
    tree = html.fromstring(explore_page.text)

    #XPATH query to grab all of the trending tag link element strings
    tags = tree.xpath('//section[@id="trending"]//a/text()')
    data = [dt.now(), ' '.join(tags)]

    try:
        update_records(pd.DataFrame(data, ap('meta/trending')))
    except Exception as e:
        print(e)

    return tags


def scrape_all(pagelim):
    '''
        Scrapes all available sources of information, including playlists,
        channels, and trending tags.
    '''
    channels = {'comedy': 1, 'art': 2, 'places': 5, 'family': 7,
                'food': 10, 'music': 11, 'fashion': 12, 'news': 14,
                'scary': 16, 'animals': 17}

    q, sq = Queue(), Queue()
    thread_pool(q, 10, ThreadScrape)
    thread_pool(sq, 1, ThreadWrite)
    for channel, cid in channels.iteritems():
        #queue data: endpoint, term, feed, name, dir_path
        q.put(('channels', str(cid), 'popular', channel, ap('meta'), pagelim, sq))

    playlists = []

    try:
        playlists = pd.read_csv(ap('meta/playlists.csv'), dtype=basestring)
        playlists = playlists.replace(np.nan, '', regex=True)
    except Exception as e:
        print(e)

    for i, row in playlists.iterrows():
        tags = str(row['tags']).split(' ')
        users = str(row['users']).split(' ')

        for tag in tags:
            if not pd.isnull(tag) and tag not in ['nan', '']:
                q.put(('tags', tag, '', row['name'], ap('meta'), pagelim, sq))

        for user in users:
            if not pd.isnull(user) and user not in ['nan', '']:
                q.put(('users', user, '', row['name'], ap('meta'), pagelim, sq))

    q.join()


if __name__ == "__main__":
    options, remainder = getopt.gnu_getopt(sys.argv[1:], ':ua',
                                           ['download=', 'flush=',
                                            'update=', 'archive'])
    for opt, arg in options:
        if opt == '--flush':
            if arg == 'render':
                flush_render()
            elif arg == 'all':
                flush_all()
        elif opt == '--download':
            data = load_top_n(90, arg)
            if isinstance(data, pd.DataFrame):
                download_vines(data)
                update_records(data, arg)
            else:
                print('could not get vine data for downloading, maybe wrong name?')
        elif opt == '--update':
            try:
                int(arg)
                scrape_all(int(arg))
            except ValueError as e:
                print(e)
                print('I need a number to set the max page limit')
        elif opt == '-u':
            scrape_all(-1)
        elif opt in ['--archive', '-a']:
            archive_metadata()
