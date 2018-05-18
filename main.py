import glob
import os

from tqdm import tqdm

import config as cfg
from tiler import WholeSlideTiler


def main():
    # open input_path, and process each wholeslide image
    files = glob.glob(cfg.IMAGE_FOLDER_PATH + '/*.svs')
    for slidepath in tqdm(files):
        basename = os.path.splitext(os.path.basename(slidepath))[0]
        basepath = os.path.join(cfg.OUTPUT_FOLDER_PATH, basename)
        WholeSlideTiler(slidepath, basepath, cfg.IMG_FORMAT, cfg.TILE_SIZE, cfg.OVERLAP, cfg.LIMIT_BOUNDS, cfg.ROTATE,
                        cfg.QUALITY, cfg.NUM_WORKERS, cfg.ONLY_LAST).run()


if __name__ == '__main__':
    main()
