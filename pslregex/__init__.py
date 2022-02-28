import pandas as pd
import time
import json
import os, re

from requests.packages.urllib3.exceptions import InsecureRequestWarning

from pslregex.regexer import getRegexes
from pslregex.etld import getETLDframe

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
    def __init__(self) -> None:
        self.etldFrame = None
        self.regexes = None
        pass

    def init(self):
        tmp = init()
        self.etldFrame = tmp[0]
        print(self.etldFrame)
        self.regexes = tmp[1]
        pass

    def single(self, dn):
        dn = dn.split('.')[::-1]
        tld = dn[0]
        dn = '.'.join(dn)
        regex = self.regexes[tld]

        start = time.time()
        m = regex.match(dn)
        if m is None:
            raise 'Not found'
        gd = m.groupdict()
        gd = [ int(k[1:]) for k in gd if gd[k] is not None ]
        end = time.time() - start

        print(f'Found {len(gd)} solution/s in {end} sec')
        return self.etldFrame.loc[gd[0]].to_markdown()

    def frame(self, frame):
        start = time.time()
        dnRevertedSeries = frame.dn.str.split('.').apply(lambda s: [ s[-1] , '.'.join(s[::-1]) ])

        def match(s):
            if s[0] not in self.regexes:
                return -1
            gd = self.regexes[s[0]].match(s[1]).groupdict()
            gd = [ int(k[1:]) for k in gd if gd[k] is not None ]
            return gd[0] if len(gd) == 1 else gd

        matchesSeries = dnRevertedSeries.apply(match)
        mergeFrame = matchesSeries.to_frame().merge(self.etldFrame, left_on='dn', right_index=True, how='left').drop(columns='dn')
        result = frame.dn.to_frame().join(mergeFrame).copy()
        end = time.time() - start
        print(f'Merged {frame.shape[0]} in {end} sec ({end/frame.shape[0]} sec/dn)')
        return result
    pass

def test():
    psl = PSLRegex()

    psl.init()

    single = psl.single('google.co.uk')

    datasetFrame = pd.read_csv('/home/princio/Desktop/malware_detection/nn/nn/dataset_training.csv').iloc[0:20_000]
    datasetFrame['tld'] = datasetFrame.dn.apply(lambda dn: dn[1 + dn.rfind('.'):])

    frame = psl.frame(datasetFrame)

    print(single)

    print(frame)

    pass
