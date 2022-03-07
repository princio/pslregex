import re, os
from typing import Set
import pandas as pd
from pslregex import PSLRegex
import pslregex.regexer as regexer
from pathlib import Path

dir = Path(__file__).parent

def __test_asterisk(psl):

    print()
    print(psl.regexes['com'].pattern)
    print()

    s = psl.single('bibo.ciao.compute.amazonaws.com')
    print()
    print(s)

    pass


maxLevel = 4

def sl(l, indent=8, c=' '):
    return (l+1)*indent*c + f'#{l})\t'


def __regex(self, firts_letter=False):
    print('firts_letter', firts_letter, self)
    fls = [ child.label[0] for child in self.children ]
    fls = { fl: fls.count(fl) for fl in fls }
    print('fl_count', len(fls))

    groups = { fl: [] for fl in fls }
    for child in self.children:
        groups[child.label[0]].append(__regex(child))
    
    reg_groups = []
    for fl in groups:
        if len(groups[fl]) > 1:
            reg = f'(?={fl})(?:' + '|'.join(groups[fl]) + ')'
        else:
            reg = '|'.join(groups[fl])
        reg = '(?:' + reg + ')'
        reg_groups.append(reg)
    
    regex_groups ='|'.join(reg_groups)
    if len(groups) > 1:
        regex_groups = f'(?:{regex_groups})'
    
    regex_label = self.label.replace('*', '[^\\.]+')
    if self.code is None:
        regex_label += '\\.'
    else:
        regex_label = f'(?P<{self.code}>{regex_label}\\.)'
    

    regex = f'{regex_label}{regex_groups}'
    
    if self.deep == 0:
        regex = '^' + regex + '(?:[^\.]+)(?:\.[^\.]*)*$'
    
    print(f'{sl(self.deep)} {regex}')

    return regex

def __getNodes(tree, l):

    branches = tree[tree[l] != '']

    if branches.shape[0] == 0:
        return []
    
    branches = branches.drop_duplicates(subset=l)

    nodes = []
    for _, branch_node in branches.iterrows():

        branch = tree[tree[l] == branch_node[l]]

        leaf = branch[(tree[l+1] == '')]
        leafCode = None
        if leaf.shape[0] == 1:
            leafCode = leaf.iloc[0]['code']
        elif leaf.shape[0] > 1:
            raise AssertionError('Multiple leaves in list.')

        node = regexer.TreeNode(branch_node[l], code=leafCode, deep=l)

        childnodes = None
        if l+1 < maxLevel:
            childnodes = __getNodes(branch, l+1)
            for childnode in childnodes:
                node.addChild(childnode)
        
        nodes.append(node)

        pass

    return nodes

if __name__ == '__main__':
    psl = PSLRegex()
    psl.init(download=False, update=False)

    # regex = regexer.getRegexes(df_etld=psl.etld.frame[(psl.etld.frame.suffix.str[-5:] == 'co.uk')])
    regex = regexer.getRegexes(df_etld=psl.etld.frame)

    print(regex['uk'].pattern)
    
    # __test_asterisk()

    # sfx = regexer.invertedSuffixLabels(psl.etld.frame).iloc[:-2] # remove ukw and none

    # nodes = __getNodes(sfx[sfx[0] == 'com'], 0)

    # nodes[0].print2()

    # regex = __regex(nodes[0])
    print()
    print(regex)
    print()