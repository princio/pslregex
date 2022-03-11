import re, os
import pandas as pd

def sl(l, indent=4, c=' '):
    return (l+1)*indent*c + f'{l}#'

MAXLEVEL = 4


def get_branches(df, k):
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

    if df.shape[0] == 1:
        endpoint = df.iloc[0].to_dict()
        preword = endpoint['suffix'][l:] + '.'
        return {
                preword: {
                'suffix': endpoint['suffix'],
                'code': endpoint['code']
            }
        }

    amazonaws = False
    if (df.suffix.str.find('amazonaws') >= 0).sum() == df.shape[0]:
        amazonaws = True
        pass

    k=l+1
    stop = 1 + df.suffix.str.len().min()
    while k <= stop:
        branches = df.copy()
        prewords = df.suffix.str[l:k-1]

        if prewords.drop_duplicates().shape[0] > 1:
            raise AssertionError('Multiple prewords should be impossible')
            
        preword = prewords.drop_duplicates().iloc[0]

        branches['group'] = df.suffix.str[k-1:k]
        branches['n'] = 1

        branches = branches.groupby('group').agg({
            'n': 'sum',
            'suffix': lambda x: list([ xx[k:] for xx in x ]),
            'code': lambda x: list(x)
        })
        branches = branches.sort_values(by='n', ascending=False)
        branches = branches.reset_index()

        endpoint = branches[branches['group'] == '']

        if endpoint.shape[0] > 1:
            raise AssertionError('Multiple endpoints should be impossible.')
        
        if endpoint.shape[0] == 1:
            endpoint = endpoint.iloc[0].to_dict()

            if endpoint['n'] > 1:
                raise AssertionError('Endpoint should be unique.')

            branches = branches[branches['group'] != '']
            
            if branches.shape[0] == 1:
                nodes = {
                    '.': {
                        'suffix': df.loc[endpoint['code'][0], 'suffix'],
                        'code': endpoint['code'][0]
                    }
                }
                child_nodes = group_by_n_l(df[~(df.index == endpoint['code'][0])], k)
                for cpreword in child_nodes:
                    nodes[cpreword] = child_nodes[cpreword]
                return { preword: nodes }
            pass

        if branches.shape[0] == 1:
            k += 1
            continue
        
        b = 0
        while branches.shape[0] == b:


        break

    # This is not and endpoint
    
    nodes = {}

    new_branches = branches[branches['n'] > 1]

    for _, branch in new_branches.iterrows():
        nodes[branch['group']] = group_by_n_l(df.loc[branch['code']], k)
        pass

    df_endpoints = branches[branches['n'] == 1]
    for _, endpoint in df_endpoints.iterrows():
        nodes[endpoint['group'] + endpoint['suffix'][0]] = df.loc[endpoint['code'][0]].to_dict()
        pass
    
    if preword == '':
        return nodes
    else:
        preword += '.'
        return { preword: nodes }

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
