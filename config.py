import os

# directory of the config file
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

DEFAULT_FILENAME = 'slide'

IMAGE_FOLDER_PATH = os.path.join(CURRENT_DIR, "input/chromophobe")

OUTPUT_FOLDER_PATH = os.path.join(CURRENT_DIR, "output/chromophobe")

IMG_FORMAT = 'jpeg'

TILE_SIZE = 149+64

OVERLAP = 75-32

LIMIT_BOUNDS = True

QUALITY = 100

NUM_WORKERS = 4

ONLY_LAST = True

SAVE_REJECTED = False

DONT_REJECT = False

# increase this to reject more
REJECT_THRESHOLD = 200

ROTATE = True

MAX_WHITE_SIZE = (TILE_SIZE*TILE_SIZE)/2

def ver_print(string, value):
    print(string + " {0}".format(value))
