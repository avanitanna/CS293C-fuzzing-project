import sys
sys.path.append("../")

# from fuzzingbook import Grammars
from fuzzingbook.Grammars import *

#error causing inputs 
# v2.9 onwards
# https://github.com/pallets/jinja/issues/669
# jinja2.Template('{% for value in values recursive %}1{% else %}0{% endfor %}').render(values=[])
# expected output: u'0'
# error output: crash failure/ syntaxerror

# https://github.com/pallets/jinja/issues/739
# template = Template('''
# {%- for i in range(10) -%}
# {{ ['foo', 'bar', 'baz', 'eggs', 'ham', 'spam'] | random }}{{ ' ' }}
# {%- endfor %}
# ''')
# print(template.render())
# expected output: <random set of strings>
#error output: <only one set of strings>

#https://github.com/pallets/jinja/issues/794, https://github.com/pallets/jinja/issues/244, https://github.com/pallets/jinja/issues/751
# jinja2.Template("{% for i in lst|reverse %}{{ loop.revindex }}:{{ i }}, {% endfor %}")
#   .render(lst=[10])
# expected output: '1:10, '
# error output: '2:10, '

#test against version 2.11

JINJA_GRAMMAR: Grammar = {
    "<start>":["<for>"],
    "<for>": ["'{% for i in <list> %}<forbody><forend>"],
    "<forbody>" : ["{{ [<stringchain>] | random }}{{ ' ' }}", "\"<string>\"{%else%}\"<string>\"", "{{ <helper> }}:{{ i }}, "],
    "<stringchain>":["\"<string>\",<stringchain>","\"<string>\""],
    "<string>": srange(string.ascii_letters + string.digits +
                                  "\"" + " " + "."),
    "<forend>" : ["{% endfor %}'"],
    "<helper>": ["loop.revindex", "loop.index", "loop.first", "loop.last", "loop.revindex0", "loop.index0", "loop.depth"],
    "<filter>": ["random","reverse"],
    "<list>": ["values", "values recursive", "values|<filter>"],
   }