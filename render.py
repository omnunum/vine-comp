# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

from shared import *
from moviepy import editor as mpe
import os
from os import path as osp
import numpy as np
import re
import pandas as pd


def vfc_from_file(filename, directory):
    path = ap(str(directory) + '/' + str(filename) + '.mp4')
    if osp.isfile(path):
        try:
            video = mpe.VideoFileClip(path)
            return video
        except Exception as e:
            print(e)


def write_x264(vfc, path):
    vfc.write_videofile(path, codec='libx264',
                        threads=4, verbose=True, fps=30)


def render_vines(data, channel):
    #verify files exist in cache folder
    datav = exists(data, 'cache')
    #files already rendered get skipped
    datavrid = list(exists(data, 'render')['id'].astype(basestring))
    #adds data so that the order of the videos can be printed on screen
    datav['order'] = datav.index.values
    for i, row in datav.iterrows():
        row = row.replace(np.nan, '', regex=True)
        vineid = row['id']
        if vineid not in datavrid:
            vine = vfc_from_file(vineid, 'cache').on_color(size=(854, 480),
                                                           color=(20, 20, 25),
                                                           pos='center')
            #encodes text as ascii for textclip creation
            user = enc_str(row['username']).upper()
            desc = enc_str(row['description']).upper()
            desc = re.sub(' #[a-zA-Z0-9]+', '', desc)
            
            user = 'VINE BY:\n' + user
            #lambda to create text clip
            tc = lambda text, size, xline: (mpe.TextClip(txt=text, size=(180, 480),
                                            method='caption', align='center',
                                            font='Heroic-Condensed-Bold', fontsize=size,
                                            color='white', interline=xline)
                                            .set_duration(vine.duration))
            user_osd = tc(user, 55, 11).set_position((0, 25))
            desc_osd = tc(desc, 40, 0).set_position('right')

            channel_icon_path = ap('meta/icons/' + channel + '.png')
            channel_icon_size = (120, 120)
            channel_icon = mpe.ImageClip(str(channel_icon_path), transparent=True)
            channel_icon = (channel_icon.set_duration(vine.duration)
                                        .resize(channel_icon_size)
                                        .set_position((0, 5)))
            #order number
            order = (mpe.TextClip(txt=str(row['order']), 
                     size=channel_icon_size,
                     font='Heroic-Condensed-Bold', fontsize=100,
                     align='east', color='red')
                     .set_position((62, 15))
                     .set_duration(vine.duration))
            #composite the parts on the sides of the video
            comp = mpe.CompositeVideoClip([vine, user_osd, desc_osd,
                                           channel_icon, order])
            #start the render
            path = ap('render/' + vineid + '.mp4')
            write_x264(comp, path)
        else:
            print('skipping ' + vineid)


def concat_vines(data, name):
    #gets all the vine ids, returns those are have been rendered with titles
    datavid = exists(data, 'render')['id']
    #makes groups of vineids with a size of 50 elements
    groups = group_data(datavid, 50)
    #makes the groups folder if doesn't exist
    if not osp.isdir(ap('render/groups')):
        os.makedirs('render/groups')
    group_render_path = lambda f: ap('render/groups/' + f + '.mp4')
    for i, group in enumerate(groups):
        videos = [vfc_from_file(vineid, 'render') for vineid in group]
        concat = mpe.concatenate_videoclips(videos)
        write_x264(concat, group_render_path(name + '_group_' + str(i)))
    #lambda to create VideoFileClip from group number
    vfcg = lambda group: vfc_from_file('group_' + str(group), 'render/groups')
    #creates list of video file clips from the group files
    video_groups = [vfcg(groupid) for groupid in range(len(groups))]
    #concatenates all the groups into one video
    concat = mpe.concatenate_videoclips(video_groups)
    #writes that final file to disk
    write_x264(concat, group_render_path(name))

if __name__ == '__main__':
    name = 'comedy'
    data = load_top_100(name)
    render_vines(data, name)
    concat_vines(data, name)
