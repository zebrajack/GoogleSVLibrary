# GoogleSVLibrary
## Introduction
This is python package to query Google Street View Image and Depth map.

### Usage
Panorama is 3328 x 6656 image.
Depth is 256 x 512 numpy array.
```python
from GoogleSVLibrary import StreetViewInfo
from GoogleSVLibrary import StreetViewImage
from GoogleSVLibrary import StreetViewDepth

panoid = StreetViewInfo.GetIDByLoc([24.7881509,121.0104312]) # Input is [lat, lon]
if panoid is None: # If there is no pano here, panoid will be None
  print 'No pano'
  exit()
StreetViewImage.GetPanoByID_full(panoid, './') # it will store pano as './pano_%s.jpg'%panoid
depth_map = StreetViewDepth.GetDepthMap(panoid = panoid) # depth_map is our depth data, which is 256 x 512
```
