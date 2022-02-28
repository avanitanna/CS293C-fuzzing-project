import sys
sys.path.append("../")

# from fuzzingbook import Grammars
from fuzzingbook.Grammars import *

#table 
fields = []
SQL_GRAMMAR: Grammar = {
    '<Query>':
        ['SELECT <SelList> FROM <FromList> WHERE <Condition>'],
    #  'SELECT <SelList> FROM <FromList>',
    #  'SELECT * FROM <FromList>',
        #  'INSERT INTO <FromList> VALUES ("' + '", "'.join(types) + '")'],
    '<SelList>':
        ['<Attribute>', '<SelList>, <Attribute>'],
    '<FromList>':
        ['<Relation>'],
    '<Condition>':
        ['<Comparison>', '<Condition> AND <Comparison>',
            '<Condition> OR <Comparison>'],
    '<Comparison>':
        [f'{f} {c} "{t}"' for f, c, t in zip(fields, comparators, types)],
    '<Comparator>':
        ['<', '<=', '=', '<LAngle><RAngle>', '>=', '>'],
    '<StringComparator>':
        ['=', '<LAngle><RAngle>'],
    '<LAngle>': ['<'],
    '<RAngle>': ['>'],
    '<Relation>': [db],
    '<Attribute>':
        fields,
    # Types:
    '<Name>': ['<String>'],
    '<String>': ['<Char>', '<String><Char>'],
    '<Char>': list(string.ascii_lowercase),
    # '<Integer>': ['<Digit>', '-<Integer>', '<Integer><Digit>'],
    '<Integer>': ['<Digit>', '<Integer><Digit>'],  # Only positive numbers
    '<Digit>': [str(i) for i in range(10)],
    '<Email>': ['<String>@<String>.com', '<String>@<String>.org', '<String>@<String>.edu'],
}