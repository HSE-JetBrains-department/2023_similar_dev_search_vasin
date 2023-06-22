from typing import Tuple, Counter


class DeveloperEntry:
    def __init__(self):
        self.data = Tuple[Counter, Counter]()

    def __getitem__(self, item):
        return self.data[item]