from os.path import dirname, expanduser, join, realpath

USER_HOME = expanduser("~")
PROJ_ROOT = dirname(dirname(dirname(dirname(realpath(__file__)))))
CONTAINER_ROOT = join(PROJ_ROOT, "container")
