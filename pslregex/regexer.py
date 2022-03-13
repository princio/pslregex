import json
from numpy import r_
import pandas as pd

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

        # endpoint = branches[branches['group'] == '']

        # if endpoint.shape[0] > 1:
        #     raise AssertionError('Multiple endpoints should be impossible.')
        
        # if endpoint.shape[0] == 1:
        #     print(endpoint)
        #     endpoint = endpoint.iloc[0].to_dict()

        #     if endpoint['n'] > 1:
        #         raise AssertionError('Endpoint should be unique.')

        #     branches = branches[branches['group'] != '']
            
        #     nodes = {
        #         '': {
        #             'suffix': df.loc[endpoint['code'][0], 'suffix'],
        #             'code': endpoint['code'][0]
        #         }
        #     }
        #     child_nodes = group_by_n_l(df[~(df.index == endpoint['code'][0])], k-1)
        #     for cpreword in child_nodes:
        #         nodes[cpreword] = child_nodes[cpreword]
        #     return { preword: nodes }

        if branches.shape[0] == 1:
            k += 1
            continue
        
        # b = branches.shape[0]
        # j = k + 1
        # if amazonaws:
        #     while branches.shape[0] == b:
        #         b2 = get_branches(df, j)
        #         b = b2.shape[0]
        #         pass

        break

    # This is not and endpoint
    
    nodes = {}

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

    df_endpoints = branches[branches['n'] == 1]
    for _, endpoint in df_endpoints.iterrows():
        nodes[endpoint['group'] + endpoint['suffix'][0]] = df.loc[endpoint['code'][0]].to_dict()
        pass

    branches = branches[branches['n'] > 1]
    for _, branch in branches.iterrows():
        _pw, _ns = group_by_n_l(df.loc[branch['code']], k-1)
        nodes[_pw] = {}
        for _n in _ns:
            nodes[_pw][_n] = _ns[_n]
        pass

    
    if is_node:
        nodes[''] = node
        nodes = { n: nodes[n] for n in sorted(nodes.keys()) }
    
    return preword, nodes

def invertedSuffixLabels(df_etld):
    sfx = df_etld.suffix.copy()
    maxLabels_suffix = sfx.str.count('\.').max()
    sfx = sfx.apply(lambda s: ('@@.'*(maxLabels_suffix - s.count('.'))) + s).str.split('.', expand=True)
    sfx = sfx[sfx.columns[::-1]]
    sfx = sfx.replace('@@', '')
    for col in range(len(sfx.columns), MAXLEVEL+1):
        sfx[col] = ''
    sfx.columns = pd.Index(list(range((MAXLEVEL+1))))
    sfx['code'] = df_etld['code']
    return sfx.copy()


def invertedSuffix(df_etld):
    sfx = df_etld.suffix.copy()
    sfx = sfx.apply(lambda s: '.'.join(s.split('.')[::-1])).to_frame()
    sfx['code'] = df_etld['code']
    return sfx.copy()

if __name__ == "__main__":
    import json

    with open('group.uk.json', 'r') as f:
        nodes = json.load(f)

    
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


    def convertWord(word):
        return word.replace('.', '\\.').replace('*', '[^\\.]+')


    def parseBegin(word, node):
        r = convertWord(word)

        if isLeaf(node):
            r = '(?P<{code}>{suffix})'.format(code=node['code'], suffix=r)
        
        elif hasLeafBranch(node):
            leafbranch = getLeafBranch(node)
            r = '(?P<{code}>{suffix})'.format(code=leafbranch['code'], suffix=r)
        
        return r


    def parseLeaf(word, node):
        return '(?P<{code}>{word})'.format(code=node['code'], word=convertWord(word))

    def ind_(l):
        return  '\n' + '    ' * l

    
    # leaf is a named capturing group
    # branch is a non-capturing group that could start with a leaf

    def parseNode(word, node, l):
        s = ''
        h = l*3

        ind1 = ind_(h+1)
        ind2 = ind_(h+2)
        ind3 = ind_(h+3)

        branches = getBranches(node)
        leaves = getLeaves(node)

        nb = len(branches)
        nl = len(leaves)

        if nb == 0 and nl == 1 and not hasLeafBranch(node):
            raise AssertionError('If there are no branches, should be at least more than one leaf.')

        r_word = parseBegin(word, node)

        if hasLeafBranch(node):
            print(node['']['code'] + '\t' + node['']['suffix'])

        print('\n'.join([ leaf[1]['code'] + '\t' + leaf[1]['suffix'] for leaf in leaves ]))

        r_leaves = '|'.join([ parseLeaf(leaf[0], leaf[1]) for leaf in leaves ])

        if r_leaves != '':
            r_leaves = f'{r_leaves}'

        r_branches = '|'.join([ parseNode(branch[0], branch[1], l+1) for branch in branches ])

        if l == -1:
            return f'^\n{r_branches}\n(?:[^\.]+)(?:\.[^\.]*)*$'

        if r_branches != '':
            r_branches = f'(?:{ind3}{r_branches}'
            if hasLeafBranch(node):
                r_branches += f'{ind2}|)'
            else:
                r_branches += f'{ind2})'
        
        if r_leaves == '' and r_branches == '':
            return r_word

        if r_leaves == '' and r_branches != '':
            return f'{r_word}{ind1}{r_branches}'

        if r_leaves != '' and r_branches == '':
            return f'{r_word}{ind1}{r_leaves}'

        return f'{r_word}(?:{ind2}{r_leaves}{ind2}|{r_branches}{ind1})'
        
    regex = parseNode('', nodes, -1)

    with open('ff.txt', 'w') as f:
        f.write(regex)

    pass