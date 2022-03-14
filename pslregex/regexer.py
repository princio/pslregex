import json
from numpy import r_
import pandas as pd
import json

def sl(l, indent=4, c=' '):
    return (l+1)*indent*c + f'{l}#'

MAXLEVEL = 4


def get_branches(df, k):
    branches = df.copy()

    branches['group'] = df.suffix.str[k-1:k]
    branches['n'] = 1

    branches = branches.groupby('group').agg({
        'n': 'sum',
        'suffix': lambda x: list([ xx[k:] for xx in x ]),
        'code': lambda x: list(x)
    })
    
    branches = branches.sort_values(by='n', ascending=False)
    
    return branches.reset_index()

def group_by_n_l(df, l):
    if l == 0:
        df.suffix = df.suffix + '.'

    if df.shape[0] == 1:
        endpoint = df.iloc[0].to_dict()
        preword = endpoint['suffix'][l:]
        return preword, {
                'suffix': endpoint['suffix'],
                'code': endpoint['code']
            }

    k=l+1
    stop = 1 + df.suffix.str.len().min()
    while k <= stop:
        prewords = df.suffix.str[l:k-1]

        if prewords.drop_duplicates().shape[0] > 1:
            raise AssertionError('Multiple prewords should be impossible')
        
        preword = prewords.drop_duplicates().iloc[0]

        branches = get_branches(df, k)

        if branches.shape[0] == 1:
            k += 1
            continue
        
        break

    is_node = False
    node = branches[branches['group'] == '']
    if node.shape[0] == 1:
        node = df.loc[node.iloc[0]['code'][0]].to_dict()
        is_node = True
        node = {
            'suffix': node['suffix'],
            'code': node['code']
        }
        branches = branches[branches['group'] != '']
        pass

    branches = branches.sort_values(by='group', ignore_index=True)

    branches['nn'] = branches.n // 5

    subgroups = branches.groupby('nn').agg({ 'group': lambda x: list(x), 'suffix': lambda x: list(x), 'code': lambda x: list(x) })

    nodes = {}
    for n, subgroup in subgroups.iterrows():
        subnodes = {}
        if len(subgroup['group']) == 1:
            subnodes = nodes
        else:
            tmp = '@' + ''.join(subgroup['group'])
            nodes[tmp] = {}
            subnodes = nodes[tmp]
            pass
        for i in range(len(subgroup['group'])):

            _group = subgroup['group'][i]
            _suffixes = subgroup['suffix'][i]
            _codes = subgroup['code'][i]

            if n == 1:
                subnodes[_group + _suffixes[0]] = df.loc[_codes[0]].to_dict()
                continue

            _pw, _ns = group_by_n_l(df.loc[_codes], k-1)
            subnodes[_pw] = {}
            for _n in _ns:
                subnodes[_pw][_n] = _ns[_n]
            pass
        pass
    
    if is_node:
        nodes[''] = node
        nodes = { n: nodes[n] for n in sorted(nodes.keys()) }
    
    return preword, nodes

def invertedSuffixLabels(df):
    df__ = pd.DataFrame(df.suffix.str.split('.').apply(lambda x: x[::-1]).to_list(), index=df.index).fillna('')
    df__['suffix'] = df['suffix']
    df__['code'] = df['code']
    df__['punycode'] = df['punycode']
    df__['type'] = df['type']
    df__['origin'] = df['origin']
    df__['section'] = df['section']
    return df__.sort_values(by=df__.columns.tolist()).copy()


def invertedSuffix(df_etld):
    sfx = df_etld.suffix.copy()
    sfx = sfx.apply(lambda s: '.'.join(s.split('.')[::-1])).to_frame()
    sfx['code'] = df_etld['code']
    return sfx.copy()

    
def hasLeafBranch(node):
    return '' in node and isLeaf(node[''])

def getLeafBranch(node):
    return node[''] if hasLeafBranch(node) else None

def isLeaf(node):
    return len(list(node.keys())) == 2 and 'suffix' in node and 'code' in node

def getLeaves(node):
    return [ (word, node[word]) for word in node if isLeaf(node[word]) and word != '' ]

def getBranches(node):
    return [ (word, node[word]) for word in node if not isLeaf(node[word]) ]

def getChildren(node):
    return [ (word, node[word]) for word in node ]

def nleaves(node, total=True):
    if not total:
        return sum([ 1 if isLeaf(child_node) else 0 for child_node in getChildren(node) ])
    
    if isLeaf(node):
        return 1
    nc = 0
    for n in node:
        nc += nleaves(node[n])
    return nc


def namedGroup(word, node):
    return word[:-2] + '(?P<{code}>\\.)'.format(code=node['code'], suffix=word)

def parseLeaf(word, node):
    word = word.replace('.', '\\.').replace('*', '[^\\.]+')
    return namedGroup(word, node)

def parseBegin(word, node):
    if isLeaf(node):
        word = parseLeaf(word, node)
    elif hasLeafBranch(node):
        leafbranch = getLeafBranch(node)
        word = parseLeaf(word, leafbranch)
    
    return word

def ind_(l):
    return  '\n' + '  ' * l


# leaf is a named capturing group
# branch is a non-capturing group that could start with a leaf

def parseNode(word, node, l):
    h = l

    ind0 = ind_(h)
    ind1 = ind_(h+1)
    ind2 = ind_(h+2)

    gl = ''
    if len(word) > 0 and word[0] == '@':
        tmp = word[1:] # remove @
        tmp = tmp if len(tmp) == 1 else f'[{tmp}]'
        return f'{ind0}(?={tmp})' + f'{ind1}(?:' + f'{ind1}|'.join([ parseNode(w, node[w], l+2) for w in node ]) + f'{ind0})'
    
    if isLeaf(node):
        return parseLeaf(word, node)

    branches = getBranches(node)
    leaves = getLeaves(node)

    nb = len(branches)
    nl = len(leaves)

    if nb == 0 and nl == 1 and not hasLeafBranch(node):
        raise AssertionError('If there are no branches, should be at least more than one leaf.')

    r_word = gl + parseBegin(word, node)

    r_leaves = '|'.join([ parseLeaf(leaf[0], leaf[1]) for leaf in leaves ])

    if r_leaves != '':
        r_leaves = f'{r_leaves}'

    r_branches = '|'.join([ parseNode(branch[0], branch[1], l+2) for branch in branches ])

    if l == -1:
        return f'^{r_branches}\n(?:[^\.]+)(?:\.[^\.]*)*$'

    if r_branches != '':
        r_branches = f'(?:{r_branches}'
        if hasLeafBranch(node):
            r_branches += f'{ind1}|)'
        else:
            r_branches += f'{ind1})'
    
    if r_leaves == '' and r_branches == '':
        return f'{ind0}{r_word}'

    if r_leaves == '' and r_branches != '':
        return f'{ind0}{r_word}{ind1}{r_branches}'

    if r_leaves != '' and r_branches == '':
        return f'{ind0}{r_word}{ind1}{r_leaves}'

    return f'{ind0}{r_word}{ind1}(?:{ind2}{r_leaves}{ind2}|{r_branches}{ind1})'




if __name__ == "__main__":

    _tld = 'com'

    with open(f'group.{_tld}.json', 'r') as f:
        nodes = json.load(f)

    regex = parseNode('', nodes, -1)

    with open(f'ff.{_tld}.txt', 'w') as f:
        f.write(regex)

    pass