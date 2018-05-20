import heapq
import os
from operator import itemgetter
from unicodedata import normalize
from multiprocessing import Process, JoinableQueue

import sys

import shutil

import re

import time

import PIL
import cv2
from PIL import Image
from openslide import open_slide, ImageSlide
from openslide.deepzoom import DeepZoomGenerator
from tqdm import tqdm

import config as cfg
import numpy as np


class TileWorker(Process):
    """A child process that generates and writes tiles."""

    def __init__(self, queue, slidepath, tile_size, overlap, limit_bounds, rotate,
                 quality):
        Process.__init__(self, name='TileWorker')
        self.daemon = True
        self._queue = queue
        self._slidepath = slidepath
        self._tile_size = tile_size
        self._overlap = overlap
        self._limit_bounds = limit_bounds
        self._quality = quality
        self._rotate = rotate
        self._slide = None

    def run(self):
        self._slide = open_slide(self._slidepath)
        last_associated = None
        dz = self._get_dz()
        while True:
            data = self._queue.get()
            if data is None:
                self._queue.task_done()
                break

            associated, level, address, outfile, rejfile = data
            if last_associated != associated:
                dz = self._get_dz(associated)
                last_associated = associated

            tile = dz.get_tile(level, address)

            if not cfg.REJECT or self._is_good(tile):
                basename = os.path.splitext(outfile)
                tile.save(basename[0] + "_" + str(1) + basename[1], quality=self._quality)

                if self._rotate:
                    # 90 deg = 2, 180 deg = 3, 270 deg = 4
                    for angle in [2, 3, 4]:
                        self.rotate_and_save(tile, angle, outfile)

            elif cfg.SAVE_REJECTED:
                tile.save(rejfile, quality=self._quality)

            self._queue.task_done()

    def rotate_and_save(self, tile, angle_type, savefile):
        basename = os.path.splitext(savefile)
        tile.transpose(angle_type).save(basename[0] + "_" + str(angle_type) + basename[1], quality=self._quality)

    def _get_dz(self, associated=None):
        if associated is not None:
            image = ImageSlide(self._slide.associated_images[associated])
        else:
            image = self._slide
        return DeepZoomGenerator(image, self._tile_size, self._overlap,
                                 limit_bounds=self._limit_bounds)

    def _is_good(self, tile):
        # tile is PIL.image

        img = np.asarray(tile)

        if img.shape[0] < self._tile_size + 2 * self._overlap or img.shape[1] < self._tile_size + 2 * self._overlap:
            return False

        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(img, (5, 5), 0)
        ret3, th3 = cv2.threshold(blur, cfg.REJECT_THRESHOLD, 255, cv2.THRESH_BINARY)
        im2, contours, hierarchy = cv2.findContours(th3, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

        return self.get_cnt_sum(contours, 2) < cfg.MAX_WHITE_SIZE

    @staticmethod
    def get_cnt_sum(contours, topn):
        res = 0
        cnts = sorted(contours, key=lambda x: cv2.contourArea(x))[-topn:]
        return sum([cv2.contourArea(cnt) for cnt in cnts])


class SingleImageTiler(object):
    """Handles generation of tiles and metadata for a single image."""

    def __init__(self, dz, basename, img_format, associated, queue, only_last=True):
        self._dz = dz
        self._basename = basename
        self._img_format = img_format
        self._associated = associated
        self._img_name = associated if associated else cfg.DEFAULT_FILENAME
        self._queue = queue
        self._processed = 0
        self._only_last = only_last

    def run(self):
        t = time.perf_counter()
        self._write_tiles()
        self._write_dzi()
        elapsed_time = time.perf_counter() - t
        cfg.ver_print("Tiling completed on {0} in: ".format(self._img_name), elapsed_time)

    def _write_tiles(self):
        if self._only_last:
            iterator = [self._dz.level_count - 1]
        else:
            iterator = range(self._dz.level_count)

        for level in iterator:

            tiledir = os.path.join(self._basename, self._img_name, str(level))
            rejpath = os.path.join(self._basename, self._img_name, str(level), "rejected")
            if not os.path.exists(tiledir):
                os.makedirs(tiledir)

            if not os.path.exists(rejpath) and cfg.SAVE_REJECTED:
                os.makedirs(rejpath)

            cols, rows = self._dz.level_tiles[level]
            pbar = tqdm(total=cols*rows, desc="Tiling {0}".format(self._associated or 'slide'))
            for row in range(rows):
                for col in range(cols):
                    location, l, s = self._dz.get_tile_coordinates(level, (col, row))
                    tilename = os.path.join(tiledir, '%d_%d.%s' % (location[0], location[1], self._img_format))
                    rejfile = os.path.join(rejpath, '%d_%d.%s' % (location[0], location[1], self._img_format))
                    if not os.path.exists(tilename):
                        self._queue.put((self._associated, level, (col, row), tilename, rejfile))

                    pbar.update()

            pbar.close()

    def _write_dzi(self):
        with open('%s.dzi' % self._basename, 'w') as fh:
            fh.write(self.get_dzi())

    def get_dzi(self):
        return self._dz.get_dzi(self._img_format)


class WholeSlideTiler(object):
    """Handles generation of tiles and metadata for all images in a slide."""

    def __init__(self, slide_path, outpath, img_format, tile_size, stride,
                 limit_bounds, rotate, quality, nworkers, only_last):

        self._slide = open_slide(slide_path)  # the whole slide image
        self._outpath = outpath  # baseline name of each tiled image
        self._img_format = img_format  # image format (jpeg or png)
        self._overlap = tile_size - stride
        self._tile_size = tile_size - 2 * self._overlap  # tile size. default: 256x256 pixels
        self._limit_bounds = limit_bounds
        self._queue = JoinableQueue(2 * nworkers)  # setup multiprocessing worker queues.
        self._nworkers = nworkers  # number of workers
        self._only_last = only_last
        self._dzi_data = {}
        for _i in range(nworkers):
            TileWorker(self._queue, slide_path, self._tile_size, self._overlap,
                       limit_bounds, rotate, quality).start()

    def run(self):
        self._run_image()
        for name in self._slide.associated_images:
            self._run_image(name)
            # self._write_static()
        self._shutdown()

    def _run_image(self, associated=None):
        """Run a single image from self._slide."""
        if associated is None:
            image = self._slide
            outpath = self._outpath

        else:
            image = ImageSlide(self._slide.associated_images[associated])
            outpath = os.path.join(self._outpath, self._slugify(associated))

        dz = DeepZoomGenerator(image, self._tile_size, self._overlap, self._limit_bounds)

        tiler = SingleImageTiler(dz, outpath, self._img_format, associated,
                                 self._queue, self._only_last)
        tiler.run()

        self._dzi_data[self._url_for(associated)] = tiler.get_dzi()

    def _url_for(self, associated):
        if associated is None:
            base = 'slide'
        else:
            base = self._slugify(associated)
        return '%s.dzi' % base

    @staticmethod
    def _copydir(src, dest):
        if not os.path.exists(dest):
            os.makedirs(dest)
        for name in os.listdir(src):
            srcpath = os.path.join(src, name)
            if os.path.isfile(srcpath):
                shutil.copy(srcpath, os.path.join(dest, name))

    @classmethod
    def _slugify(cls, text):
        text = normalize('NFKD', text.lower()).encode('ascii', 'ignore').decode()
        return re.sub('[^a-z0-9]+', '_', text)

    def _shutdown(self):
        for _i in range(self._nworkers):
            self._queue.put(None)
        self._queue.join()
