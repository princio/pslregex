import keyword
import pandas as pd
import time
import json
import os, re
import numpy as np

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from pslregex.regexer import getRegexes, invertedSuffixLabels
from pslregex.etld import ETLD

from pslregex.etld import codes, inv_codes

DIR = os.path.dirname(__file__)

class RegexEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) == re.Pattern:
            return obj.pattern
        return json.JSONEncoder.default(self, obj)


class PSLRegex:
    def __init__(self, dir=DIR, print_perf=True) -> None:
        self.etld = ETLD(dir)
        self.regexes = None
        self.ukwIndex = None
        self.print_perf = print_perf
        pass

    def init(self, download=False, update=False):
        self.etld.init(download=download, update=update)
        
        if not update and os.path.exists(os.path.join(DIR, 'regex.json')):
            with open(os.path.join(DIR, 'regex.json')) as f:
                jregexes = json.load(f)
                self.regexes = { tld: re.compile(jregexes[tld]) for tld in jregexes }
        else:
            self.regexes = getRegexes(self.etld.frame)
            with open(os.path.join(DIR, 'regex.json'), 'w') as f:
                json.dump(self.regexes, f, cls=RegexEncoder)

        # self.etld['l'] = self.etld.frame.suffix.str.count('\.')

        ukwRow = [ '--' ] * self.etld.frame.shape[1]
        ukwRow[0] = self.etld.frame.shape[0]
        ukwRow = [
            'ukw', 'ukw', '--', '--', '--', '--', '--', False, False
        ]
        self.ukwIndex = self.etld.frame.shape[0]
        self.etld.frame.loc[self.etld.frame.shape[0]] = ukwRow

        noneRow = [ '--' ] * self.etld.frame.shape[1]
        noneRow[0] = self.etld.frame.shape[0]
        noneRow = [
            'none', 'none', '--', '--', '--', '--', '--', False, False
        ]
        self.noneIndex = self.etld.frame.shape[0]
        self.etld.frame.loc[self.etld.frame.shape[0]] = noneRow


        self.np = self.etld.frame.to_numpy()
        self.list = self.etld.frame.values.tolist()

        pass

    def match(self, s, onlytld=False, not_private=False):
        if s[0] not in self.regexes:
            return [ self.ukwIndex, self.ukwIndex ]

        gd = self.regexes[s[0]].match(s[1]).groupdict()

        icann_indexes = [ self.noneIndex ] + [ int(code[1:6]) for code in gd if code[0] != 'p' and gd[code] is not None ]
        pvt_indexes = [ self.noneIndex ] + [ int(code[1:6]) for code in gd if code[0] == 'p' and gd[code] is not None ]

        if len(icann_indexes) == 1 and len(pvt_indexes) == 1:
            return [ self.ukwIndex, self.ukwIndex ]

        return [ icann_indexes[-1], pvt_indexes[-1] ] # return the longest on


    def single(self, dn, onlytld=False, not_private=False):

        dn = dn.split('.')[::-1]
        m = self.match((dn[0], '.'.join(dn)), onlytld=onlytld, not_private=not_private)
        suffix = [ self.list[mm] for mm in m ]

        # # df = self.etld.frame.to_numpy()
        # # start = time.time()
        # a = time.time()
        # dn = dn.split('.')[::-1]
        # m = self.match((dn[0], '.'.join(dn)), onlytld=onlytld, not_private=not_private)
        # a = time.time() - a

        # print(a)
        
        
        # a = time.time()
        # a = time.time() - a
        # print(a)
        # # end = time.time() - start

        # # if self.print_perf:
        # #     print(f'Found 1 solution/s in {end} sec')
        
        return suffix

    def multi(self, dnSeries, onlytld=False, not_private=False, compact=True):
        start = time.time()
        dnRevertedSeries = dnSeries.str.split('.').apply(lambda s: [ s[-1] , '.'.join(s[::-1]) ])

        indexes = dnRevertedSeries.apply(self.match, onlytld=onlytld, not_private=not_private)
        indexes = np.array(indexes.values.tolist())
        icann = indexes[:,0]
        pvt = indexes[:,0]

        cols = ['suffix', 'type', 'section'] if compact else self.etld.frame.colums
            
        df = {
            'icann': self.etld.frame[cols].iloc[icann],
            'pvt': self.etld.frame[cols].iloc[pvt]
        }

        for a in df:
            df[a].index = df[a].reset_index().index

        suffixes = pd.concat(df, axis=1)

        end = time.time() - start

        if self.print_perf:
            print(f'Multi {dnSeries.shape[0]} in {end} sec ({end/dnSeries.shape[0]} sec/dn)')
        
        return suffixes

    def merge(self, frame, onlytld=True, not_private=False, compact=True):
        start = time.time()

        suffixes = self.multi(frame.dn, onlytld=onlytld, not_private=not_private)

        suffixes.index = frame.index

        frame.columns = pd.MultiIndex.from_tuples([ ('dn', col) for col in frame.columns ])

        frame_merged = pd.concat([ frame, suffixes ], axis=1)
        end = time.time() - start

        if self.print_perf:
            print(f'Merged {frame.shape[0]} in {end} sec ({end/frame.shape[0]} sec/dn)')
        
        return frame_merged
        
    pass

if __name__ == '__main__':
    psl = PSLRegex()

    psl.init(download=False, update=False)

    df = psl.etld.frame
    a = time.time()
    single = psl.single('www.example.co.')
    a = time.time() - a
    print(a)
    print(single)

    df = psl.etld.frame
    df = df[(df.tld == 'com')]

    dfinv = invertedSuffixLabels(df)

    regexes = getRegexes(df[(dfinv[1].str[0] == '') | (dfinv[1].str[0] == '0') | (dfinv[1].str[0] == 'e')])

    print(regexes['com'].pattern)

    # print('\n', psl.regexes['uk'].pattern, '\n')

    # datasetFrame = pd.read_csv('/home/princio/Desktop/malware_detection/nn/nn/dataset_training.csv').iloc[0:1_000]
    # datasetFrame['tld'] = datasetFrame.dn.apply(lambda dn: dn[1 + dn.rfind('.'):])

    # frame = psl.merge(datasetFrame)

    # print(single)
    # print(frame)

    pass
