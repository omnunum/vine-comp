# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

import pandas as pd
from scraper import append_path
from moviepy import editor as mpe


def render_vines(data):
    for i, vineid in enumerate(data['id'].astype(basestring)):
        #gets absolute path of video
        vine_path = append_path('cache/' + vineid + '.mp4')
        #creates vine VFC and formats it
        vine = mpe.VideoFileClip(vine_path)
        vine = vine.on_color(size=(854, 480), color=(20, 20, 25),
                             pos='center')
        #encodes text as ascii for textclip creation
        user = data['username'].astype(basestring)[i].encode('ascii', 'ignore')
        desc = data['description'].astype(basestring)[i].encode('ascii', 'ignore')
        user_osd = (mpe.TextClip(txt=user, size=(187, 480),
                                 method='caption', align='center',
                                 font='arial', fontsize=30,
                                 color='white')
                    .set_duration(vine.duration))
        desc_osd = (mpe.TextClip(txt=desc, size=(187, 480),
                                 method='caption', align='center',
                                 font='arial', fontsize=24,
                                 color='white')
                    .set_duration(vine.duration))
        #composite the text on the sides of the video
        comp = mpe.CompositeVideoClip([vine, user_osd, desc_osd.set_pos('right')])
        render_path = append_path('render/' + vineid + '.mp4')
        comp.write_videofile(render_path, fps=30,
                             codec='libx264', threads=2,
                             verbose=True)

if __name__ == '__main__':
    data = pd.read_csv(append_path('records.csv'), encoding='utf-8')
    render_vines(data)
