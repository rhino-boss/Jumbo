import pandas as pd
import numpy as np
import time
import math
import matplotlib.pyplot as plt
from datetime import datetime


# Show


class div:
    def __init__(self) -> None:
        pass

    def div_right(div_str, div_symbol="=", all_len=60, end_len=3):
        """
        Examples
        --------
        >>> print_div_____str_____(div_str='div_str', div_symbol="=", all_len=60, end_len=3)
        '================================================ div_str ==='

        >>> print_div_____str_____(div_str='div_str', div_symbol="=", all_len=60, end_len=3)
        '------------------------------------------------ div_str ---'

        """

        # end_len = all_len - len(div_str) - start_len - 2
        start_len = all_len - len(div_str) - end_len - 2
        if end_len < 0 | start_len < 0:
            print("out of range.")
            return

        # start print div
        print("")

        for i in range(start_len):
            print(div_symbol, end="")

        print(f" {div_str} ", end="")

        for i in range(end_len):
            print(div_symbol, end="")

        print()

    def div_center(div_str, div_symbol="-", len=3, upper=False, lower=True):
        if upper:
            print("")

        print(div_symbol * len, div_str, div_symbol * len)

        if lower:
            print("")


class format_setting:
    def __init__(self) -> None:
        pass

    def probability_and_round(value):
        """
        Examples
        --------
        >>> probability_and_round(0.210000)
        '0.21% (約5場)'
        
        """
        return "{0:0.2f}% (約{1:0.0f}場)".format(value, 1 / value)

    def thousands_style(num):
        """
        Examples
        --------
        >>> thousands_style(100000000)
        100,000,000

        """
        str_ = str(num)
        show_str = ""
        cnt = 0
        for i in str_[::-1]:
            cnt += 1
            show_str = i + show_str
            if cnt == 3 and i != str_[0]:
                show_str = "," + show_str
                cnt = 0
        return show_str


class log_use:
    def __init__(self) -> None:
        pass

    def print_run_log(*content):
        """
        Examples
        --------
        >>> print_run_log('content1', 'content2')
        log: ('content1', 'content2')

        >>> print_run_log('content1')
        log: content1

        """
        if len(content) == 1:
            print(f"log: {content[0]}")
        else:
            print(f"log: {content}")

    def print_result(*content, tag=">>> ", next_line=False, end_next_line=False):
        """
        Examples
        --------
        >>> print_result('aa', 10, 'bb', 20)
        'aa: 10, bb: 20'

        >>> print_result('aa', 10, 'bb', 20, tag='*')
        '* aa: 10, bb: 20'
        """
        str_ = ""
        for i, c in enumerate(content):
            c = str(c)
            if i % 2 == 0:
                if next_line:
                    str_ += c + ": \n"
                else:
                    str_ += c + ": "
            elif i == len(content) - 1:
                str_ += c
            else:
                str_ += c + ", "

        print(tag, str_)

        if end_next_line:
            print("")


# Else


def write_log(value1=0, value2=0, value3=0, log=""):
    """
    use format:
        write_log(1, 2, 300)

    """
    log_data = pd.read_excel("Log/Log.xlsx")
    add = log_data.copy().iloc[-1]

    add.idx += 1
    add.time = datetime.now()

    add.value1 = value1
    add.value2 = value2
    add.value3 = value3
    add.log = log

    add = add.to_frame().T
    new_data = pd.concat([log_data, add], axis=0)
    new_data.to_excel("Log/Log.xlsx", sheet_name="log_data", index=False)

    return new_data


def get_value(cum_weight):
    """
    get random index of value by cumulative weight.

    input cum Weight, output random index(position).

    Examples
    --------
    >>> get_value([1,3,5])
    2

    Test
    --------
    aa = [0, 0, 0, 0, 0]
    bb = np.array([60, 30, 10, 1, 1]).cumsum()
    # bb = np.array([1, 2, 3, 4, 5]).cumsum()

    tt = 10**5
    for i in range(tt):
        cc = get_value(bb)
        # print(cc)
        aa[cc] += 1

    np.array(aa)/tt
    """
    rd = np.random.randint(0, cum_weight[-1])
    for i in range(len(cum_weight)):
        if rd < cum_weight[i]:
            return i


def by_bin(status_):
    """
    Examples
    --------
    >>> by_bin(0, 1, 0, 0, 0)
    8   
    """
    num = 0
    for i, s in enumerate(status_[::-1]):
        num += s * 10 ** i

    return int("0b" + str(num), 2)


def show_bin_table(group_num):
    temp = []
    max_len = 2 ** group_num

    for i in range(group_num):
        temp.append(2 ** i)

    combo = []
    for i, num in enumerate(temp):
        rn = [0] * num
        rn.extend([1] * num)
        rn *= int(max_len / num)
        combo.append(rn)

    combo = np.array(combo)
    li = []
    for i in range(max_len):
        idx = by_bin(tuple(combo[:, i]))
        info = "".join(np.array(combo[:, i], dtype=str))
        li.append((idx, info))
    li.sort()

    # print
    print("--- symbol info ---")

    for i in li:
        print(i[0], ": ", i[1])

    print("---")

