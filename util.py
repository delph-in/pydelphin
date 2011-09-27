# Utility functions for python-delphin

def unique_filename(filename, max_num=999):
    """
    Returns a unique filename for the filename given by appending a number.
    By default, an exception is raised if the number exceeds 999.

    @param filename: The base filename to be made unique.
    @param max_num: The highest number value to append to the base filename.
    """
    import os
    i = 0
    new_filename = filename
    while os.path.exists(new_filename):
        i += 1
        if i > max_num:
            raise ValueError('Filename extension out of range (%d)' % max_num)
        new_filename = '.'.join([filename, str(i)])
    return new_filename
