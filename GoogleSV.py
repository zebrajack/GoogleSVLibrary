#!/usr/bin/python

import urllib2
import libxml2
import inspect
import zlib
import base64
import struct
import Image
import os
import shutil


#BaseUri = 'http://maps.google.com/cbk'
BaseUri = 'https://geo3.ggpht.com/cbk'
def GetIDByLoc(panoid = None, lat = None, lon = None, radius = 10):

    pano_info = GetPanoramaMetadata(lat=lat,lon=lon)
    if pano_info == None:
        return None

    return pano_info.PanoId

def GetLocByID(panoid = None, radius = 10):

    pano_info = GetPanoramaMetadata(panoid=panoid)

    if pano_info == None:
        return None

    return (pano_info.Lat, pano_info.Lon)


def GetPanoramaMetadata(panoid = None, lat = None, lon = None, radius = 50):

        url =  '%s?'
        url += 'output=xml'                     # metadata output
        url += '&v=4'                           # version
        url += '&dm=1'                          # include depth map
        url += '&pm=1'                          # include pano map
        if panoid == None:
                url += '&ll=%s,%s'              # lat/lon to search at
                url += '&radius=%s'             # search radius
                url = url % (BaseUri, lat, lon, radius)
                #print url
        else:
                url += '&panoid=%s'             # panoid to retrieve
                url = url % (BaseUri, panoid)


        #print url
        #exit()
        findpanoxml = GetUrlContents(url)
        #print url
        #print findpanoxml.find('data_properties')
        if findpanoxml.find('data_properties') == -1:
                return None

        return PanoramaMetadata(libxml2.parseDoc(findpanoxml))

# panoid is the value from the panorama metadata
# zoom range is 0->NumZoomLevels inclusively
# x/y range is 0->?
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

        return GetUrlContents(url)

def GetUrlContents(url):
        f = urllib2.urlopen(url)
        data = f.read()
        f.close()
        return data

