# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

#from moviepy.editor import *
import pandas as pd
from scraper import append_path
import moviepy


def stich_files(data):
    dstrings = data['id'].astype(basestring)
    files = [append_path('cache/' + x + '.mp4') for x in dstrings]
    print files

if __name__ == '__main__':
    data = pd.read_csv(append_path('records.csv'), encoding='utf-8')
    stich_files(data)
