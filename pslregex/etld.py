
import pandas as pd
import requests
import re


def getETLDframe():
    psl_file = requests.get(
            'https://publicsuffix.org/list/public_suffix_list.dat',
            verify=False,
            allow_redirects=True,
            timeout=5
        ).text.split('\n')


    df_iana = pd.read_html('https://www.iana.org/domains/root/db', attrs = {'id': 'tld-table'})[0]

    df_tldlist = pd.read_csv('https://tld-list.com/df/tld-list-details.csv')

    df_iana = df_iana.rename(columns={
        'Domain': 'tld', 'Type': 'type', 'TLD Manager': 'manager'
    })

    df_tldlist = df_tldlist.rename(columns={'Punycode': 'punycode'})

    if (df_iana['tld'].apply(lambda tld: tld.count('.') > 1)).sum() > 0:
        raise 'Unexpected: TLDs should have only one point each.'

    # cleaning TLDs from points and special right-to-left character
    df_iana['tld'] = df_iana.tld.str.replace('.', '', n=1, regex=False)
    df_iana['tld'] = df_iana.tld.str.replace('\u200f', '', n=1, regex=False)
    df_iana['tld'] = df_iana.tld.str.replace('\u200e', '', n=1, regex=False)

    # converting Type labels to IANA naming convention
    df_tldlist['Type'] = df_tldlist['Type'].str.replace('gTLD', 'generic', regex=False)
    df_tldlist['Type'] = df_tldlist['Type'].str.replace('ccTLD', 'country-code', regex=False)
    df_tldlist['Type'] = df_tldlist['Type'].str.replace('grTLD', 'generic-restricted',regex=False)
    df_tldlist['Type'] = df_tldlist['Type'].str.replace('sTLD', 'sponsored', regex=False)


    df = df_iana.merge(df_tldlist, left_on='tld', right_on='TLD', how='outer')


    ### HANDLING NOT COINCIDENT TLDs ###

    # check TLD-types should be the same execept for 'music' and pakistan پاكستان
    if df[(~(df.Type == df['type']))].shape[0] > 2:
        print(df[(~(df.Type == df['type']))])
        raise 'Error: TLD-Types not coincided'

    # check which IANA tlds are not in tldlist
    iana_notin_tldlist = df[df.TLD.isna()].tld
    if iana_notin_tldlist.shape[0] > 0:
        if not (iana_notin_tldlist.shape[0] == 1 and iana_notin_tldlist.iloc[0] == 'music'):
            print(f'Warning: IANA has {iana_notin_tldlist.shape[0]} TLDs not contained in tldlist:')
            for _, tmp in iana_notin_tldlist.iteritems():
                print(f'\t- {tmp}')
    # check which tldlist tlds are not in IANA
    tldlist_notin_iana = df[df.tld.isna()].TLD
    if tldlist_notin_iana.shape[0] > 0:
        if not (tldlist_notin_iana.shape[0] == 1 and tldlist_notin_iana.iloc[0] == 'پاكستان'):
            print(f'Warning: tldlist has {tldlist_notin_iana.shape[0]} TLDs not contained in IANA')
            for _, tmp in tldlist_notin_iana.iteritems():
                print(f'\t- {tmp}')

    # cloning not shared TLDs to specific columns (only one from pakistan)
    nans = df.tld.isna()
    df['tld'].values[nans] = df[nans].TLD
    df['type'].values[nans] = df[nans].Type
    df['manager'].values[nans] = df[nans].Sponsor

    ### FINISHED TO HANDLE NOT COINCIDENT TLDs ###

    df_tld = df[['tld', 'punycode', 'type', 'manager']].copy()

    psl_lines = psl_file

    sections_delimiters = [
        '// ===BEGIN ICANN DOMAINS===',
        '// newGTLDs',
        '// ===BEGIN PRIVATE DOMAINS==='
    ]
    
    sections_names = [
        'icann',
        'icann-new',
        'private-domains'
    ]

    regex_punycode = r'^\/\/ (xn--.*?) .*$'
    regex_comment = r'^\/\/ (?!Submitted)(.*?)(?: : )(.*?)$'

    line_start = 1 + psl_lines.index('// ===BEGIN ICANN DOMAINS===')

    # Take attention to punycodes parsing: a new punycode should be used only for the PSL the punycode comment

    sd = 0
    manager = None
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
            
        tld = line
        tld = tld[tld.rfind('.')+1:]
        
        # if the tld (not the suffix) has changed and so the punycode too
        if last_tld != tld and not punycode_found:
            punycode = None
        punycode_found = False
        
        values.append([ sections_names[sd], tld, punycode, line, manager ])
        
        last_tld = tld
        pass

    df_psl = pd.DataFrame(values, columns=['type', 'tld', 'punycode', 'suffix', 'manager'])

    df_psl = df_psl[['type', 'tld', 'punycode', 'suffix', 'manager']].reset_index()

    df_psl.head()

    # the merge will be done with the tld column

    df = df_psl.reset_index().merge(df_tld.reset_index(), left_on='tld', right_on='tld', suffixes=['_psl', '_tld'], how='outer')

    df['origin'] = 'both'
    df['origin'].values[(~df['type_psl'].isna()) & (df['type_tld'].isna())] = 'PSL'
    df['origin'].values[(~df['type_tld'].isna()) & (df['type_psl'].isna())] = 'TLDLIST'
    df['origin'].values[(df['origin'] == 'both') & (df.tld != df.suffix)] = 'merged'

    df = df.reset_index(drop=True)


    # merge

    # the 'type' columns:
    # - equal to TLDLIST type
    # - only if PSL type is private-domains, replace the previously defined TLDLIST type with the PSL one
    # - for unknown types: other if punycode is empty, orphan-punycode otherwise
    df['type'] = df['type_tld']

    icann_pd = (df['type_psl'] == 'private-domains')
    df['type'].values[icann_pd] = 'private-domains'


    mask = (df['type_tld'].isna() & df['punycode_psl'].isna())
    df['type'].values[mask] = 'other'

    mask = (df['type_tld'].isna() & (~df['punycode_psl'].isna()))
    df['type'].values[mask] = 'orphan-punycode'

    # Checking rows having both punycodes not null matches
    df_punycode = df[~(df.punycode_psl.isna()) & ~(df.punycode_tld.isna())]
    if (df_punycode.punycode_psl != df_punycode.punycode_tld).sum() > 0:
        print('Warning: punycode does not match but should.')
    df['punycode'] = df['punycode_psl']
    notna_punycodetld = ~(df['punycode_tld'].isna())
    df['punycode'].values[notna_punycodetld] = df['punycode_tld'].loc[notna_punycodetld]


    df = df[[
        'suffix', 'tld',
        'punycode',
        'origin',
        'type', 'type_tld', 'type_psl',
        'manager_tld', 'manager_psl'
    ]]


    df.rename(columns={'type_tld': 'tld type', 'type_psl': 'suffix type'}, inplace=True)
    df.rename(columns={'manager_tld': 'tld manager', 'manager_psl': 'psl comment'}, inplace=True)

    suffix_na = df.suffix.isna()
    tld_na = df.tld.isna()

    # checking empty tlds (should never happen)
    if df[tld_na].shape[0] > 0:
        raise f'Error: {df[tld_na].shape[0]} NaN empty TLDs'
        
    # checking empty suffixes
    if df[suffix_na & tld_na].shape[0] > 0:
        print(f'Warning: there are {df[suffix_na].shape[0]} NaN Suffixes and TLDs')
    df.suffix.values[suffix_na] = df.tld[suffix_na]

    df = df.fillna('')

    df.to_csv('tld_and_suffixes.csv')

    df[df['origin'] != 'both'].to_csv('differents.csv')

    return df.reset_index().rename(columns={'index': 'id'})