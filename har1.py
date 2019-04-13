from __future__ import print_function
import json
import sys

fin = open(sys.argv[1], 'r')

ents = json.load(fin)
root = ents[0]['url']
conn = ents[0]['connection']

for e in ents:
    e['stream'] += 6
    e['connection'] = conn
    if e['url'] != root and e['initiator'] == '':
        e['initiator'] = root
    cont = ''
    for h in e['response']:
        if h['name'] == 'content-type':
            cont = h['value']
    t = cont.find(';')
    if t > 0:
        cont = cont[:t]
    if cont.startswith('image'):
        e['dependency'] = 7
        e['weight'] = 22
    elif cont.startswith('font'):
        e['dependency'] = 7
        e['weight'] = 42
    elif cont.startswith('application') or cont == '':
        e['dependency'] = 9
        e['weight'] = 32
    elif cont == 'text/css' or cont == 'text/javascript':
        e['dependency'] = 5
        e['weight'] = 32
    elif cont.startswith('text'):
        e['dependency'] = 7
        e['weight'] = 32
    else:
        raise 'unknown ' + cont

psu = (('leader', 5, 0, 201), ('follower', 7, 5, 1), ('unblocked', 9, 0, 101))

for idx, v in enumerate(psu):
    e = {
        'initiator': '',
        'weight': v[3],
        'stream': v[1],
        'url': v[0],
        'request': [
            {
                'name': ':authority', 
                'value': v[0],
            },
        ],
        'dependency': v[2], 
        'connection': conn,
        'response': [
            {
                'name': ':status', 
                'value': '200',
            }, 
        ],
        'size': 1,
    }
    ents.insert(idx, e)

json.dump(ents, sys.stdout, indent=2)

fin.close()
