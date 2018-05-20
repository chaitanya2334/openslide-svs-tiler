import os

# directory of the config file
CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))

DEFAULT_FILENAME = 'slide'

IMAGE_FOLDER_PATH = "/fs/scratch/osu1522/TCGA/subset_wsi/"

OUTPUT_FOLDER_PATH = "/fs/scratch/osu1522/TCGA/subset_tiled/"

LEIDOS_PATH = os.path.join(CURRENT_DIR, "../leidos_output/output_features/")

IMG_FORMAT = 'png'

TILE_SIZE = 224

STRIDE = 110

LIMIT_BOUNDS = True

QUALITY = 100

NUM_WORKERS = 28

ONLY_LAST = True

SAVE_REJECTED = False

REJECT = True

# increase this to reject more
REJECT_THRESHOLD = 200

ROTATE = False

MAX_WHITE_SIZE = (TILE_SIZE*TILE_SIZE)/2

LEIDOS_TILESIZE = 4096

SIMPLE_THRESHOLDING = False

def ver_print(string, value):
    print(string + " {0}".format(value))
