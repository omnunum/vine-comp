# -*- coding: utf-8 -*-
"""
Created on Mon Dec 15 13:11:38 2014

@author: sunshine
"""
import os
import os.path as osp
import sys
import pandas as pd
import re
import subprocess
from unicodedata import normalize


#populates a threadpool in the given queue with the passed class
def thread_pool(q, maxthreads, ThreadClass):
    for x in range(maxthreads):
        t = ThreadClass(q)
        t.setDaemon(True)
        t.start()


#converts utf-8 strings to ascii by dropping invalid characters
def enc_str(x):
    if isinstance(x, unicode):
        return normalize('NFKD', x).encode('ascii', 'ignore')
    else:
        return str(x)


#sorts the rows by the loop count, drop duplicates, and resets the index
def sort_clean(data):
    data_sorted = data.sort(columns=['count'], ascending=False)
    data_cleaned = data_sorted.drop_duplicates(subset='permalinkUrl')
    data_reindex = data_cleaned.reset_index(drop=True)
    return data_reindex


#gets the absolute path of the directory and append the path to it
def ap(path):
    return osp.join(osp.dirname(osp.abspath(sys.argv[0])), path)


#checks all the id's of the vines to see if there is a corresponding file
#in the specified directory, if wrong directory method returns empty DataFrame
def exists(data, directory):
    if directory in ['cache', 'render']:
        #filter lambda for the dataframe
        is_file = lambda vineid: osp.isfile(ap(directory + '/' + str(vineid) + '.mp4'))
        datav = data[data['id'].map(is_file)]
        return datav
    else:
        return pd.DataFrame()


def delete_file(path):
    path = ap(path)
    try:
        if osp.isfile(path):
            os.unlink(path)
    except Exception as e:
        print(e)


def load_top_n(n, name):
    path = ap('meta/' + name + '.csv')
    if osp.isfile(path):
        try:
            df = pd.read_csv(path, encoding='utf-8')
            return sort_clean(df).ix[:n - 1, :]
        except Exception as e:
            print(e)


#gets rid of all files in the render and cache directories as well as
#the vine records csv and leftover temp mp3 audio clips
def flush_all():
    directories = ['render/', 'cache/', 'meta/']
    for directory in directories:
        print('removing all files in: ' + directory)
        for vfile in os.listdir(ap(directory)):
            if not re.match('playlists.csv', vfile):
                delete_file(directory + vfile)
    for vfile in os.listdir(ap('')):
        if vfile.endswith('.mp3'):
            print('removing: ' + vfile)
            delete_file(vfile)


def flush_render():
    for directory in ['render/', 'render/finals/']:
        print('removing all files in: ' + directory)
        for vfile in os.listdir(ap(directory)):
            delete_file(directory + vfile)


def group_data(data, group_size):
    return [data[x:x+group_size] for x in range(0, len(data), group_size)]
