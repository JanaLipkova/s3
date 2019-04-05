import inspect
import os


def get_relative_path(file_path):
    dirname = os.path.dirname(os.path.abspath(inspect.stack()[0][1]))
    file_path = os.path.join(dirname, file_path)

    return file_path


def getopts(argv):
    opts = {}  # Empty dictionary to store key-value pairs.
    while argv:  # While there are arguments left to parse...
        if argv[0][0] == '-':  # Found a "-name value" pair.
            if argv[0][1] == "t":
                opts[argv[0]] = 1
            elif argv[0][1] == "a":
                opts[argv[0]] = 1
            else:
                opts[argv[0]] = argv[1]  # Add key and value to the dictionary.
        argv = argv[1:]  # Reduce the argument list by copying it starting from index 1.
    return opts
