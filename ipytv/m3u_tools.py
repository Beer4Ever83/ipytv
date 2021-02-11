#!/usr/env/bin python3
import regex


class M3UFileDoctor:
    @staticmethod
    def fix_split_quoted_string(infile, outfile):
        with open(infile) as file:
            buffer = file.readlines()
        output = M3UDoctor.fix_split_quoted_string(buffer)
        with open(outfile, "w") as file:
            file.write(output)


class M3UDoctor:
    '''
    This covers the case of rows beginning with double quotes that belong to the previous row.
    Example:
        #EXTINF:-1 tvg-id="Cinema1
        " tvg-name="Cinema1" group-title="Cinema",Cinema One
    '''
    @staticmethod
    def fix_split_quoted_string(buffer):
        if isinstance(buffer, str):
            buffer = buffer.split("\n")
        lines = len(buffer)
        for index in range(lines):
            if regex.match("^[[:space:]]*\"", buffer[index]):
                buffer[index] = buffer[index].replace("\"", "", 1)
                buffer[index-1] = buffer[index-1].rstrip() + "\""
        return "".join(buffer)
