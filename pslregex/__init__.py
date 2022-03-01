import keyword
import pandas as pd
import time
import json
import os, re

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from pslregex.regexer import getRegexes
from pslregex.etld import getETLDframe

from pslregex.etld import codes, inv_codes

DIR = os.path.dirname(__file__)

class RegexEncoder(json.JSONEncoder):
    def default(self, obj):
        if type(obj) == re.Pattern:
            return obj.pattern
        return json.JSONEncoder.default(self, obj)

def init():
    if os.path.exists(os.path.join(DIR, 'etld.csv')):
        df = pd.read_csv(os.path.join(DIR, 'etld.csv'), index_col=0)
    else:
        df = getETLDframe()
        df.to_csv(os.path.join(DIR, 'etld.csv'))
    
    if os.path.exists(os.path.join(DIR, 'regex.json')):
        with open(os.path.join(DIR, 'regex.json')) as f:
            jregexes = json.load(f)
            regexes = { tld: re.compile(jregexes[tld]) for tld in jregexes }
    else:
        regexes = getRegexes(df)
        with open(os.path.join(DIR, 'regex.json'), 'w') as f:
            json.dump(regexes, f, cls=RegexEncoder)

    return df, regexes


def update():
    df = getETLDframe()
    df.to_csv(os.path.join(DIR, 'etld.csv'))
    regexes = getRegexes(df)
    with open(os.path.join(DIR, 'regex.json'), 'w') as f:
        json.dump(regexes, f, cls=RegexEncoder)
    pass


class PSLRegex():
    def __init__(self, print_perf=True) -> None:
        self.etldFrame = None
        self.regexes = None
        self.ukwIndex = None
        self.print_perf = print_perf
        pass

    def init(self):
        tmp = init()
        self.etldFrame = tmp[0]
        self.regexes = tmp[1]

        self.etldFrame['l'] = self.etldFrame.suffix.str.count('\.')

        ukwRow = [ '--' ] * self.etldFrame.shape[1]
        ukwRow[0] = self.etldFrame.shape[0]
        ukwRow[-2] = 'ukw'
        ukwRow[-1] = 0
        self.ukwIndex = self.etldFrame.shape[0]
        self.etldFrame.loc[self.etldFrame.shape[0]] = ukwRow

        pass

    def match(self, s, onlytld=False, not_private=False):
        if s[0] not in self.regexes:
            return self.ukwIndex
        gd = self.regexes[s[0]].match(s[1]).groupdict()

        if not_private:
            indexes = [ int(code[1:6]) for code in gd if gd[code] is not None and code[-3:-1] != 'pd' ]
        else:
            indexes = [ int(code[1:6]) for code in gd if gd[code] is not None ]

        if onlytld:
            return indexes[0]

        return indexes[-1] # return the longest one


    def single(self, dn, onlytld=False, not_private=False):
        start = time.time()

        dn = dn.split('.')[::-1]
        m = self.match((dn[0], '.'.join(dn)), onlytld=onlytld, not_private=not_private)
        suffix = self.etldFrame.iloc[m]
        end = time.time() - start

        if self.print_perf:
            print(f'Found 1 solution/s in {end} sec')
        return suffix

    def multi(self, dnSeries, onlytld=False, not_private=False, compact=True):
        start = time.time()
        dnRevertedSeries = dnSeries.str.split('.').apply(lambda s: [ s[-1] , '.'.join(s[::-1]) ])

        indexes = dnRevertedSeries.apply(self.match, onlytld=onlytld, not_private=not_private)
        if compact:
            suffixes = self.etldFrame[['suffix', 'type', 'suffix type', 'code', 'l']].iloc[indexes]
        else:
            suffixes = self.etldFrame.iloc[indexes]
        end = time.time() - start

        if self.print_perf:
            print(f'Multi {dnSeries.shape[0]} in {end} sec ({end/dnSeries.shape[0]} sec/dn)')
        
        return suffixes

    def merge(self, frame, onlytld=True, not_private=False, compact=True):
        start = time.time()
        dnRevertedSeries = frame.dn.str.split('.').apply(lambda s: [ s[-1] , '.'.join(s[::-1]) ])

        indexes = dnRevertedSeries.apply(self.match, onlytld=onlytld, not_private=not_private)

        if compact:
            suffixes = self.etldFrame[['suffix', 'type', 'suffix type', 'code', 'l']].iloc[indexes]
        else:
            suffixes = self.etldFrame.iloc[indexes]

        suffixes.index = frame.index
        frame_merged = pd.concat([ frame, suffixes ], axis=1).sort_values(by='l')
        end = time.time() - start

        if self.print_perf:
            print(f'Merged {frame.shape[0]} in {end} sec ({end/frame.shape[0]} sec/dn)')
        
        return frame_merged

    
    pass

def test():
    psl = PSLRegex()

    psl.init()

    single = psl.single('google.co.uk')

    datasetFrame = pd.read_csv('/home/princio/Desktop/malware_detection/nn/nn/dataset_training.csv').iloc[0:1_000]
    datasetFrame['tld'] = datasetFrame.dn.apply(lambda dn: dn[1 + dn.rfind('.'):])

    frame = psl.merge(datasetFrame)

    print(single)
    # print(frame.values)
    # print(pd.DataFrame.from_dict(single, orient='index').T)
    print(pd.DataFrame.from_records(frame.values).fillna(''))#.to_csv('./tmp.csv'))

    pass
