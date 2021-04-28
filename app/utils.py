import os

def is_not_empty(fpath):
    return os.path.isfile(fpath) and os.path.getsize(fpath) > 0


def write_to_file(fpath, data_to_write, isImage=False):
    if isImage:
        f = open(fpath, "wb")
        f.write(data_to_write)
    else:
        f = open(fpath, "w+")
        f.write(data_to_write.decode('utf-8'))
    f.close
    print(f'Wrote to {fpath}')