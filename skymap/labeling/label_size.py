from skymap.tikz import Tikz


def calculate_label_sizes(labeldict, normalsize=11, fontsize="normal", verbose=False):
    """
    Calculates the size of the bounding box for the labels generated from the give object names.

    The function returns a dict where each object id is mapped to a dict containing the label text, label width
    and label height.

    Args:
        labeldict (dict): object id, label text pairs
        normalsize (int): the point size for LaTeX's normalsize
        fontsize (str): the label fontsize (LaTeX name)
        verbose (bool): whether to print info to stdout

    Returns:
        dict: object_id, label size dict pairs
    """
    t = Tikz("labels", template="labels.j2", normalsize=normalsize)
    texoutput = t.render(extra_context={"labels": labeldict, "fontsize": fontsize})

    result = {}
    processing = False
    for l in texoutput.split("\n"):
        if l.startswith("START SKYMAP LABELS"):
            processing = True
            continue
        elif l.startswith("END SKYMAP LABELS"):
            processing = False
            continue
        if processing:
            parts = l.split("|")
            object_id = int(parts[0])
            label_text = parts[1]
            label_width = float(parts[2])
            label_height = float(parts[3])
            result[object_id] = {
                "label_text": label_text,
                "label_width": label_width,
                "label_height": label_height
            }
            if verbose:
                print("---------------------")
                print(f"Object ID: {object_id}")
                print(f"Label text: {label_text}")
                print(f"Label width: {label_width}")
                print(f"Label height: {label_height}")

    return result
