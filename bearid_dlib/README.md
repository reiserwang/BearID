# bearid
Hypraptive BearID project code repository. For more information, read the [hypraptive blog](https://hypraptive.github.io/).

## Pre-Requisites
* [dlib](http://dlib.net/) - download and install somwhere. You should have OpenCV and CUDA and other packages which are helpful for dlib.
* [boost](http://www.boost.org/)

## Build
Uses cmake flow:

```
cd bearid
mkdir build
cd build
cmake -DDLIB_PATH=<path_to_dlib> ..
cmake --build . --config Release
```

## Running
* Bearchip - finds bear faces, aligns and crops
  * ./bearchip <mmod_dog_hipsterizer.dat> <image_file or image_path>
* Bearembed - uses a set of bear faces to train a 128D embedding
  * ./bearembed -train <face_chip_dir>
  * ./bearembed -test <face_chip_dir>
  * ./bearembed -embed <embedded_dir> <face_chip_dir>
* Bearsvm - uses a set of embeddings to train and SVM one-vs-one classifier
  * ./bearsvm <embedded_dir>
* Bearid - puts it all together
  * ./bearid <image_file>

## Tools
There are some python tools and scripts in the `tools` directory for managing datasets and evaluating results.

## Data Sources

### Brooks Falls, Katmai National Park, Alaska, USA
* [Anna-Marie_AZ on Flickr](https://www.flickr.com/photos/105187918@N03/albums)
* [Carla Farris on Flickr](https://www.flickr.com/photos/129908461@N03/albums/with/72157672138992512)
  * [Brooks Falls 2015](https://www.flickr.com/photos/129908461@N03/albums/72157657150224152)
  * [Brooks Falls 2016](https://www.flickr.com/photos/129908461@N03/albums/72157672138992512)
* [Ike Fitz on Flickr](https://www.flickr.com/photos/ikefitz/albums)
  * [Brooks River Wildlife 2015](https://www.flickr.com/photos/ikefitz/albums/72157666514167600)
  * [Brooks River Wildlife 2016](https://www.flickr.com/photos/ikefitz/albums/72157665026099739)
* [Katmai National Park](https://www.nps.gov/katm) (sent on hard disk via mail)
  * Images from their bear monitoring program
  * Ranger David's personal photos
  * Ranger Anela's personal photos
* Larinor (provided via direct transfer)
* littleostow (provided via email)
* [Ranger Jeanne on Flickr](https://www.flickr.com/photos/jeanner/albums)

### Glendale Cove, Knights Inlet, British Columbia, Canada
* [Brown Bear Research Network](http://bearresearch.org/) (sent on flash drive via mail)
