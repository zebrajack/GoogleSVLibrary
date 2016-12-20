#! /usr/bin/env python
import subprocess
import cv2
import os
import numpy as np
import urllib2

test_id = 'X8dCxQEPFLJpXnntuKRFLA'
BaseUri = 'http://maps.google.com/cbk'
zoom_lv = 4
ext = '.jpg'
def GetUrlContent(url):
    f = urllib2.urlopen(url)
    data = f.read()
    f.close()
    return data

def GetPanoramaTile(panoid, zoom, x, y): 
    url =  '%s?'
    url += 'output=tile'                    # tile output
    url += '&panoid=%s'                     # panoid to retrieve
    url += '&zoom=%s'                       # zoom level of tile
    url += '&x=%i'                          # x position of tile
    url += '&y=%i'                          # y position of tile
    url += '&fover=2'                       # ???
    url += '&onerr=3'                       # ???
    url += '&renderer=spherical'            # standard speherical projection
    url += '&v=4'                           # version
    url = url % (BaseUri, panoid, zoom, x, y)
    #print url
    return GetUrlContent(url)
def GetPanoByID(ID, DIR):
    if not os.path.isdir(DIR):
        return False
    try:
        if not os.path.isdir('./buffer_%s'%ID):
            subprocess.call('mkdir -p buffer_%s/tmp'%ID, shell=True)
        else:
            subprocess.call('rm -r buffer_%s'%ID, shell=True)
            subprocess.call('mkdir -p buffer_%s/tmp'%ID, shell=True)
        row_range = [2,3,4]
        col_range = [5,6,7]
        index = 0
        for row in row_range:
            for col in col_range:
                data = GetPanoramaTile(ID, zoom_lv, col, row)
                #subprocess.call("wget '%s'  -O buffer_%s/tmp/image_%.2d%s"%(url, ID, index, ext), shell=True)
                f = open('buffer_%s/tmp/image_%.2d%s'%(ID,index,ext), 'wb')
                f.write(data)
                f.close()
                index += 1
        lst = os.listdir('buffer_%s/tmp/'%ID)
        lst.sort()
        output = np.zeros([1536, 1536, 3], dtype = np.uint8)
        begin_row = 0
        begin_col = 0
        index = 0
        for row in range(0,3):
            begin_col = 0
            for col in range(0,3):
                img = cv2.imread('buffer_%s/tmp/'%ID+lst[index])
                output[begin_row:begin_row+512, begin_col: begin_col+512] = img
                begin_col += 512
                index += 1
            begin_row += 512
        cv2.imwrite('buffer_%s/pano_%s_0.jpg'%(ID,ID), output[208:928, 128:1408])
        subprocess.call('rm buffer_%s/tmp/*'%ID, shell=True)
        row_range = [2,3,4]
        col_range = [11,12,0,1]
        index = 0
        for row in row_range:
            for col in col_range:
                data = GetPanoramaTile(ID, zoom_lv, col, row)
                #subprocess.call("wget '%s'  -O buffer_%s/tmp/image_%.2d%s"%(url, ID, index, ext), shell=True)
                f = open('buffer_%s/tmp/image_%.2d%s'%(ID,index,ext), 'wb')
                f.write(data)
                f.close()
                index += 1
        lst = os.listdir('buffer_%s/tmp/'%ID)
        lst.sort()
        output = np.zeros([2048, 2048, 3], dtype = np.uint8)
        begin_row = 0
        begin_col = 0
        index = 0
        for row in range(0,3):
            begin_col = 0
            for col in range(0,4):
                img = cv2.imread('buffer_%s/tmp/'%ID+lst[index])
                output[begin_row:begin_row+512, begin_col: begin_col+512] = img
                begin_col += 512
                index += 1
            begin_row += 512
        cv2.imwrite('buffer_%s/pano_%s_180.jpg'%(ID,ID), output[208:928, 384:1664])
        subprocess.call('mv buffer_%s/*.jpg %s'%(ID,DIR), shell=True)
        subprocess.call('rm -r buffer_%s/'%ID, shell=True)
        return True
    except:
        subprocess.call('rm -r buffer_%s/'%ID, shell=True)
        return False
#GetPanoByID(test_id,'.') 
