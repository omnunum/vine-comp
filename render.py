# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

from shared import *
from moviepy import editor as mpe
import os
from os import path as osp


def vfc_from_file(filename, directory):
    path = ap(str(directory) + '/' + str(filename) + '.mp4')
    try:
        video = mpe.VideoFileClip(path)
        return video
    except Exception as e:
        print(e)


def write_x264(vfc, path):
    vfc.write_videofile(path, codec='libx264',
                        threads=4, verbose=True, fps=30)


def render_vines(data):
    #verify files exist in cache folder
    datav = exists(data, 'cache')
    #files already rendered get skipped
    datavrid = list(exists(data, 'render')['id'].astype(basestring))
    for i, row in datav.iterrows():
        vineid = row['id']
        if vineid not in datavrid:
            vine = vfc_from_file(vineid, 'cache').on_color(size=(854, 480),
                                                           color=(20, 20, 25),
                                                           pos='center')
            #encodes text as ascii for textclip creation
            user = enc_str(row['username']).upper()
            desc = enc_str(row['description']).upper()
            user = 'VINE BY:\n' + user
            #lambda to create text clip
            tc = lambda text, size, xline: (mpe.TextClip(txt=text, size=(180, 480),
                                            method='caption', align='center',
                                            font='arial', fontsize=size,
                                            color='white', interline=xline)
                                    .set_duration(vine.duration))
            user_osd = tc(user, 40, 20)
            desc_osd = tc(desc, 28, 13).set_pos('right')
            #composite the text on the sides of the video
            comp = mpe.CompositeVideoClip([vine, user_osd, desc_osd])
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
    render_vines(data)
    concat_vines(data, name)
