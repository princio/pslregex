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
            if l < 4 and df.iloc[0][l] != '':
                d = { df.iloc[0][l]: d }
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
        # b = time.time()
        idn = '.'.join(dn.split('.')[::-1])
        d = self.dicter[idn[0]]
        labels = idn.split('.')
        # print('58', time.time() - b)

        def _d(d, i):
            d['@dn-suffix'] = '.'.join(labels[len(labels):i:-1])
            return { k[1:]: d[k] for k in d }
            
        for i, l in enumerate(labels):
            # b = time.time()
            suffix = d.get(l)
            if suffix is None:
                if len(labels)-1 > i:
                    suffix = d.get('*')
                    if suffix is not None:
                        ds[suffix['@isprivate']] = _d(suffix, i)
                    # print('78', time.time() - b)
                    break
            elif '@code' in suffix:
                ds[suffix['@isprivate']] = _d(suffix, i)
                # print('73', time.time() - b)
                break
            else:
                suffix2 = suffix.get('')
                if suffix2 is not None:
                    ds[suffix2['@isprivate']] = _d(suffix2, i)
                # print('70', time.time() - b)
                d = suffix
                pass
            pass

        # b = time.time()
       # a =  [ _d(d[0], d[1]) for d in ds if d[0] is not None ]
        # print('84', time.time() - b)

        return ds
    
    # end of PSLdict
    pass

if __name__ == '__main__':
    psl = PSLdict()

    psl.init(download=False, update=False)

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