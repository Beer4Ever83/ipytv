#!/usr/env/bin python3
from typing import List

import re


class M3UFileDoctor:
    @staticmethod
    def fix_split_quoted_string(infile: str, outfile: str):
        with open(infile, encoding='utf-8') as file:
            buffer = file.readlines()
        output_str = "".join(M3UDoctor.fix_split_quoted_string(buffer))
        with open(outfile, "w", encoding='utf-8') as file:
            file.write(output_str)


class M3UDoctor:
    '''
    This covers the case of rows beginning with double quotes that belong to the previous row.
    Example:
        #EXTINF:-1 tvg-id="Cinema1
        " tvg-name="Cinema1" group-title="Cinema",Cinema One
    '''
    @staticmethod
    def fix_split_quoted_string(buffer: List) -> List:
        lines = len(buffer)
        for index in range(lines):
            if re.match("^[[:space:]]*\"", buffer[index]):
                buffer[index] = buffer[index].replace("\"", "", 1)
                buffer[index-1] = buffer[index-1].rstrip() + "\""
        return buffer
