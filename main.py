import glob
import os

import config as cfg
from epi import gen_epi_addrs
from tiler import WholeSlideTiler




def main():
    # open input_path, and process each wholeslide image
    files = glob.glob(cfg.IMAGE_FOLDER_PATH + '/*.svs')
    print(len(files))
    i = 1
    for slidepath in files:
        print("processing {0} of {1} whole slide images".format(i, len(files)))
        print(slidepath)
        basename = os.path.splitext(os.path.basename(slidepath))[0]
        basepath = os.path.join(cfg.OUTPUT_FOLDER_PATH, basename)

        epi_addrs = gen_epi_addrs(basename, cfg.LEIDOS_PATH)

        WholeSlideTiler(slidepath, basepath, epi_addrs, cfg.IMG_FORMAT, cfg.TILE_SIZE, cfg.STRIDE, cfg.LIMIT_BOUNDS, cfg.ROTATE, cfg.QUALITY,
                        cfg.NUM_WORKERS, cfg.ONLY_LAST).run()
        i += 1


if __name__ == '__main__':
    main()
