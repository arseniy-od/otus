def left_bound(_list, key):
    left = -1
    right = len(_list)
    while right - left > 1:
        middle = (left + right) // 2
        if _list[middle] < key:
            left = middle
        else:
            right = middle
    return left


def right_bound(_list, key):
    left = -1
    right = len(_list)
    while right - left > 1:
        middle = (left + right) // 2
        if _list[middle] <= key:
            left = middle
        else:
            right = middle
    return right
