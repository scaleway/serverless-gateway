from os.path import join
from subprocess import run

from ..util.const import PROJ_ROOT

CONTAINER_ROOT = join(PROJ_ROOT, "container")

DOCKERFILE = join(CONTAINER_ROOT, "Dockerfile")

DOCKER_TAG = "scw-gw"


def build():
    cmd = ["docker", "build", f"-t {DOCKER_TAG}", "."]

    run(" ".join(cmd), shell=True, check=True, cwd=CONTAINER_ROOT)


def push():
    cmd = ["docker", "push", f"-t {DOCKER_TAG}"]

    run(" ".join(cmd), shell=True, check=True, cwd=CONTAINER_ROOT)
