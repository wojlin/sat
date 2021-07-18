from pathlib import Path
from pprint import pprint

def read_current_pos():
    path = str(Path(__file__).parent.parent.parent.as_posix()) + "/config/current_position.cfg"
    file = open(path, "r")
    lines = file.readlines()
    current_position_str = str(lines[0]).split(',')
    return [float(current_position_str[0]), float(current_position_str[1])]


if __name__ == "__main__":
    print(read_current_pos())