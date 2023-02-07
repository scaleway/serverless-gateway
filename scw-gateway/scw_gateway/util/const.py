from os.path import expanduser, join, realpath
from os import dirname

USER_HOME = expanduser("~")
PROJ_ROOT = dirname(dirname(realpath(__file__)))
CONTAINER_ROOT = join(PROJ_ROOT, "container")
