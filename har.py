from __future__ import print_function
import sys
import json

fin = open(sys.argv[1], "r")
har = json.load(fin)

ent = har['log']['entries']
assert type(ent) == list

ret = list()
ne = dict()
smap = dict()
for e in ent:
    if not '_protocol' in e:
        continue
    if e['_protocol'] != 'HTTP/2':
        continue
    if not '_http2_stream_id' in e:
        continue
    if not '_client_port' in e:
        continue
    if not '_initiator' in e:
        continue
    cur = dict()
    # cur['connection'] = int(e['_client_port'])
    cur['connection'] = 12345
    cur['url'] = e['_full_url']
    cur['initiator'] = e['_initiator']
    if cur['initiator'] == cur['url']:
        cur['initiator'] = ''
    cur['size'] = max(int(e['_objectSize']), 1)
    cur['stream'] = int(e['_http2_stream_id'])
    # cur['dependency'] = int(e.get('_http2_stream_dependency', 0))
    cur['dependency'] = 0
    cur['weight'] = int(e.get('_http2_stream_weight', 1))
    
    req = cur['request'] = list()
    req.append({'name': ':path', 'value': e['_url']})
    req.append({'name': ':method', 'value': e['_method']})
    req.append({'name': ':authority', 'value': e['_host']})
    for h in e['request']['headers']:
        req.append({'name': h['name'], 'value': h['value']})
    
    resp = cur['response'] = list()
    resp.append({'name': ':status', 'value': str(e['response']['status'])})
    for h in e['response']['headers']:
        resp.append({'name': h['name'], 'value': h['value']})
    
    conn = cur['connection']
    if not conn in ne:
        ne[conn] = 5
        smap[conn] = dict()
    if cur['dependency'] != 0:
        cur['dependency'] = smap[conn][cur['dependency']]
    smap[conn][cur['stream']] = ne[conn]
    cur['stream'] = ne[conn]
    ne[conn] += 2

    ret.append(cur)

json.dump(ret, sys.stdout, indent=2)
fin.close()
