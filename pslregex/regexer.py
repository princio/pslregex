import re, os
import pandas as pd

def sl(l, indent=4, c=' '):
    return (l+1)*indent*c + f'{l}#'

MAXLEVEL = 4

class TreeNode:
    def __init__(self, label, code=None, deep=0, singleLetter=False, parent=None, dn=None):
        self.parent = parent
        self.label = label
        self.dn = dn
        self.code = code
        self.children = []
        self.deep = deep
        self.singleLetter = singleLetter
        self._debug = os.environ.get('DEBUG')
        pass
    
    def level(self):
        i = 0 if self.parent is None else self.parent.level() + 1 + self.singleLetter
        return i
    
    def add(self, label, code=None, singleLetter=False, dn=None):
        childDeep = self.deep+1 if not self.singleLetter else self.deep
        node = TreeNode(label, code=code, deep=childDeep, singleLetter=singleLetter, parent=self, dn=dn)
        self.children.append(node)
        return node

    
    def addChild(self, node):
        node.parent = self
        self.children.append(node)
        return node
    
    def leaves(self):
        _leafs = [self] if self.code is not None else []
        for child in self.children:
            _leafs += child.leaves()
        return _leafs
    
    def allLeaf(self):
        return all([child.isLeaf() for child in self.children])
    
    def isLeaf(self):
        return self.code is not None
    
    def branch(self):
        if self.parent is None:
            return [ self ]
        return [ self ] + self.parent.branch()
    
    def __getitem__(self, key):
        return self.children[key]
    
    def compact(self):
        if self.parent is not None:
            while not self.singleLetter and len(self.children) == 1 and not self.isLeaf():
                self.label = self.label + '\\.' + self[0].label
                self.dn = self[0].dn
                self.code = self[0].code
                self.singleLetter = self[0].singleLetter
                self.children = self[0].children
        for child in self.children:
            child.compact()
    
    def _print(self):
        print((self.level() * '  ') + str(self))
        for child in self.children:
            child._print()

    def print2(self):
        print(f'{sl(self.deep)} {self.__str__()}')
        for child in self.children:
            child.print2()
    
    def __str__(self):
            return f'{self.label}' + (f'[{self.code}]')
    
    def __repr__(self):
        return self.__str__()

    def regex(self):
        regex_label = self.label.replace('*', '[^\\.]+')
        regex_label += '\\.'
        regex_label = regex_label if self.code is None else f'(?P<{self.code}>{regex_label})'
        if len(self.children) == 0:
            return regex_label
        
        fls = [ child.label[0] for child in self.children ]
        fls = { fl: fls.count(fl) for fl in fls }

        groups_per_letter = { fl: [] for fl in fls }
        for child in self.children:
            groups_per_letter[child.label[0]].append(child.regex())
        
        children_regexes = []
        for fl in groups_per_letter:
            if len(groups_per_letter[fl]) > 1:
                child_regex = f'(?={fl})(?:' + '|'.join(groups_per_letter[fl]) + ')'
            else:
                child_regex = '|'.join(groups_per_letter[fl])
            children_regexes.append(child_regex)
        
        if len(children_regexes) > 0:
            tmp = '' if self.code is None else f'|'
            regex = f'{regex_label}(?:{"|".join(children_regexes)}{tmp})'
        else:
            regex = regex_label
        
        # TODO: Check regex having one single node (i.e. the one with unusal tld like '.post')
        if self.deep == 0:
            regex = '^' + regex + '(?:[^\.]+)(?:\.[^\.]*)*$'
        
        return regex
    
    pass


def __getNodes(tree, l):
    if tree.shape[0] == 0:
        return []
    
    treenodes = []
    for node in tree[l].drop_duplicates():

        branch = tree[(tree[l] == node)]

        leaf = branch[branch[l+1] == '']
        leafCode = None
        if leaf.shape[0] == 1:
            leafCode = leaf.iloc[0]['code']
        elif leaf.shape[0] > 1:
            print(leaf)
            raise AssertionError('Multiple leaves in list.')

        treenode = TreeNode(node, code=leafCode, deep=l)

        childnodes = None
        if l+1 < MAXLEVEL:
            childnodes = __getNodes(branch[branch[l+1] != ''], l+1)
            for childnode in childnodes:
                treenode.addChild(childnode)
        
        treenodes.append(treenode)

        pass

    return treenodes


def invertedSuffixLabels(df_etld):
    sfx = df_etld.suffix.copy()
    # sfx = df_etld.suffix.str.replace(r'*.', '', regex=False).copy()
    maxLabels_suffix = sfx.str.count('\.').max()
    sfx = sfx.apply(lambda s: ('@@.'*(maxLabels_suffix - s.count('.'))) + s).str.split('.', expand=True)
    sfx = sfx[sfx.columns[::-1]]
    sfx = sfx.replace('@@', '')
    for col in range(len(sfx.columns), MAXLEVEL+1):
        sfx[col] = ''
    sfx.columns = pd.Index(list(range((MAXLEVEL+1))))
    sfx['code'] = df_etld['code']
    return sfx.copy()


def getRegexes(df_etld):
    sfx = invertedSuffixLabels(df_etld)
    regexes = {}
    tlds = sfx[0].drop_duplicates()
    for tld in tlds:
        nodes = __getNodes(sfx[sfx[0] == tld], 0)
        if os.environ.get('DEBUG'):
            regexes[tld] = re.compile(nodes[0].regex(), re.VERBOSE)
        else:
            regexes[tld] = re.compile(nodes[0].regex())
    return regexes

