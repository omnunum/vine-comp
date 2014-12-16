# -*- coding: utf-8 -*-
"""
Created on Wed Dec 10 22:18:28 2014

@author: sunshine
"""

import pandas as pd
import os.path as osp
import sys
from lxml import html
import requests as rq
import subprocess
from shared import *
import thread


def scrape(endpoint, term=''):
    comp = pd.DataFrame()
    success = True
    page = 0
    url = 'https://vine.co/api/{0}/{1}'.format(endpoint, term)
    while success:
        if page > 0:
            url = url.split('?')[0] + '?page=' + str(page)
        try:
            #print('Attempting to scrape: ' + url)
            vines = rq.get(url).json()
        except Exception as e:
            print('Failed to scrape!')
            print(e)
        if len(vines['data']['records']) > 0:
            #the meat of the json object we're looking for, vine entries
            df = pd.DataFrame.from_dict(vines['data']['records'])
            #print('Scrape successful! Downloaded {0} entries'.format(len(df.index)))
            #if this is the first page, start comp as a copy of the page
            if page == 0:
                comp = df.copy()
            #else add current page to the comp
            else:
                comp = pd.concat([df, comp], ignore_index=True)
            page += 1
        else:
            success = False
    if page > 0:
        #expands the loops column's objects into count and velocity columns
        loops = comp['loops'].apply(lambda x: pd.Series(x))
        unstacked = loops.unstack().unstack().T[['count', 'velocity']]
        #adds the new columns to the previous page composite
        comp[['count', 'velocity']] = unstacked
        #takes the columns we need
        subset = comp[['count', 'velocity', 'videoUrl',
                       'permalinkUrl', 'description', 'username']].copy()
        #extracts the vineid from the permalink
        get_id = lambda x: x.rsplit('/', 1)[-1]
        subset['id'] = [get_id(perma) for perma in subset['permalinkUrl']]
        sort = sort_clean(subset)
        return sort
    else:
        return pd.DataFrame()


def download_vines(data):
    #zip the data we need so we can run through with one loop
    zipped = zip(data['videoUrl'], data['id'], data['description'])
    for url, perma, desc in zipped[:100]:
        name = perma
        filename = ap('cache/' + name + '.mp4')
        # Download the file if it does not exist
        if not osp.isfile(filename):
            print('downloading ' + perma + ': ' + desc)
            with open(filename, 'wb') as fd:
                for chunk in rq.get(url, stream=True).iter_content(5000):
                    fd.write(chunk)


def update_records(data, abs_path):
    #gets pathfile passed in before thread started
    filename = abs_path
    #if the file exsts, combine file with new data
    try:
        if osp.isfile(filename):
            records = pd.read_csv(filename, encoding='utf-8')
            comp = sort_clean(pd.concat([data, records], ignore_index=True))
            comp.to_csv(filename, index=False, encoding='utf-8')
        #if file doesn't exist, save it for the first time
        else:
            print
            data.to_csv(filename, index=False, encoding='utf-8')
    except Exception as e:
                print(e)


def upload_video(path):
    if osp.isfile(path):
        args = (['python2', ap('youtube_upload.py'),
                '--email=vinecompauthority@gmail.com',
                '--password=4u7H0r17Y',
                '--title=Hottest Vines of The Week 12-14-14',
                '--category=Comedy',
                path])
        subprocess.call(args)
    else:
        print('File not found: ' + path)


def get_trending_tags():
    explore_page = rq.get('https://vine.co/explore')
    tree = html.fromstring(explore_page.text)
    tags = tree.xpath('//section[@id="trending"]//a/text()')
    return tags


def scrape_channels(feed):
    def tscrape(cid, feed, channel, dir_path):
            cdf = scrape('timelines/channels', str(cid) + '/' + feed)
            if not cdf.empty:
                try:
                    update_records(cdf, dir_path + channel + '.csv')
                except Exception as e:
                    print(e)

    channels = {'comedy': 1, 'art': 2, 'cats': 3, 'dogs': 4, 'places': 5,
                'urban': 6, 'family': 7, 'specialfx': 8, 'sports': 9,
                'food': 10, 'music': 11, 'fashion': 12, 'healthandfitness': 13,
                'news': 14, 'weirdbanner': 15, 'scary': 16, 'animals': 17}
    for channel, cid in channels.iteritems():
        thread.start_new_thread(tscrape, (cid, feed, channel, ap('')))


def read_playlists():
    playlists = pd.read_csv('playlists.csv')


if __name__ == "__main__":
        if len(sys.argv) > 1:
            if '--flush' in sys.argv:
                flush_all()
            if '--update' in sys.argv:
                update_records(data)
            if '--download' in sys.argv:
                download_vines(data)
            if '--upload' in sys.argv:
                upload_video(ap('render/groups/FINAL RENDER.mp4'))
        else:
            scrape_channels('popular')
