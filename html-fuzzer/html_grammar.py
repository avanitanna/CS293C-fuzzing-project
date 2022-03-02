import sys
sys.path.append("../")

# from fuzzingbook import Grammars
from fuzzingbook.Grammars import *

HTML_GRAMMAR: Grammar = {
    "<start>": ["<!DOCTYPE html><<body>><html-tree></<body>>"],
    "<html-tree>": ["<text>",
                   "<html-open-tag><html-tree>",
                   "<html-tree><html-tree>"],
    "<html-open-tag>":     ["<id>"],
    "<id>":                ["<letter_keywords>", "<id><letter_keywords>","<keywords>"],
    "<text>":              ["<text><letter_space>", "<letter_space>", "<letter_space><text>", "<letter>"],
    "<letter>":            srange(string.ascii_letters + string.digits +
                                  "\"" + " " + "."),
    "<letter_space>":      srange(string.ascii_letters + string.digits +
                                  "\"" + " " + "\t"),
    "<keywords>" : ["<<script>><text></<script>>","<<style>><text></<style>>","<<div>><text></<div>>"],
    "<letter_keywords>": ["<<p>><text></<p>>","<<b>><text></<b>>","<<i>><text></<i>>","<<a> href='<text>'></<a>>",
    "<<u>><text></<u>>", "<<br>>"],
    "<p>":["p"],
    "<a>":["a"],
    "<b>":["b"],
    "<i>":["i"],
    "<br>":["br"],
    "<u>":["u"],
    "<body>":["body"],
    "<script>":["script"],
    "<style>":["style"],
    "<div>":["div"],
}