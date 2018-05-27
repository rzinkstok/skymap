import math
from collections import OrderedDict




class FontSize(OrderedDict):
    """Class for generating a series of LaTeX fontsizes.

    Several functions are available for generating a fontsize series:
    - exp, an exponential function
    - lin, a linear function
    - linexp, linear below normalsiza and exponential above normalsize

    As an alternative, a custom function can be passed in: this function should
    accept a single int argument, return the normalsize value when passed zero as
    argument, and the appropriate values for the other sizes, which are indicated
    by the indices in the SIZENAMES tuple minus the index of normalsize.

    Args:
        normalsize (int): the fontsize in points for the normalsize font
        sizefunc (str): the type of generator function for the fontsize series
    """
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

    def __init__(self, normalsize=11, sizefunc="exp"):
        OrderedDict.__init__(self)
        self.normalsize = normalsize
        self.normalindex = self.SIZENAMES.index("normalsize")

        try:
            self.sizefunc = getattr(self, "_" + sizefunc)
        except TypeError:
            self.sizefunc = sizefunc

        for index, sn in enumerate(self.SIZENAMES):
            self[sn] = self.sizefunc(index-self.normalindex)

    def _exp(self, index):

        return int(round(self.normalsize * math.exp(0.1515 * index)))

    def _lin(self, index):
        return self.normalsize + index

    def _linexp(self, index):
        if index >= 0:
            return self._exp(index)
        return self._lin(index)


if __name__ == "__main__":
    fs = FontSize(11, "exp")
    for sn, s in fs.items():
        print sn, "->", s
    print
    fs = FontSize(11, lambda x: (x+6)**2)
    for sn, s in fs.items():
        print sn, "->", s
