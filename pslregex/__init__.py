import pandas as pd
import time
import json
import os
import json

from pslregex.etld import ETLD


DIR = os.path.dirname(__file__)

class PSLdict:
    def __init__(self, dir=DIR, print_perf=True) -> None:
        self.etld = ETLD(dir)
        self.dicter = None
        pass

    def init(self, download=False, update=False):
        self.etld.init(download=download, update=update)
        
        dicter_path = os.path.join(DIR, 'dicter.json')
        if not update and os.path.exists(dicter_path):
            with open(dicter_path) as f:
                self.dicter = json.load(f)
        else:
            dfi = self.etld.iframe()
            self.dicter = self.__dicter(dfi, 0)
            with open(dicter_path, 'w') as f:
                json.dump(self.dicter, f)

        pass

    def __dicter(self, df, l):
        if df.shape[0] == 1:
            d = df.iloc[0].fillna('').to_dict()
            d = { f'@{k}': d[k] for k in d if not isinstance(k, int) and d[k] != '' }
            k = l
            keys = []
            while ((k) in df.columns and df[k].iloc[0] != ''):
                keys += [ df[k].iloc[0] ]
                k += 1
            for key in keys[::-1]:
                d = { key: d }
        else:
            d = { k: self.__dicter(df[df[l] == k], l+1) for k in df[l].drop_duplicates() }
            if l == 0:
                dd = {}
                for k in d:
                    if k[0] not in dd:
                        dd[k[0]] = {}
                    dd[k[0]][k] = d[k]
                d = dd

        return d

    def match(self, dn):
        ds = {
            'icann': None,
            'private': None
        }
        if dn is None or len(dn) == 0:
            return ds

        if dn[0] == '.' or dn[-1] == '.' or dn.find('..') >= 0 or len(dn) < 3:
            return ds

        dn = dn.lower()
        idn = '.'.join(dn.split('.')[::-1])
        if idn[0] not in self.dicter:
            return ds
        d = self.dicter[idn[0]]
        labels = idn.split('.')

        def _d(d, i):
            d['@dn-suffix'] = '.'.join(labels[len(labels):i:-1])
            return { k[1:]: d[k] for k in d }
            
        for i, l in enumerate(labels):
            suffix = d.get(l)
            if suffix is None:
                if len(labels)-1 > i:
                    suffix = d.get('*')
                    if suffix is not None:
                        ds[suffix['@isprivate']] = _d(suffix, i)
                    break
            elif '@code' in suffix:
                ds[suffix['@isprivate']] = _d(suffix, i)
                break
            else:
                suffix2 = suffix.get('')
                if suffix2 is not None:
                    ds[suffix2['@isprivate']] = _d(suffix2, i)
                d = suffix
                pass
            pass

        return ds
    
    pass # end of PSLdict

def init():
    psl = PSLdict()
    psl.init(download=True, update=True)
    pass

if __name__ == '__main__':
    psl = PSLdict()

    psl.init(download=False, update=True)

    dn = 'www.example.com'
    dn = 'ciao.issmarterthanyou.com'
    dn = 'ciao.asterisk.compute-1.amazonaws.com'

    df = psl.etld.frame
    a = time.time()
    single = psl.match(dn)
    a = time.time() - a
    print(a)
    print(single)

    df = psl.etld.frame

    pass