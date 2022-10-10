import json
from numpy import r_
import pandas as pd
import json, numpy as np


def dicter(df, l):
    if df.shape[0] == 1:
        d = df.iloc[0].fillna('').to_dict()
        d = { f'@{k}': d[k] for k in d if not isinstance(k, int) and d[k] != '' }
        if l < 4 and df.iloc[0][l] != '':
            d = { df.iloc[0][l]: d }
    else:
        d = { k: dicter(df[df[l] == k], l+1) for k in df[l].drop_duplicates() }
        if l == 0:
            dd = {}
            for k in d:
                if k[0] not in dd:
                    dd[k[0]] = {}
                dd[k[0]][k] = d[k]
            d = dd

    return d

def match(dn):
    ds = []
    idn = '.'.join(dn.split('.')[::-1])
    labels = idn.split('.')

    def _d(d):
        d['@dn-suffix'] = '.'.join(labels[i+1:][::-1])
        return { k[1:]: d[k] for k in d }
        
    for i, l in enumerate(labels):
        try:
            d = d[l]
            if '' in d:
                ds.append(_d(d[''], i))
            elif '@code' in d:
                ds.append(_d(d, i))
                break
        except KeyError as e:
            if len(labels)-1 > i and '*' in d:
                ds.append(_d(d['*'], i))
            break
        pass
    return ds
    


if __name__ == "__main__":

    dicter_ = {}
    with open('dicter.com.json', 'r') as f:
        dicter_['com'] = json.load(f)
    with open('dicter.uk.json', 'r') as f:
        dicter_['uk'] = json.load(f)
    with open('dicter.all.json', 'r') as f:
        dicter_['all'] = json.load(f)

    dn = 'ciao.ciao.0emm.com'
    dn = 'ciao.issmarterthanyou.com'
    dn = 'ciao.compute-1.amazonaws.com'
    dn = 'ciao.compute-1.amazonaws.aaa'
    dn = 'ciao.co.uk'
    ds = []
    d = dicter_['all']
    idn = '.'.join(dn.split('.')[::-1])
    labels = idn.split('.')
    for i, l in enumerate(labels):
        try:
            d = d[l]
            if '' in d:
                ds.append(d[''])
            elif '@code' in d:
                ds.append(d)
                break
        except KeyError as e:
            if len(labels)-1 > i and '*' in d:
                ds.append(d['*'])
            break

    print(ds)

    pass