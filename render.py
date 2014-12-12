# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

import pandas as pd
from scraper import append_path
from moviepy.editor import *


def stitch_files(data):
    dstrings = data['id'].astype(basestring)
    files = [append_path('cache/' + x + '.mp4') for x in dstrings]
    batches = [files[x:x+10] for x in xrange(0, len(files), 10)]
    for i, batch in enumerate(batches):
        videos = [VideoFileClip(file) for file in batch]
        comp = concatenate_videoclips(videos)
        comp.write_videofile('composite_%d.mkv' % i, fps=30, codec='libx264')
    print files

if __name__ == '__main__':
    data = pd.read_csv(append_path('records.csv'), encoding='utf-8')
    stitch_files(data)
