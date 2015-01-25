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
import datetime as dt
from unicodedata import normalize


def from_utc(utcTime,fmt="%Y-%m-%dT%H:%M:%S.%fZ"):
    """
    Convert UTC time string to time.struct_time
    """
    # change datetime.datetime to time, return time.struct_time type
    return dt.datetime.strptime(utcTime, fmt)


def thread_pool(q, maxthreads, ThreadClass):
    '''
        Populates a threadpool in the given queue with the passed class.

        q
            Queue instance to populate with threads
        maxthreads
            Maximum number of threads that will be allowed in the queue
        ThreadClass
            Class that extends Thread class to be run
    '''
    for x in range(maxthreads):
        t = ThreadClass(q)
        t.setDaemon(True)
        t.start()


def enc_str(utf):
    '''
        Converts utf-8 strings to ascii by dropping invalid characters.
    '''
    if isinstance(utf, unicode):
        return normalize('NFKD', utf).encode('ascii', 'ignore')
    else:
        return str(utf)


def sort_clean(data):
    '''
        Sorts the rows by the loop count, drop duplicates, and resets the index.
    '''
    data_sorted = data.sort(columns=['count'], ascending=False)
    data_cleaned = data_sorted.drop_duplicates(subset='permalinkUrl')
    data_reindex = data_cleaned.reset_index(drop=True)
    return data_reindex



def ap(path):
    """
        Gets the absolute path of the directory and appends the path to it.
    """
    return osp.join(osp.dirname(osp.abspath(sys.argv[0])), path)


def exists(data, directory):
    """
        Checks all the id's of the vines to see if there is a corresponding file
        in the specified directory, and if wrong directory, method returns 
        empty DataFrame.
    """
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
    print(path)
    if osp.isfile(path):
        try:
            df = pd.read_csv(path, encoding='utf-8', error_bad_lines=False)
            return sort_clean(df).ix[:n - 1, :]
        except Exception as e:  
            print(e)


def archive_metadata():
    time = dt.datetime.now().strftime('%d-%m-%Y')

    if not osp.isdir(ap('meta/archives')):
        os.mkdir(ap('meta/archives'))
    if not osp.isdir(ap('meta/archives/' + time)):
        os.mkdir(ap('meta/archives/' + time))

    for filename in os.listdir(ap('meta/')):
        if osp.isfile(ap('meta/' + filename)):
            if not re.match('playlists.csv', filename):
                os.rename(ap('meta/' + filename), 
                          ap('meta/archives/' + time + '/' + filename))
            


def flush_all():
    """
       Gets rid of all files in the render and cache directories as well as
       the vine records csv and leftover temp mp3 audio clips.
    """
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
    """
       Gets rid of all files in the render directory
    """
    for directory in ['render/', 'render/finals/']:
        print('removing all files in: ' + directory)
        for vfile in os.listdir(ap(directory)):
            delete_file(directory + vfile)


def group_data(data, group_size):
    return [data[x:x+group_size] for x in range(0, len(data), group_size)]
