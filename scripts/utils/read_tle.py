from pathlib import Path
from pprint import pprint

def read_tle():
    path = str(Path(__file__).parent.parent.parent.as_posix()) + "/config/tle.cfg"
    file = open(path, "r")
    lines = file.readlines()
    satellites = []
    sat = []
    current_line = 0
    for line in lines:
        sat.append(line)
        if current_line == 2:
            if int(line[0]) != 2:
                raise Exception(f'error when laoding tle file at location: "{path}"')
            current_line = 0
            satellites.append(''.join(sat))
            sat = []
        else:
            current_line += 1
    print(f'loaded {len(satellites)} files from tle config')
    return satellites


if __name__ == "__main__":
    print(read_tle())