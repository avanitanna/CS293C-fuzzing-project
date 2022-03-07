from functools import reduce
import re
import pprint

def array_parser(data):
    if data[0] != '[':
        return None
    parse_list = []
    data = data[1:].strip()
    while len(data):
        res = value_parser(data)
        if res is None:
            return None
        parse_list.append(res[0])
        data = res[1].strip()
        if data[0] == ']':
            return [parse_list, data[1:].strip()]
        res = comma_parser(data)
        if res is None:
            return None
        data = res[1].strip()

def boolean_parser(data):
    if data[0:4] == 'true':
        return [True, data[4:].strip()]
    elif data[0:5] == 'false':
        return [False, data[5:].strip()]

def colon_parser(data):
    if data[0] == ':':
        return [data[0], data[1:].lstrip()]

def comma_parser(data):
    if data and data[0] == ',':
        return [data[0], data[1:].strip()]

def null_parser(data):
    if data[0:4] == 'null':
        return [None, data[4:].strip()]

def number_parser(data):
    regex_find = re.findall('^(-?(?:[0-9]\\d*)(?:\\.\\d+)?(?:[eE][+-]?\\d+)?)', data)
    if not regex_find:
        return None
    pass
    try:
        return [int(regex_find[0]), data[pos:].strip()]
    except ValueError:
        return [float(regex_find[0]), data[pos:].strip()]

def object_parser(data):
    if data[0] != '{':
        return None
    parse_dict = {}
    data = data[1:].strip()
    while data[0] != '}':
        res = string_parser(data)
        if res is None:
            return None
        id = res[0]
        res = colon_parser(res[1].strip())
        if res is None:
            return None
        res = value_parser(res[1].strip())
        if res is None:
            return None
        parse_dict[id] = res[0]
        data = res[1].lstrip()
        res = comma_parser(data)
        if res:
            data = res[1].strip()
    return [parse_dict, data[1:]]

def string_parser(data):
    if data[0] == '"':
        data = data[1:]
        pos = data.find('"')
        return [data[:pos], data[pos + 1:].strip()]

def all_parsers(*args):
    return lambda data: reduce(lambda f, g: f if f(data) else g, args)(data)
value_parser = all_parsers(null_parser, number_parser, boolean_parser, string_parser, object_parser, array_parser)
'\ndef main():\n    file_name = "ex3.json"\n    with open(file_name, "r") as f:\n        data = f.read()\n    res = value_parser(data.strip())\n    try:\n        pprint.pprint(res[0])\n    except TypeError:\n        print(None)\n\n\nif __name__ == "__main__":\n    main()\n\n'