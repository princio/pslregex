
import os
import re
import unittest
import pandas

from publicsuffixlist import PublicSuffixList, b, encode_idn, u

from pslregex import PSLdict

if __name__ == "__main__":
    psl = PSLdict()

    psl.init(False, False)
    
    ts = []
    
    ts += [ [ "wWw.eXaMpLe.cO.Jp", "co.jp", None] ]
    ts += [ [ "www..invalid", None, None ] ]
    ts += [ [ ".example.com", None, None ] ]
    ts += [ [ "example.com.", None, None ] ]
    ts += [ [ '', None, None ] ]
    ts += [ [ '', None, None ] ]
    ts += [ [ '', None, None ] ]
    ts += [ [ 'www.example.香港', '香港', None ] ]
    ts += [ [ 'www.example.unknowntld', None, None ] ]
    ts += [ [ 'example.nagoya.jp', 'jp', None ] ]
    ts += [ [ 'filler.example.nagoya.jp', '*.nagoya.jp', None ] ]
    ts += [ [ "example.com", "com", None ] ]
    ts += [ [ "compute.example.com", "com", None ] ]
    ts += [ [ "region.compute.example.com", "com", None ] ]
    ts += [ [ "user.region.compute.example.com", "com", None ] ]
    ts += [ [ "sub.user.region.compute.example.com", "com", None ] ]
    ts += [ [ "sub.user.region.compute.example.com", "com", None ] ]
    ts += [ [ 'atim.s3.cn-north-1.amazonaws.com.cn', 'com.cn', 's3.cn-north-1.amazonaws.com.cn' ] ]
    ts += [ [ 'atim.astersik.compute.amazonaws.com', 'com', '*.compute.amazonaws.com' ] ]
    ts += [ [ 'ciao.compute.amazonaws.com', 'com', None ] ]
    ts += [ [ 'cvyh1po636avyrsxebwbkn7.ddns.net', 'net', 'ddns.net' ] ]

    df = []
    for t in ts:
        a = psl.match(t[0])

        t[0] = t[0].lower()

        icann = { 'suffix': None }
        icann_dn = True
        if t[1] is None and a['icann'] is None:
            pass
        elif a['icann'] is None:
            pass
        else:
            icann = a['icann']
            sfx_nl = icann['suffix'].count('.') + 1
            labels = t[0].split('.')
            x = '.'.join(labels[:-1*sfx_nl])
            icann_dn = x == icann['dn-suffix']
            if icann_dn is False:
                icann_dn = x + '|' + icann['dn-suffix']

        
        private = { 'suffix': None }
        private_dn = True
        if t[1] is None and a['private'] is None:
            pass
        elif a['private'] is None:
            pass
        else:
            private = a['private']
            sfx_nl = private['suffix'].count('.') + 1
            labels = t[0].split('.')
            x = '.'.join(labels[:-1*sfx_nl])
            private_dn = x == private['dn-suffix']
            if private_dn is False:
                private_dn = x + '|' + private['dn-suffix']
        
        df += [ [ icann['suffix'] == t[1], t[1], icann['suffix'], private['suffix'] == t[2], t[2], private['suffix'], t[0], icann_dn, private_dn ] ]

    print(pandas.DataFrame(df, columns=pandas.MultiIndex.from_tuples([
        ( 'icann', 'equal' ), ( 'icann', 'test' ), ( 'icann', 'psl' ),
        ( 'private', 'equal' ), ( 'private', 'test' ), ( 'private', 'psl' ),
        ( 'X', 'dn' ),
        ( 'X', 'icann' ),
        ( 'X', 'private' ),
    ])))
