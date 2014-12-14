# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

import pandas as pd
from scraper import append_path
from moviepy import editor as mpe
import re


def render_vines(data):
    background = mpe.ColorClip((854, 480), col=(20, 20, 25))
    for i, vineid in enumerate(data['id'].astype(basestring)):
        vine_path = append_path('cache/' + vineid + '.mp4')
        vine = mpe.VideoFileClip(vine_path)
        vine = vine.on_color(size=(854, 480), color=(20, 20, 25), pos='center')
        vine = vine.set_position('center').set_duration(vine.duration)
        user = data['username'].astype(basestring)[i].encode('ascii', 'ignore')
        desc = data['description'].astype(basestring)[i].encode('ascii', 'ignore')
        user_osd = mpe.TextClip(txt=user, size=(227, 480),
                                method='caption', align='East')
        desc_osd = mpe.TextClip(txt=desc, size=(227, 480),
                                method='caption', align='West')
        comp = mpe.CompositeVideoClip([background, user_osd, desc_osd, vine])
        render_path = append_path('render/' + vineid + '.mp4')
        comp.write_videofile(render_path, fps=30,
                             codec='libx264', threads=2,
                             verbose=True)

if __name__ == '__main__':
    data = pd.read_csv(append_path('records.csv'), encoding='utf-8')
    render_vines(data)
