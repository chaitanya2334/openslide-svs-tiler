import os
from unicodedata import normalize
from multiprocessing import Process, JoinableQueue

import sys

import shutil

import re

import time
from openslide import open_slide, ImageSlide
from openslide.deepzoom import DeepZoomGenerator
import config as cfg


class TileWorker(Process):
    """A child process that generates and writes tiles."""

    def __init__(self, queue, slidepath, tile_size, overlap, limit_bounds,
                 quality):
        Process.__init__(self, name='TileWorker')
        self.daemon = True
        self._queue = queue
        self._slidepath = slidepath
        self._tile_size = tile_size
        self._overlap = overlap
        self._limit_bounds = limit_bounds
        self._quality = quality
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

            associated, level, address, outfile = data
            if last_associated != associated:
                dz = self._get_dz(associated)
                last_associated = associated
            tile = dz.get_tile(level, address)
            tile.save(outfile, quality=self._quality)
            self._queue.task_done()

    def _get_dz(self, associated=None):
        if associated is not None:
            image = ImageSlide(self._slide.associated_images[associated])
        else:
            image = self._slide
        return DeepZoomGenerator(image, self._tile_size, self._overlap,
                                 limit_bounds=self._limit_bounds)


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
            if not os.path.exists(tiledir):
                os.makedirs(tiledir)

            cols, rows = self._dz.level_tiles[level]
            for row in range(rows):
                for col in range(cols):
                    tilename = os.path.join(tiledir, '%d_%d.%s' % (col, row, self._img_format))
                    if not os.path.exists(tilename):
                        self._queue.put((self._associated, level, (col, row), tilename))

                    self._tile_done()

    def _tile_done(self):
        self._processed += 1
        if self._only_last:
            ncols, nrows = self._dz.level_tiles[self._dz.level_count - 1]
            total = ncols * nrows
        else:
            total = self._dz.tile_count

        count = self._processed
        if count % 100 == 0 or count == total:
            print("\rTiling %s: wrote %d/%d tiles" % (
                self._associated or 'slide', count, total),
                  end='', file=sys.stderr)
            if count == total:
                print(file=sys.stderr)

    def _write_dzi(self):
        with open('%s.dzi' % self._basename, 'w') as fh:
            fh.write(self.get_dzi())

    def get_dzi(self):
        return self._dz.get_dzi(self._img_format)


class WholeSlideTiler(object):
    """Handles generation of tiles and metadata for all images in a slide."""

    def __init__(self, slide_path, basepath, img_format, tile_size, overlap,
                 limit_bounds, quality, nworkers, only_last):

        self._slide = open_slide(slide_path)  # the whole slide image
        self._basepath = basepath  # baseline name of each tiled image
        self._img_format = img_format  # image format (jpeg or png)
        self._tile_size = tile_size  # tile size. default: 256x256 pixels
        self._overlap = overlap  # ??
        self._limit_bounds = limit_bounds  # ??
        self._queue = JoinableQueue(2 * nworkers)  # setup multiprocessing worker queues.
        self._nworkers = nworkers  # number of workers
        self._only_last = only_last
        self._dzi_data = {}
        for _i in range(nworkers):
            TileWorker(self._queue, slide_path, tile_size, overlap,
                       limit_bounds, quality).start()

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
            basepath = self._basepath

        else:
            image = ImageSlide(self._slide.associated_images[associated])
            basepath = os.path.join(self._basepath, self._slugify(associated))

        dz = DeepZoomGenerator(image, self._tile_size, self._overlap, self._limit_bounds)

        tiler = SingleImageTiler(dz, basepath, self._img_format, associated,
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
