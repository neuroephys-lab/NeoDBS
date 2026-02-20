import json 

def open_alpha_omega(file_path):
    file = open(file_path,'r',encoding='utf-8')
    try:
        raw = json.load(file)
    except Exception:
        return 'JSON corrupted.'
    
    return raw

merged = 'C:\\Users\\OCD\\Desktop\\LRODRIGUES\\AO\\merge_aot0001.json'

raw = open_alpha_omega(merged)

ratio = raw['CSPK_01___Central']['KHz'] / raw['CLFP_01___Central']['KHz']

time =  len(raw['CSPK_01___Central']['Samples']) / raw['CSPK_01___Central']['KHz']

print(time/1000)

print('level fs (kHz): ', len(raw['CSEG_01___Central']['LEVEL'])/time)

if isinstance(raw,str): print(raw)
else:
    print('LFP Samples:', len(raw['CLFP_01___Central']['Samples']))
    print('SPK Samples:', len(raw['CSPK_01___Central']['Samples']))
    print('SEG Samples:', len(raw['CSEG_01___Central']['LEVEL']))