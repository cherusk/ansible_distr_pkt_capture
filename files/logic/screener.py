#!/usr/bin/env python

import json
from concurrent import futures
from collections import Callable
from collections import  defaultdict
from scapy.all import rdpcap
from scapy.all import TCP


associated_context_file = "{{ associated_context }}"


class Flow(Callable):
    def __init__(self, flow_association):
        self.flow_key = flow_association.keys()[0]
        self.flow_gist = flow_association.values()[0]
        # only outgoing
        self.materialized_flow_pkts = [rdpcap(pkt_file)
                                       for pkt_file in
                                       self.flow_gist['pcap']['egress']]
        self.retrans_count = 0

    def count_retransmissions(self):
        def increment(incrementee, delta=1):
            return incrementee + delta

        for egress_flow_pkts in self.materialized_flow_pkts:
            sub_retrans_count = 0
            last_sequ_num = -1
            for pkt in egress_flow_pkts:
                tcp_header = pkt[TCP]
                if tcp_header.seq <= last_sequ_num:
                    sub_retrans_count = increment(sub_retrans_count)
                last_sequ_num = tcp_header.seq

            self.retrans_count = increment(self.retrans_count,
                                           sub_retrans_count)

    def __call__(self):
        self.count_retransmissions()
        return self.flow_gist['holder'], self.retrans_count


def run():
    result = defaultdict(lambda: defaultdict(int))

    with open(associated_context_file, 'rb') as ac_file:
        a_context = json.load(ac_file)
        pending = {}
        with futures.ThreadPoolExecutor(max_workers=100) as executor:
            for origin_host, flow_association in a_context.items():
                future = executor.submit(Flow(flow_association))
                pending[future] = origin_host
            done_iter = futures.as_completed(pending)
            for future in done_iter:
                origin_host = pending[future]
                holder, retrans_count = future.result()
                result[origin_host][json.dumps(holder)] = retrans_count

    for origin_host, retrans_association in result.items():
        result[origin_host] = sorted(retrans_association.items(),
                                     key=lambda kv: kv[1])

    print(json.dumps(result))

if __name__ == "__main__":
    run()
