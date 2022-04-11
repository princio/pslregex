
import pandas as pd
import requests
import re, os

codes = {
    'type': {
        'country-code': 'cc',
        'sponsored': 'sp',
        'infrastructure': 'in',
        'generic-restricted': 'gr',
        'generic': 'ge',
        'test': 'te'
    },
    'section': {
        'icann': 'i',
        'icann-new': 'n',
        'private-domain': 'p'
    }
}

### Coding:
###
### A code is composed by: S00000TTE1
### Where:
### - S: the section (icann, icann-new, private-domain)
### - 00000: five digits which indicates the index in the etld frame
### - TT: two letters which indicates the type
### - E: if is an exception suffix
### - 1: the number of labels


inv_codes = {}
for t in [ 'type', 'section' ]:
    inv_codes[t] = {v: k for k, v in codes[t].items() }

class ETLD:
    def __init__(self, dir) -> None:
        self.files = {}
        self.dir = dir
        self.frame = None
        pass

    def iframe(self):
        dfi = pd.DataFrame(self.frame.suffix.str.split('.').apply(lambda x: x[::-1]).to_list(), index=self.frame.index).fillna('')
        dfi['suffix'] = self.frame['suffix']
        dfi['code'] = self.frame['code']
        dfi['punycode'] = self.frame['punycode']
        dfi['type'] = self.frame['type']
        dfi['origin'] = self.frame['origin']
        dfi['section'] = self.frame['section']
        dfi['isprivate'] = self.frame['isprivate']
        
        return dfi.sort_values(by=dfi.columns.tolist()).copy()

    def init(self, download=False, update=False):

        if not update and os.path.exists(os.path.join(self.dir, 'etld.csv')):
            self.frame = pd.read_csv(os.path.join(self.dir, 'etld.csv'), index_col=0)
            return

        self.files = {}

        if download or not os.path.exists(os.path.join(self.dir, 'public_suffix_list.dat')):
            self.files['psl'] = requests.get(
                'https://publicsuffix.org/list/public_suffix_list.dat',
                verify=False,
                allow_redirects=True,
                timeout=5
            ).text

            with open(os.path.join(self.dir, 'public_suffix_list.dat'), 'w') as f:
                f.writelines(self.files['psl'])

        if download or not os.path.exists(os.path.join(self.dir, 'iana.csv')):
            self.files['iana'] = pd.read_html('https://www.iana.org/domains/root/db', attrs = {'id': 'tld-table'})[0]
            self.files['iana'].to_csv(os.path.join(self.dir, 'iana.csv'))

        if download or not os.path.exists(os.path.join(self.dir, 'tldlist.csv')):
            self.files['tldlist'] = pd.read_csv('https://tld-list.com/df/tld-list-details.csv')
            self.files['tldlist'].to_csv(os.path.join(self.dir, 'tldlist.csv'))


        with open(os.path.join(self.dir, 'public_suffix_list.dat'), 'r') as f:
            self.files['psl'] = [ l.replace('\n', '') for l in f.readlines() ]
        self.files['iana'] = pd.read_csv(os.path.join(self.dir, 'iana.csv'))
        self.files['tldlist'] = pd.read_csv(os.path.join(self.dir, 'tldlist.csv'))

        def parseIANA():
            df = self.files['iana'].rename(columns={
                'Domain': 'tld', 'Type': 'type', 'TLD Manager': 'manager'
            })
            # cleaning TLDs from points and special right-to-left character
            df['tld'] = df.tld.str.replace('.', '', n=1, regex=False)
            df['tld'] = df.tld.str.replace('\u200f', '', n=1, regex=False)
            df['tld'] = df.tld.str.replace('\u200e', '', n=1, regex=False)
            
            if (df.tld.apply(lambda tld: tld.count('.') > 1)).sum() > 0:
                raise 'Unexpected: TLDs should have only one point each.'
            
            df = df.fillna('-').sort_values(by='tld').reset_index(drop=True).reset_index()
            
            return df

        def parseTLDLIST():
            df = self.files['tldlist'].copy()
            df.rename(columns={ col: col.lower() for col in df.columns }, inplace=True)
            # df.rename(columns={ 'sponsor': 'manager' }, inplace=True)
            # converting Type labels to IANA naming convention
            df['type'] = df['type'].str.replace('gTLD', 'generic', regex=False)
            df['type'] = df['type'].str.replace('ccTLD', 'country-code', regex=False)
            df['type'] = df['type'].str.replace('grTLD', 'generic-restricted',regex=False)
            df['type'] = df['type'].str.replace('sTLD', 'sponsored', regex=False)
            
            df = df.fillna('-').sort_values(by='tld').reset_index(drop=True).reset_index()
            
            return df

        def parseICANN():
            # import json

            # with open('./country-json/src/country-by-domain-tld.json') as json_file:
            #     cc_tld = {}
            #     for line in json.load(json_file):
            #         if line['tld'] is not None:
            #             cc_tld[line['tld'].replace('.', '')] = line['country']
            
            # cc_tld['ac'] = 'Ascension Island'
            # cc_tld['ax'] = 'Åland Islands'
            # cc_tld['bl'] = 'Collectivité territoriale de Saint-Barthélemy'
            # cc_tld['bq'] = 'Caribbean Netherlands'
            # cc_tld['cw'] = 'Curaçao'
            # cc_tld['eu'] = 'Europe'
            # cc_tld['fm'] = 'Federated States of Micronesia'
            # cc_tld['fo'] = 'Faroe Islands'
            # cc_tld['gg'] = 'Bailiwick of Guernsey'
            # cc_tld['je'] = 'Jersey'
            # cc_tld['im'] = 'Isle of Man'
            # cc_tld['me'] = 'Montenegro'
            # cc_tld['mf'] = 'Collectivity of Saint Martin'
            # cc_tld['su'] = 'Russian Federation'
            # cc_tld['sx'] = 'Sint Maarten'
            # cc_tld['tp'] = 'retired'
            # cc_tld['tw'] = 'Taiwan'
            # cc_tld['uk'] = 'United Kingdom'
            # cc_tld['um'] = 'United States Minor Outlying Islands'
            # cc_tld['ελ'] = 'Greece'
            # cc_tld['ευ'] = 'Greece'
            # cc_tld['бг'] = 'Bulgaria'
            # cc_tld['бел'] = 'Belarus'
            # cc_tld[''] = ''
                
            df_iana = parseIANA()
            
            df_tldlist = parseTLDLIST()
            
            df = df_iana.merge(df_tldlist, on=[ 'tld', 'type' ], how='outer', suffixes=('_iana', '_tldlist'))
            
            # TODO: verbose variable
            # print(f'IANA tlds not present in TLDLIST: {df[df.index_iana.isna()].shape[0]}')
            # print(f'TLDLIST tlds not present in IANA: {df[df.index_tldlist.isna()].shape[0]}')
            
            df = df.drop(columns=[ 'index_iana', 'index_tldlist' ]).fillna('-')
            df = df.sort_values(by='tld').reset_index()
            
            # df['country'] = df.tld.apply(lambda tld: '-' if tld not in cc_tld else cc_tld[tld])
            
            return df[['index','tld','type','manager', 'sponsor','punycode','language code','translation','romanized','rtl' ]] #, 'country']]

        def parsePSL():
            psl_lines = self.files['psl'].copy()

            sections_delimiters = [
                '// ===BEGIN ICANN DOMAINS===', '// newGTLDs', '// ===BEGIN PRIVATE DOMAINS==='
            ]

            sections_names = [ 'icann', 'icann-new', 'private-domain' ]

            regex_punycode = r'^\/\/ (xn--.*?) .*$'
            regex_comment = r'^\/\/ (?!Submitted)(.*?)(?: : )(.*?)$'

            line_start = 1 + psl_lines.index(sections_delimiters[0])

            # Take attention to punycodes parsing: a new punycode should be used only for the next PSL
            
            sd = 0
            punycode = None
            values = []
            last_tld = ''
            punycode_found = False
            for i in range(line_start, len(psl_lines)):
                line = psl_lines[i]
                if len(line) == 0: continue
                if sd+1 < len(sections_delimiters) and line.find(sections_delimiters[sd+1]) == 0:
                    sd += 1
                if line.find('//') == 0:
                    punycode_match = re.match(regex_punycode, line)
                    if punycode_match is not None:
                        punycode_found = True
                        punycode = punycode_match[1]
                    else:
                        first_comment_match = re.match(regex_comment, line)
                        if first_comment_match is not None:
                            manager = first_comment_match[1]
                    continue

                suffix = line
                tld = suffix[suffix.rfind('.')+1:]

                # if the tld (not the suffix) changed, the punycode changed too
                if last_tld != tld and not punycode_found:
                    punycode = None
                punycode_found = False

                values.append([ suffix, tld, punycode, sections_names[sd] ]) #, manager

                last_tld = tld
                
                pass

            df = pd.DataFrame(values, columns=[ 'suffix', 'tld', 'punycode', 'type'])

            return df.reset_index()
    
        def parse():

            df_icann = parseICANN()
            df_psl = parsePSL()

            df = df_icann.merge(df_psl, on='tld', how='outer', suffixes=('_icann', '_psl'))

            # TODO: verbose variable
            # print(f'ICANN tlds not present in PSL: {df[df.index_icann.isna()].shape[0]}')
            # print(f'PSL tlds not present in ICANN: {df[df.index_psl.isna()].shape[0]}')

            df = df[['suffix', 'tld', 'punycode_icann', 'punycode_psl', 'type_icann', 'type_psl', 'index_icann', 'index_psl' ]]

            df['tld'] =    df.tld.where(~df.index_icann.isna(), df[df.index_icann.isna()].suffix)
            df['suffix'] = df.suffix.where(~df.index_psl.isna(), df[df.index_psl.isna()].tld)
            
            df['exception'] = df['suffix'].str[0] == '!'
            df['suffix'] = df.suffix.where(~df.exception, df[df.exception].suffix.str[1:])

            df['newGLTD'] = df['type_psl'] == 'new-icann'

            df['origin'] = 'both'
            df['origin'] = df.origin.where(~df.index_icann.isna(), 'PSL')
            df['origin'] = df.origin.where(~df.index_psl.isna(), 'icann')
            df['punycode'] = df.punycode_icann.where(~df.punycode_icann.isna(), 'icann')
            df['punycode'] = df.punycode_psl.where(~df.punycode_psl.isna(), df.punycode_psl[~df.punycode_psl.isna()])

            df['section'] = df['type_psl'].where(~(df['type_psl'] == 'icann'), 'icann')
            df['section'] = df['type_psl'].where(~(df['type_psl'] == 'new-icann'), 'icann')
            df['section'] = df['type_psl'].where(~(df['type_psl'] == 'private-domain'), 'private-domain')
            df['section'] = df['type_psl'].where(~(df['type_psl'].isna()), 'icann')

            df['type'] = df['type_icann']
            df['type'] = df['type'].where(~((df['type_icann'].isna()) & (df['punycode_psl'].str.count('\-') > 0) & (df['type_psl'] == 'icann')), 'country-code')
            df['type'] = df['type'].where(~((df['type_icann'].isna()) & (df['section'] == 'icann')), 'generic')
            df['type'] = df['type'].where(~df['type_icann'].isna(), 'generic')

            df['isprivate'] = 'icann'
            df['isprivate'] = df['isprivate'].where(~(df['section'] == 'private-domain'), 'private')

            df = df.sort_values(by='suffix').reset_index(drop=True).reset_index()

            df['code'] = df['section'].apply(lambda o: codes['section'][o]) \
                + df['index'].apply(lambda x: f'{{0:0>5}}'.format(x)) \
                + df['type'].apply(lambda t: codes['type'][t]) \
                + df['exception'].apply(lambda e: 'e' if e else 'd') \
                + df['suffix'].str.count('\.').astype(str)

            df = df[[ 'code', 'suffix', 'tld', 'punycode', 'type', 'origin', 'section', 'newGLTD', 'exception', 'isprivate' ]]
            
            return df.copy()
        
        self.frame = parse()

        pass

