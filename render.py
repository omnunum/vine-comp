# -*- coding: utf-8 -*-
"""
Created on Thu Dec 11 14:36:33 2014

@author: sunshine
"""

import pandas as pd
from shared import *
from moviepy import editor as mpe
import os
from os import path as osp
from threading import Thread
from Queue import Queue


def vfc_from_file(filename, directory):
    path = ap(str(directory) + '/' + str(filename) + '.mp4')
    try:
        video = mpe.VideoFileClip(path)
        return video
    except Exception as e:
        print(e)


class ThreadWritex264(Thread):

    def __init__(self, queue):
        self.q = queue
        Thread.__init__(self)

    def run(self):
        while True:
            vfc, path = self.q.get()
            vfc.write_videofile(path, codec='libx264',
                            threads=2, verbose=True, fps=30)
            self.q.task_done()


def render_vines(data):
    #verify files exist in cache folder
    datav = exists(data, 'cache')
    #files already rendered get skipped
    datavrid = list(exists(data, 'render')['id'].astype(basestring))
    q = Queue()
    thread_pool(q, 3, ThreadWritex264)
    for i, vineid in enumerate(datav['id'].astype(basestring)):
        if vineid not in datavrid:
            vine = vfc_from_file(vineid, 'cache').on_color(size=(854, 480),
                                                           color=(20, 20, 25),
                                                           pos='center')
            #encodes text as ascii for textclip creation
            user = enco_str(data['username'][i])
            desc = enco_str(data['description'][i])
            user = 'Vine By:\n' + user
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
            q.put((comp, ap('render/' + vineid + '.mp4')))
        else:
            print('skipping ' + vineid)
    q.join()


def concat_vines(data):
    datavid = exists(data, 'render')['id']
    groups = group_data(datavid, 10)
    if not osp.isdir(ap('render/groups')):
        os.makedirs('render/groups')
    #lambda to get VideoFileClip from group number
    vfcg = lambda group: vfc_from_file('group_' + str(group), 'render/groups')
    group_render_path = lambda f: ap('render/groups/' + f + '.mp4')
    for i, group in enumerate(groups):
        videos = [vfc_from_file(vineid, 'render') for vineid in group]
        concat = mpe.concatenate_videoclips(videos)
        write_x264(concat, group_render_path('group_' + str(i)))
    videos = [vfcg(groupid) for groupid in range(len(groups))]
    concat = mpe.concatenate_videoclips(videos)
    write_x264(concat, group_render_path("FINAL RENDER"))


if __name__ == '__main__':
    data = pd.read_csv(ap('meta/worldstarhiphop.csv'), encoding='utf-8')
    render_vines(data)
    concat_vines(data)
