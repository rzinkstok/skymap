import math
import re


class PaperSize(object):
    """General class for paper sizes.

    For every papersize, the class contains a regular expression match pattern for the name
    and a method named ``get_<basename>_papersize``. The match pattern should include at least a group
    for the basename of the papersize, which might be the full name. This basename is used to identify
    the correct method to call. If more than one group is defined in the match pattern, the rest of
    the groups are passed as arguments to the method. The method should have ``landscape`` as the final
    argument.

    For aliases, a separate dict is used: any name is first checked for aliases, and the canonical name is
    used to determine the paper size.

    Args:
        width (float): the width of the paper size in mm
        height (float): the height of the paper size in mm
        name (str): the name of the paper size
        landscape (bool): whether to set the largest value to width or not
    """

    MATCH_TARGETS = (
        re.compile("(a)(\d+)"),
        re.compile("(b)(\d+)"),
        re.compile("(c)(\d+)"),
        re.compile("(ansi)-([a-e])"),
        re.compile("(legal)"),
    )
    ALIASES = {"letter": "ANSI-A", "tabloid": "ANSI-B"}

    def __init__(self, name="", width=None, height=None, landscape=False):
        if not (width or height or name):
            name = "A4"
        self.width = width
        self.height = height
        self.name = name
        self.landscape = landscape

        if self.width is None and self.height is None and self.name:
            # No width/height passed in, but a name is given
            if self.name in self.ALIASES:
                name = self.ALIASES[self.name]

            for mt in self.MATCH_TARGETS:
                m = mt.match(name.lower())
                if not m:
                    continue

                # Extract the basename and arguments for the method from the name
                basename = m.groups()[0]
                args = m.groups()[1:]

                try:
                    func = getattr(self, "_get_{}_papersize".format(basename))
                except AttributeError:
                    raise ValueError("Unable to parse papersize name")

                self.width, self.height = func(*args, landscape=self.landscape)

    def _get_a_papersize(self, index, landscape=False):
        """Returns the papersize from the A series with the given index number.

        The A series is defined by setting the area of A0 to 1 square meter requiring that
        the ratio between the largest and the smallest side is equal to the square root of 2, and
        that successive members in the series have half the area. The result is rounded to an integer
        number of mm.

        Args:
            index (int): the A series number to retrieve the papersize for (e.g. the 4 in A4)
            landscape (bool): whether to return a landscape papersize or not

        Returns:
            tuple: the requested papersize (width, height) in mm
        """
        index = int(index)
        x = int(round(math.sqrt(1e6 / (pow(2, index) * math.sqrt(2)))))
        y = int(round(math.sqrt(2) * x))

        if landscape:
            x, y = y, x
        return x, y

    def _get_b_papersize(self, index, landscape=False):
        """Returns the papersize from the B series with the given index number.

        The B series is defined by taking the geometric mean of areas of the A series papersizes
        with indices that are equal and one lower than the B series index. The ratio between the
        largest and smallest size is again equal to the square root of 2. The geometric mean of
        two numbers is defined as the square root of the product of the two numbers.

        Args:
            index (int): the B series number to retrieve the papersize for (e.g. the 4 in B4)
            landscape (bool): whether to return a landscape papersize or not

        Returns:
            tuple: the requested papersize (width, height) in mm
        """
        index = int(index)
        x1, y1 = self._get_a_papersize(index - 1, landscape)
        x2, y2 = self._get_a_papersize(index, landscape)

        area1 = x1 * y1
        area2 = x2 * y2
        area = math.sqrt(area1 * area2)
        x = int(round(math.sqrt(area / math.sqrt(2))))
        y = int(round(x * math.sqrt(2)))

        return x, y

    def _get_c_papersize(self, index, landscape=False):
        """Returns the papersize from the C series with the given index number.

        The C series is defined by taking the geometric mean of areas of the A series papersize
        and the B series papersize with the same index. The ratio between the largest and smallest
        size is again equal to the square root of 2. The geometric mean of two numbers is defined
        as the square root of the product of the two numbers.

        Args:
            index (int): the B series number to retrieve the papersize for (e.g. the 4 in C4)
            landscape (bool): whether to return a landscape papersize or not

        Returns:
            tuple: the requested papersize (width, height) in mm
        """
        index = int(index)
        x1, y1 = self._get_a_papersize(index, landscape)
        x2, y2 = self._get_b_papersize(index, landscape)

        area1 = x1 * y1
        area2 = x2 * y2
        area = math.sqrt(area1 * area2)
        x = int(round(math.sqrt(area / math.sqrt(2))))
        y = int(round(x * math.sqrt(2)))

        return x, y

    def _get_ansi_papersize(self, index, landscape=False):
        n = ord(index) - ord("a") + 1
        x, y = 216, 279
        if landscape:
            x, y = y, x
        return n * x, n * y

    def _get_legal_papersize(self, landscape=False):
        x, y = 216, 356
        if landscape:
            x, y = y, x
        return x, y

    def __repr__(self):
        return "PaperSize({}, {} mm x {} mm)".format(self.name, self.width, self.height)


class PaperMargin(object):
    def __init__(self, left=24, bottom=24, right=None, top=None):
        self.left = left
        self.bottom = bottom
        self.right = left if right is None else right
        self.top = bottom if top is None else top

    @property
    def l(self):
        return self.left

    @property
    def r(self):
        return self.right

    @property
    def t(self):
        return self.top

    @property
    def b(self):
        return self.bottom

    def __repr__(self):
        return "PaperMargins(left {} mm, right {} mm, top {} mm, bottom {} mm)".format(
            self.left, self.right, self.top, self.bottom
        )


if __name__ == "__main__":
    print(PaperSize())
    print(PaperSize("ANSI-A"))
    print(PaperSize("letter"))
    print(PaperSize("A4"))
    print(PaperSize("A3"))
    print(PaperSize("A2"))

    print(PaperMargin(24, 24))
    print(PaperMargin(0, 0))
    print(PaperMargin())
