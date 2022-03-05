import re, os
import pandas as pd


def sl(l, indent=4, c=' '):
    return (l+1)*indent*c + f'{l}#'
class Node:
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
        node = Node(label, code=code, deep=childDeep, singleLetter=singleLetter, parent=self, dn=dn)
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
        if self.singleLetter:
            return 'FL/' + self.label[0]
        else:
            psingleLetter = int(self.parent.singleLetter) if self.parent else ''
            return f'{self.label}' + (f'[{self.code}]' if self.isLeaf() else '')
    def __repr__(self):
        return self.__str__()

    def regex(self, indent='  '):
        groups = []
        
        if self._debug:
            lindent = '\n' + self.level() * indent
            lindent2 = '\n' + (1 + self.level()) * indent
        else:
            lindent = ''
            lindent2 = ''
        
        for child in self.children:
            groups.append(child.regex(indent=indent))
        
        if self.parent is None:
            return '|'.join(groups)
        
        label = self.label[1:] if self.parent.singleLetter else self.label

        label = label.replace('*', '.+')
        
        if self.isLeaf():
            label = f'(?P<{self.code}>{label}\\.)'
        
        if len(groups) == 0:
            return label
        
        bs = "" if self.singleLetter else "\\."
        
        uncaptured = f'{label}{bs}'
        
        child_regex = f'|'.join(groups) 
        
        sep = ''
        if child_regex != '':
            sep = '|'
        
        regex = f'{lindent}(?:{uncaptured}(?:{lindent2}{child_regex}{sep}{lindent2}))'

        if self.deep == 0:
            regex = '^' + regex + '(?:.+(?:.*)*)$'
        
        return regex
    
    pass

def fillTree(sfxOr, l, parent):
    subcols = list(range(l+1, len(sfxOr.columns)-1)) # max number of labels is columns less 'index' column
    subcols.append('code')
    currentLabelUniques = sfxOr.drop_duplicates(subset=l)[l]
    singleLetters = currentLabelUniques.str[0].value_counts(sort=False)
    flNodes = {}
    for singleLetter, c in singleLetters.iteritems():
        flNodes[singleLetter] = parent.add(singleLetter, singleLetter=True) if c > 1 else parent
    for singleLetter in flNodes:
        sfx = sfxOr[sfxOr[l].str[0] == singleLetter]
        if l == 4:
            s_leaves = sfx
            s_branches = pd.DataFrame([])
        else:
            s_leaves = sfx[sfx[l+1] == '']
            s_branches = sfx[sfx[l+1] != ''][l].drop_duplicates()
        leaves = {}
        for _, leaf in s_leaves.iterrows():
            leaves[leaf[l]] = flNodes[leaf[l][0]].add(leaf[l], code=leaf['code'], dn='.'.join(leaf.values[:l+1]))
        for loc, branch in s_branches.iteritems():
            if branch not in leaves:
                node = flNodes[branch[0]].add(branch)
            else:
                node = leaves[branch]
            if (sfx[l+1] != '').sum() > 0:
                fillTree(sfx[(sfx[l] == branch) & (sfx[l+1] != '')], l+1, node)
        pass

def invertedSuffixLabels(df_etld):
    sfx = df_etld.suffix.copy()
    # sfx = df_etld.suffix.str.replace(r'*.', '', regex=False).copy()
    maxLabels_suffix = sfx.str.count('\.').max()
    sfx = sfx.apply(lambda s: ('@@.'*(maxLabels_suffix - s.count('.'))) + s).str.split('.', expand=True)
    sfx = sfx[sfx.columns[::-1]]
    sfx = sfx.replace('@@', '')
    sfx = sfx.rename(columns={ 4:0, 3:1, 2:2, 1:3, 0:4})
    sfx['code'] = df_etld['code']
    return sfx.copy()

def getRegexes(df_etld):
    sfx = invertedSuffixLabels(df_etld)
    regexes = {}
    tlds = sfx[0].drop_duplicates()
    for tld in tlds:
        tree = Node('root', deep=-1)
        fillTree(sfx[sfx[0] == tld], 0, tree)
        tree.compact()
        if os.environ.get('DEBUG'):
            regexes[tld] = re.compile(tree.regex(), re.VERBOSE)
        else:
            regexes[tld] = re.compile(tree.regex())
    return regexes