class PanoramaMetadata:

        def __init__(self, panodoc):
                self.PanoDoc = panodoc
                panoDocCtx = self.PanoDoc.xpathNewContext()

                self.PanoId = panoDocCtx.xpathEval("/panorama/data_properties/@pano_id")[0].content
                self.ImageWidth = panoDocCtx.xpathEval("/panorama/data_properties/@image_width")[0].content
                self.ImageHeight = panoDocCtx.xpathEval("/panorama/data_properties/@image_height")[0].content
                self.ImageDate = panoDocCtx.xpathEval("/panorama/data_properties/@image_date")[0].content
                self.TileWidth = panoDocCtx.xpathEval("/panorama/data_properties/@tile_width")[0].content
                self.TileHeight = panoDocCtx.xpathEval("/panorama/data_properties/@tile_height")[0].content
                self.NumZoomLevels = panoDocCtx.xpathEval("/panorama/data_properties/@num_zoom_levels")[0].content
                self.Lat = panoDocCtx.xpathEval("/panorama/data_properties/@lat")[0].content
                self.Lon = panoDocCtx.xpathEval("/panorama/data_properties/@lng")[0].content
                self.OriginalLat = panoDocCtx.xpathEval("/panorama/data_properties/@original_lat")[0].content
                self.OriginalLon = panoDocCtx.xpathEval("/panorama/data_properties/@original_lng")[0].content
                self.Copyright = panoDocCtx.xpathEval("/panorama/data_properties/copyright/text()")[0].content

                #self.Text = panoDocCtx.xpathEval("/panorama/data_properties/text/text()")[0].content
                try:
                    self.Text = panoDocCtx.xpathEval("/panorama/data_properties/text/text()")[0].content
                except:
                    self.Text = None

                try:
                    self.Region = panoDocCtx.xpathEval("/panorama/data_properties/region/text()")[0].content
                except:
                    self.Region = None
                #self.Region = panoDocCtx.xpathEval("/panorama/data_properties/region/text()")[0].content
                self.Country = panoDocCtx.xpathEval("/panorama/data_properties/country/text()")[0].content

                self.ProjectionType = panoDocCtx.xpathEval("/panorama/projection_properties/@projection_type")[0].content
                self.ProjectionPanoYawDeg = panoDocCtx.xpathEval("/panorama/projection_properties/@pano_yaw_deg")[0].content
                self.ProjectionTiltYawDeg = panoDocCtx.xpathEval("/panorama/projection_properties/@tilt_yaw_deg")[0].content
                self.ProjectionTiltPitchDeg = panoDocCtx.xpathEval("/panorama/projection_properties/@tilt_pitch_deg")[0].content

                self.AnnotationLinks = []
                for cur in panoDocCtx.xpathEval("/panorama/annotation_properties/link"):
                        self.AnnotationLinks.append({ 'YawDeg': cur.xpathEval("@yaw_deg")[0].content,
                                            'PanoId': cur.xpathEval("@pano_id")[0].content,
                                            'RoadARGB': cur.xpathEval("@road_argb")[0].content,
                                            #'Text': cur.xpathEval("link_text/text()")[0].content,
                        })

                tmp = panoDocCtx.xpathEval("/panorama/model/pano_map/text()")
                if len(tmp) > 0:
                        tmp = tmp[0].content
                        tmp = zlib.decompress(base64.urlsafe_b64decode(tmp + self.MakePadding(tmp)))
                        self.DecodePanoMap(tmp)

                tmp = panoDocCtx.xpathEval("/panorama/model/depth_map/text()")
                if len(tmp) > 0:
                        tmp = tmp[0].content
                        tmp = zlib.decompress(base64.urlsafe_b64decode(tmp + self.MakePadding(tmp)))
                        self.DecodeDepthMap(tmp)
                panodoc.freeDoc()
                panoDocCtx.xpathFreeContext()


        def MakePadding(self, s):
                return (4 - (len(s) % 4)) * '='


        def DecodePanoMap(self, raw):
                pos = 0

                (headerSize, numPanos, panoWidth, panoHeight, panoIndicesOffset) = struct.unpack('<BHHHB', raw[0:8])
                if headerSize != 8 or panoIndicesOffset != 8:
                        print "Invalid panomap data"
                        return
                pos += headerSize

                self.PanoMapIndices = [ord(x) for x in raw[panoIndicesOffset:panoIndicesOffset + (panoWidth * panoHeight)]]
                pos += len(self.PanoMapIndices)

                self.PanoMapPanos = []
                for i in xrange(0, numPanos - 1):
                        self.PanoMapPanos.append({ 'panoid': raw[pos: pos+ 22]})
                        pos += 22

                for i in xrange(0, numPanos - 1):
                        (x, y) = struct.unpack('<ff', raw[pos:pos+8])
                        self.PanoMapPanos[i]['x'] = x
                        self.PanoMapPanos[i]['y'] = y
                        pos+=8

        def DecodeDepthMap(self, raw):
                pos = 0

                (headerSize, numPlanes, panoWidth, panoHeight, planeIndicesOffset) = struct.unpack('<BHHHB', raw[0:8])
                if headerSize != 8 or planeIndicesOffset != 8:
                        print "Invalid depthmap data"
                        return
                self.DepthHeader = {'numPlanes': numPlanes, 'panoWidth': panoWidth, 'panoHeight': panoHeight}
                pos += headerSize

                self.DepthMapIndices = [ord(x) for x in raw[planeIndicesOffset:planeIndicesOffset + (panoWidth * panoHeight)]]
                pos += len(self.DepthMapIndices)
                
                self.DepthMapPlanes = []
                #for i in xrange(0, numPlanes - 1):
                for i in xrange(0, numPlanes):
                        #(d, nx, ny, nz) = struct.unpack('<ffff', raw[pos:pos+16])
                        (nx, ny, nz, d) = struct.unpack('<ffff', raw[pos:pos+16])
                        self.DepthMapPlanes.append({ 'd': d, 'nx': nx, 'ny': ny, 'nz': nz }) # nx/ny/nz = unit normal, d = distance from origin
                        pos += 16

        def __str__(self):
                tmp = ''
                for x in inspect.getmembers(self):
                        if x[0].startswith("__") or inspect.ismethod(x[1]):
                                continue

                        tmp += "%s: %s\n" % x
                return tmp
'''
pano = GetPanoramaMetadata(panoid='hTWZyyK1YaCSLchz0iTXPA') #Pu-X49Gu62_oPFYfusjd4Q
print pano.PanoId, pano.ImageDate
pano = GetPanoramaMetadata(panoid='1wN_8lP21Xjbl_uzd7vHzQ')
print pano.PanoId, pano.ImageDate
pano = GetPanoramaMetadata(panoid='5pJqrutfg0S553D5nAFYjA')
print pano.PanoId, pano.ImageDate
pano = GetPanoramaMetadata(panoid='MMh0z1UOdC1iNmXoupBmIA')
print pano.PanoId, pano.ImageDate
pano = GetPanoramaMetadata(panoid='3M7djh1njyhSxfvs7OwrpQ') #KS0V1c0_DmhCRG2h6pbZyw_180
print pano.PanoId, pano.ImageDate
pano = GetPanoramaMetadata(panoid='6kL3jbNuE74SS18-yHMWsA') #CaxiovpOSkB1p4uRlzJKIg_180
print pano.PanoId, pano.ImageDate
#print pano.PanoMapPanos
#print pano.AnnotationLinks
#print pano.PanoMapPanos
#print pano.DepthMapPlanes
#print GetPanoramaTile(pano.PanoId, 2, 0, 0)
'''
