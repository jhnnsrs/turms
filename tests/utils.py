import os

DIR_NAME = os.path.dirname(os.path.realpath(__file__))


def build_relative_glob(path):
    return DIR_NAME + path
