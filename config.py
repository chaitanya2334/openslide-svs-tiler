import os

# directory of the config file
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

DEFAULT_FILENAME = 'slide'

IMAGE_FOLDER_PATH = os.path.join(CURRENT_DIR, "input/images/")

OUTPUT_FOLDER_PATH = os.path.join(CURRENT_DIR, "output/")

IMG_FORMAT = 'jpeg'

TILE_SIZE = 2000

OVERLAP = 1

LIMIT_BOUNDS = True

QUALITY = 100

NUM_WORKERS = 8

ONLY_LAST = True


def ver_print(string, value):
    print(string + " {0}".format(value))