def getCountry(df):
    # TODO: problem with ISO Codes GRE, USSR and regex
    import wptools
    import wikipedia

    cctld = df[(df.type == 'country-code') & (df.country == '-')].sort_values(by='country').tld

    ibreg = re.compile(r'Entities connected with.*?\{\{(?:(?:\w+\|)?)?(?:(?P<ISO>[A-Z]+)|(?P<Normal>[\w, ]+))\}\}(?:\s+\[\[(?P<link>[\w, ]+)\|?(?P<name>[\w, ]+)\]\])?')

    def try_infobox(page):
        so = page.get_parse()
        infobox = so.data['infobox']['intendeduse']
        m = ibreg.match(infobox)
        if m is not None:
            return m.groupdict()
        return None


    def try_page(pageid):
        p = wikipedia.page(pageid=pageid).html()
        p = p[p.find('Entities connected with'):]
        p = p[:p.find('</tr>')].replace('\n', '')
        m = preg.match(p)
        if m is not None:
            return m.groups()[0]
        return None


    cc = {}
    a = True
    for tld in cctld:
        if tld == tldk:
            a = False
            continue
        if a: continue
        
        country = None
        
        try:
            page = wptools.page(f'.{tld}', silent=True)
        except Exception as e:
            print(e)
            pass
        
        query = page.get_query().data
        
        print('title=' + query['title'])
        
        if page is not None:
            if query['title'][0] == '.':
                country = try_infobox(page)
                if country.upper() == country:
                    print(wikipedia.search(f'country {country}'))
            else:
                country = query['title']
        else:
            q = wikipedia.search(tld)
            country = q[0]
            
            
        print(country)
                
        cc[tld] = country
    return cc