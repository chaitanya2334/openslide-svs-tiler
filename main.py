import glob
import os
from argparse import ArgumentParser

from tqdm import tqdm

import config as cfg
from tiler import WholeSlideTiler

def setup_argparser():
    parser = ArgumentParser(description='Tiler')
    parser.add_argument('S', type=int,
                        help='an integer, to specify the Sth wsi from where to start tiling')

    args = parser.parse_args()
    return args

def main():
    # open input_path, and process each wholeslide image
    args = setup_argparser()
    files = sorted(glob.glob(cfg.IMAGE_FOLDER_PATH + '/*.svs'))
    if args.S < len(files):
        for slidepath in tqdm(files[args.S:]):
            print("starting from: {0}".format(args.S))
            basename = os.path.splitext(os.path.basename(slidepath))[0]
            basepath = os.path.join(cfg.OUTPUT_FOLDER_PATH, basename)
            WholeSlideTiler(slide_path=slidepath,
                            outpath=basepath,
                            img_format=cfg.IMG_FORMAT,
                            tile_size=cfg.TILE_SIZE,
                            stride=cfg.STRIDE,
                            limit_bounds=cfg.LIMIT_BOUNDS,
                            rotate=cfg.ROTATE,
                            quality=cfg.QUALITY,
                            nworkers=cfg.NUM_WORKERS,
                            only_last=cfg.ONLY_LAST).run()


if __name__ == '__main__':
    main()
