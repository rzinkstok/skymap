import math


class FontSize(object):
    SIZENAMES = (
        'nano',
        'miniscule',
        'tiny',
        'scriptsize',
        'footnotesize',
        'small',
        'normalsize',
        'large',
        'Large',
        'LARGE',
        'huge',
        'Huge',
        'HUGE'
    )

    def __init__(self, normalsize=11):
        self.normalsize = normalsize

    def _calculate_fontsize(self, sizename):
        index = self.SIZENAMES.index(sizename) + 1
        return int(round((self.normalsize / 11.0) * 3.8282 * math.exp(0.1515 * index)))

    def __getitem__(self, item):
        return self._calculate_fontsize(item)


if __name__ == "__main__":
    fs = FontSize(12)
    for sn in fs.SIZENAMES:
        print sn, "->", fs[sn]