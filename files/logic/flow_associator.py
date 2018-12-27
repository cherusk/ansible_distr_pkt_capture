#!/usr/bin/env python

import json
import os
import ipaddress as ipa
import collections as col

_controller_basin = "{{ controller_basin }}"
_capture_files = {{ capture_files }}
_tcp_flow_context = {
{% for hv_k, hv_v in hostvars.iteritems() %}
'{{ hv_k }}' : {{ hv_v.tcp_flows_ctxt }}
{% if not loop.last %}
,
{% endif %}
{% endfor %}
}

# from upstream hint: https://www.oreilly.com/library/view/python-cookbook/0596001673/ch04s16.html
#def path_full_split(path):
    #allparts = []
    #while True:
        #parts = os.path.split(path)
        #if parts[0] == path:  # sentinel for absolute paths
            #allparts.insert(0, parts[0])
            #break
        #elif parts[1] == path: # sentinel for relative paths
            #allparts.insert(0, parts[1])
            #break
        #else:
            #path = parts[0]
            #allparts.insert(0, parts[1])
    #return allparts

class Associator:

    marshalling_keys = ['src', 'src_port', 'dst', 'dst_port']

    def __init__(self, tcp_flow_context, capture_root):
        self.f_association_map = col.defaultdict(dict)
        self.result = col.defaultdict(lambda: col.defaultdict(self.flow_dict_factory))

        self.build_auxil_map(tcp_flow_context)
        #self.origin_depth = self.assess_origin_depth(capture_root)

    def flow_dict_factory(self):
        return {'holder' : None,
                'pcap' : {'ingress' : list(),
                           'egress' : list()}}

    #def assess_origin_depth(self, path):
        #return (len(path_full_split(path)) + 1)

    def flow_key_marshaller(self, flow):
        result = {}
        for m_k in self.marshalling_keys:
            result[m_k] = flow[m_k]
        return json.dumps(result)

    def build_auxil_map(self, tcp_flow_context):
        for origin, host_flow_ctxt in tcp_flow_context.items():
            _tcp_flows = host_flow_ctxt['TCP']['flows']
            for flow in _tcp_flows:
                flow_key = self.flow_key_marshaller(flow)
                self.f_association_map[origin][flow_key] = flow

    def act(self, capture_files):
        def ip_reduce_to_hex(ip_addr):
            shards = [int(x) for x in ip_addr.split('.')]
            return bytearray(shards)

        def determine_origin(path):
            shards = path_full_split(path)
            return shards[self.origin_depth]
        
        def form_flow_keys(src_addr, dst_addr, src_port, dst_port):
            flow_hull = dict(zip(self.marshalling_keys,
                                 [str(src_addr), int(src_port),
                                  str(dst_addr), int(dst_port)]))
            flow_hull_inverted = dict(zip(self.marshalling_keys,
                                          [str(dst_addr), int(dst_port),
                                           str(src_addr), int(src_port)]))

            flow_hulls = [ self.flow_key_marshaller(fh) for fh in
                           [flow_hull, flow_hull_inverted] ]

            return flow_hulls 

        def process_addr_part(addr_part):
            addr, port = os.path.splitext(addr_part)
            addr = ipa.ip_address(str(ip_reduce_to_hex(addr)))
            port = port.replace('.', "")
            return addr,port

        for f_batch in capture_files['results']:
            origin = f_batch['_ansible_item_label']
            for f in f_batch['files']:
                pcap_file_n = os.path.basename(f['path'])
                flow_spec,ext = os.path.splitext(pcap_file_n)

                src_part,dst_part = flow_spec.split('-')
                src_addr,src_port = process_addr_part(src_part) 
                dst_addr,dst_port = process_addr_part(dst_part)

                flow_key, flow_key_inverted = form_flow_keys(src_addr, dst_addr,
                                                             src_port, dst_port)

                ss_flow = None
                # determine _flow_key via 'act-ahead' 
                for _flow_key in [flow_key, flow_key_inverted]:
                    try:
                        ss_flow = self.f_association_map[origin][_flow_key]
                        flow_key = _flow_key
                    except KeyError:
                        pass

                ss_flow = self.f_association_map[origin][flow_key]
                self.result[origin][flow_key]['holder'] = ss_flow['usr_ctxt']
                if src_addr == ipa.ip_address(ss_flow['src']):
                    self.result[origin][flow_key]['pcap']['egress'].append(f['path'])
                else:
                    self.result[origin][flow_key]['pcap']['ingress'].append(f['path'])

        return self.result

if __name__ == "__main__":
    associator = Associator(_tcp_flow_context, _controller_basin)
    associator.act(_capture_files)
    print json.dumps(associator.result)
