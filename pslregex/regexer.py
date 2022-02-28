import re, os
import pandas as pd

class Node:
    def __init__(self, label, deep=0, index=None, fl=False, parent=None, dn=None):
        self.parent = parent
        self.label = label
        self.index = index
        self.dn = dn
        self.children = []
        self.deep = deep
        self.fl = fl
        self._debug = os.environ.get('DEBUG')
        pass
    
    def level(self):
        i = 0 if self.parent is None else self.parent.level() + 1 + self.fl
        return i
    
    def add(self, label, index=None, fl=False, dn=None):
        childDeep = self.deep+1 if not self.fl else self.deep
        node = Node(label, index=index, deep=childDeep, fl=fl, parent=self, dn=dn)
        self.children.append(node)
        return node
    
    def leaves(self):
        _leafs = [self] if self.index is not None else []
        for child in self.children:
            _leafs += child.leaves()
        return _leafs
    
    def allLeaf(self):
        return all([child.isLeaf() for child in self.children])
    
    def isLeaf(self):
        return self.index is not None
    
    def branch(self):
        if self.parent is None:
            return [ self ]
        return [ self ] + self.parent.branch()
    
    def __getitem__(self, key):
        return self.children[key]
    
    def compact(self):
        if self.parent is not None:
            while not self.fl and len(self.children) == 1 and not self.isLeaf():
                self.label = self.label + '.' + self[0].label
                self.index = self[0].index
                self.dn = self[0].dn
                self.children = self[0].children
        for child in self.children:
            child.compact()
    
    def _print(self):
        print((self.level() * '  ') + str(self))
        for child in self.children:
            child._print()
    
    def __str__(self):
        if self.fl:
            return 'FL/' + self.label[0]
        else:
            pfl = int(self.parent.fl) if self.parent else ''
            return f'{self.label}#{pfl}' + f'[{self.dn}]'
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
        
        label = self.label[1:] if self.parent.fl else self.label
        
        leaf = f'(?P<l{self.index}>{label})' if self.isLeaf() else ''
        
        if len(groups) == 0:
            return leaf
        
        bs = "" if self.fl else "\\."
        
        uncaptured = f'{label}{bs}'
        
        child_regex = f'|'.join(groups) 
        
        sep = ''
        if child_regex != '' and leaf != '':
            sep = '|'
        
        return f'{lindent}({uncaptured}({lindent2}{child_regex}{lindent2}){sep}{leaf})'
    
    pass

def fillTree(sfxOr, l, parent):
    subcols = list(range(l+1, len(sfxOr.columns)-1)) # max number of labels is columns less 'index' column
    subcols.append('id')
    currentLabelUniques = sfxOr.drop_duplicates(subset=l)[l]
    firstLetters = currentLabelUniques.str[0].value_counts(sort=False)
    flNodes = {}
    for fl, c in firstLetters.iteritems():
        flNodes[fl] = parent.add(fl, fl=True) if c > 1 else parent
    for fl in flNodes:
        sfx = sfxOr[sfxOr[l].str[0] == fl]
        if l == 4:
            s_leaves = sfx
            s_branches = pd.DataFrame([])
        else:
            s_leaves = sfx[sfx[l+1] == '']
            s_branches = sfx[sfx[l+1] != ''][l].drop_duplicates()
        leaves = {}
        for _, leaf in s_leaves.iterrows():
            leaves[leaf[l]] = flNodes[leaf[l][0]].add(leaf[l], index=leaf['id'], dn='.'.join(leaf.values[:l+1]))
        for loc, branch in s_branches.iteritems():
            if branch not in leaves:
                node = flNodes[branch[0]].add(branch)
            else:
                node = leaves[branch]
            if (sfx[l+1] != '').sum() > 0:
                fillTree(sfx[(sfx[l] == branch) & (sfx[l+1] != '')], l+1, node)
        pass

def invertedSuffixLabels(df_etld):
    sfx = df_etld.suffix.str.replace(r'*.', '', regex=False).copy()
    maxLabels_suffix = sfx.str.count('\.').max()
    sfx = sfx.apply(lambda s: ('@@.'*(maxLabels_suffix - s.count('.'))) + s).str.split('.', expand=True)
    sfx = sfx[sfx.columns[::-1]]
    sfx = sfx.replace('@@', '')
    sfx = sfx.rename(columns={ 4:0, 3:1, 2:2, 1:3, 0:4})
    sfx['id'] = df_etld.reset_index()['index']
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

