# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

from shared import *
from moviepy import editor as mpe
import os
from os import path as osp
import sys
import getopt
import numpy as np
import re
import pandas as pd
import random


def vfc_from_file(filename, directory):
    path = str
    if directory == '':
        path = ap(str(filename) + '.mp4')
    else:
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
        #replaces all instances of NaN with a blank string
        row = row.replace(np.nan, '', regex=True)
        vineid = row['id']
        if vineid not in datavrid:
            vine = vfc_from_file(vineid, 'cache').on_color(size=(854, 480),
                                                           color=(20, 20, 25),
                                                           pos='center')
            #encodes text as ascii for textclip creation
            user = enc_str(row['username']).upper()
            user = re.sub('[_]+', ' ', user)
            user = re.sub('[()]+', '', user)
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
            channel_icon_size = (118, 118)
            channel_icon = mpe.ImageClip(str(channel_icon_path), transparent=True)
            channel_icon = (channel_icon.set_duration(vine.duration)
                                        .resize(channel_icon_size)
                                        .set_position((0, 5)))
            #order number
            order = (mpe.TextClip(txt=str(row['order'] + 1), 
                     size=channel_icon_size,
                     font='Heroic-Condensed-Bold', fontsize=100,
                     align='east', color='red')
                     .set_position((62, 15))
                     .set_duration(vine.duration))
            #grabs a random second from our static video sourced from
            #http://www.videezy.com/elements-and-effects/242-tv-static-hd-stock-video
            static_v = vfc_from_file('static', '').resize(vine.size)
            randsec = random.randint(0, int(static_v.duration) - 2)
            static_v = static_v.subclip(randsec, randsec + 1)
            #grab the audio for the static and set it to the video
            static_a = mpe.AudioFileClip(ap('static.wav')).volumex(0.4)
            static = static_v.set_audio(static_a)
            
            #composite the parts on the sides of the video
            #then concatenate with the static intercut
            comp = mpe.CompositeVideoClip([vine, user_osd, desc_osd,
                                           channel_icon, order])
            comp = mpe.concatenate_videoclips([comp, static])
                                           
            #start the render
            path = ap('render/' + vineid + '.mp4')
            write_x264(comp, path)
        else:
            print('skipping ' + vineid)


def concat_vines(data, name):
    #gets all the vine ids, returns those are have been rendered with titles
    datavid = exists(data, 'render')['id']
    #sets up the paths we'll need
    vine_list_path = ap('render/' + name + '.txt')
    final_path = ap('render/finals/' + name + '.mp4')
    #makes the necessary folders if doesn't exist
    if not osp.isdir(ap('render/finals')):
        os.makedirs(ap('render/finals'))
    else:
        #if an old copy already exists let's delete it
        if osp.isfile(final_path):
            os.unlink(final_path)
    
    with open(vine_list_path, 'w+') as l:
        for vineid in datavid:
            path = ap('render/' + vineid + '.mp4')
            l.write('file \'' + path + '\'\n')
    args = (['ffmpeg', '-f', 'concat', '-i', vine_list_path,
             '-c', 'copy', final_path])
    subprocess.call(args)
    return final_path


def create_comp_description(data):
    #confirms that the files were rendered
    datav = exists(data, 'render')
    comp_desc = list()

    for i, row in datav.iterrows():
        user = enc_str(row['username'])
        line = ('{0}: {1} -- {3}'
                .format(i + 1, user, row['permalinkUrl']))
        comp_desc.append(line)
    return '\n'.join(comp_desc)[:4990]


def upload_video(path, desc, name):
    if osp.isfile(path):
        args = (['python2', ap('youtube_upload.py'),
                 '--api-upload',
                '--email=vinecompauthority@gmail.com',
                '--password=yvngqhuxhjynsyfq',
                '--title=Hottest ' + name.title() + ' Vines of The Week',
                '--category=Comedy',
                '--description=' + desc,
                path])
        subprocess.call(args)
    else:
        print('File not found: ' + path)


if __name__ == '__main__':
    options, remainder = getopt.gnu_getopt(sys.argv[1:], ':',
                                           ['name=', 'limit='])
    name, n = 'comedy', 10
    for opt, arg in options:
        if opt == '--name':
            name = arg
        if opt == '--limit':
            n = int(arg)

    data = load_top_n(n, name)
    render_vines(data, name)
    path = concat_vines(data, name)
    desc = create_comp_description(data)
    try:
        if osp.isfile(path):
            upload_video(path, desc, name)
        else:
            print('Final ' + name + ' render file not found')
    except Exception as e:
        print('Error with upload script, not flushing render folder')
        print(e)
