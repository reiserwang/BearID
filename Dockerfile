FROM spmallick/opencv-docker:opencv
MAINTAINER ReiserW reiser@live.com

RUN apt-get -y install libboost-all-dev \
    && cd /home 
RUN cd /home \
    && wget http://dlib.net/files/dlib-19.6.tar.bz2 \
    && tar xvf dlib-19.6.tar.bz2 \
    && cd dlib-19.6/ \
    && mkdir build \
    && cd build \
    && cmake .. \
    && cmake --build . --config Release \
    && make install \
    && ldconfig
RUN cd /home \
    && git clone https://github.com/hypraptive/bearid.git \
    && cd bearid \
    && mkdir build \
    && cd build \
    && cmake -DDLIB_PATH=/home/dlib-19.6 ..

RUN cd /home/bearid \
    && mkdir build \
    && cd build \
    && cmake -DDLIB_PATH=/home/dlib-19.6 .. \
    && cmake --build . --config Release

COPY mmod_dog_hipsterizer.dat /home/bearid/build
COPY images /homebearid/build/images

EXPOSE 5000
EXPOSE 8888
CMD ["/bin/bash"]

#docker run -p 5000:5000 -p 8888:8888 -it spmallick/opencv-docker:opencv /bin/bash
