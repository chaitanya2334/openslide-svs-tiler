import glob
import os
from collections import namedtuple

import config as cfg

import re
import pandas as pd

Epi_Address = namedtuple('Epi_Address', ['x', 'y', 'w', 'h'])


def extract_x_y(digits, tilesize):
    for i in range(1, len(digits) + 1):
        x = int(digits[:i])
        y = int(digits[i:])
        if x % tilesize == y % tilesize == 0:
            print(x, y)
            return x, y

def is_non_zero_file(fpath):
    return True if os.path.isfile(fpath) and os.path.getsize(fpath) > 0 else False

def gen_epi_addrs(slidebasename, epi_path):
    base = os.path.join(epi_path, slidebasename)
    files = glob.glob(base + "*_Epi_Features.txt")
    ret = []
    for file in files:
        if is_non_zero_file(file):
            digits = re.search(base + "(.*)" + "_Epi_Features\.txt", file)
            x, y = extract_x_y(digits.group(1), cfg.LEIDOS_TILESIZE)

            df = pd.read_csv(file, header=None, usecols=[0, 1, 4, 5])
            for row in df.itertuples():
                rel_x = row[1]
                rel_y = row[2]
                w = row[3]
                h = row[4]
                ret.append(Epi_Address(x + rel_x - w / 2, y + rel_y - h / 2, w, h))

    return ret


if __name__ == '__main__':
    slidepaths = glob.glob("Images/*")
    for slidepath in slidepaths:
        basename = os.path.splitext(os.path.basename(slidepath))[0]
        basepath = os.path.join(cfg.OUTPUT_FOLDER_PATH, basename)
        gen_epi_addrs(basename, "output_features/")
