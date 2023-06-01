import os

class Options:
    # Sets the global home of the project (useful for running external tools)
    PYSZZ_HOME = os.path.dirname(os.path.realpath(__file__))

    TEMP_WORKING_DIR = '_szztemp'
