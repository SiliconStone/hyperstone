from typing import Iterable, Dict, Any, List

from hyperstone.util.logger import log


TAB_SIZE = 8
DEFAULT_TAB_COUNT = 1
TAB_CHARACTER = '\t'

def tabbed_print(*, header: List[str], body: Iterable[Dict[str, Any]],
                 amount_per_line: int = 1, tab_size: int = TAB_SIZE) -> None:
    """
    This function prints data in a formatted way, based on items' length

    :param header: The headers to print (inc. the keys, ordered)
    :param body: Content to print
    :param amount_per_line: Amount to print per line
    :param tab_size: Size of a tab in spaces on your machine
    """
    body_max = {}
    body_clone = list(body)

    for i, key in enumerate(header):
        # No need to add tabs at end of line
        if len(header) - 1 == i and amount_per_line == 1:
            body_max[key] = 0
            continue

        for entry in body_clone:
            current_length = (len(entry[key]) // tab_size) + 1
            if key not in body_max:
                body_max[key] = current_length
                continue

            if current_length > body_max[key]:
                body_max[key] = current_length

    for _ in range(amount_per_line):
        for key in header:
            if 0 == len(body_clone):
                tabs_needed = DEFAULT_TAB_COUNT
            else:
                tabs_needed = body_max[key] - (len(key) // tab_size)

            print(key, end=TAB_CHARACTER * tabs_needed)


    print('\n')

    for i, entry in enumerate(body_clone):
        for key in header:
            tabs_needed = body_max[key] - (len(entry[key]) // tab_size)
            print(entry[key], end=TAB_CHARACTER * tabs_needed)

        if (i + 1) % amount_per_line == 0:
            print()

    print()
