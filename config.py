import os

# directory of the config file
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

DEFAULT_FILENAME = 'slide'

IMAGE_FOLDER_PATH = os.path.join(CURRENT_DIR, "../fs/scratch/osu1522/TCGA/wsi/")

OUTPUT_FOLDER_PATH = os.path.join(CURRENT_DIR, "/fs/scratch/osu1522/TCGA/tiled/")

LEIDOS_PATH = os.path.join(CURRENT_DIR, "../leidos_output/output_features/")

IMG_FORMAT = 'png'

TILE_SIZE = 224

STRIDE = 75

LIMIT_BOUNDS = True

QUALITY = 100

NUM_WORKERS = 24

ONLY_LAST = True

SAVE_REJECTED = False

DONT_REJECT = False

# increase this to reject more
REJECT_THRESHOLD = 200

ROTATE = True

MAX_WHITE_SIZE = (TILE_SIZE*TILE_SIZE)/2

LEIDOS_TILESIZE = 4096

SIMPLE_THRESHOLDING = False

def ver_print(string, value):
    print(string + " {0}".format(value))
