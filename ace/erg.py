
from util import per_section

def erg_lexicon(lextdl=erg_lextdl):
    lexkey_name = defaultdict(list)
    with open(lextdl, 'r') as fin:
        for entry in per_section(fin):
            if not entry.strip(): # skip empty lines.
                continue
            entry = entry.strip()
            lexkey = entry.split(":=")[0]
            
            # Getting the ORTH values.
            orth = re.findall(r'ORTH \<(.*?)\>,', entry)
            if not orth:
                orth = re.findall(r'ORTH \<(.*?)\>', entry)
            orth = orth[0]
            lexnames = extract_between_quotations(orth)
            lexkey_name[lexkey].append(lexnames)
            
            # Getting the KEYREL.PRED values.
            keyrelpred = re.findall(r'KEYREL\.PRED (.*?) ]', entry)
            if keyrelpred:
                lexkey2 = keyrelpred[0]
                if lexkey2.strip().startswith('"'):
                    lexkey2 = extract_between_quotations(lexkey2)[0]
                lexkey_name[lexkey2].append(lexnames)
                    
            # Getting the LKEYS.KEYREL.PRED values.
            lkeyskeyrelpred = re.findall(r'LKEYS\.KEYREL\.PRED (.*?),', entry)
            if lkeyskeyrelpred:
                lkeyskeyrelpred = lkeyskeyrelpred[0]
                if lkeyskeyrelpred.startswith('"'):
                    lexkey3 = extract_between_quotations(lkeyskeyrelpred)[0]
                else:
                    lexkey3 = lkeyskeyrelpred
                lexkey_name[lexkey3].append(lexnames)
           
    return lexkey_name