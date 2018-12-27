ansible_distr_pkt_capture
=========

Non-Invasive, lightweight, potentially ad-hoc wielded, distributed packet capturing logic based on ansible.


Rationale
-------

* There are already a decent set of distributed and open packet capturing solutions. e.g. **Moloch**.
Though, those tend to demand an excessive set of physical prerequisites or an gargantuan setup procedure
coming with literally a myriad of dependencies attached. In other words, those are geared to anything 
than being used ad-hoc.
* For many flow analysis aspects, there are superior kernel internal tracing tools on the way or already
existant (e.g.based on ebpf to name one). Nigh, these come with performance burdens incurred when built
into the kernel and therefore hardly allow to be employed for every production kernel of any landscape.
Holding a subset of such tracing capable nodes might not suffice to confine down a more wide-spread, 
tenacious culprit. Let alone legacy systems not yet on recent enough kernels. A pcap engine, though, 
is in place extensively, well understood and plain to use throughout different problem sets.


Install Hints
-------

Nominally, shouldn't deviate from standard role inclusion approaches.

**Prerequisits**
* The central dependency **tcpflow** lacked pcap preservation, 
it was expedited for that recently. Therefore, at first, until the next release,
you'll need the latest build of tcpflow on your target capturing platforms.


Example
-------

``` 
---
- hosts: all 
  remote_user: root
    tasks:
        - include_role:
                name: ansible_distr_pkt_capture
          vars:
            processing_logic: # custom post processing
                - ../tests/retransmitter.yml
            tcpflow_cmd: /usr/bin/tcpflow
            ss2_cmd: /usr/bin/ss2
            capture_iface: any
            gather_basin: /tmp
            gather_stretch 300
            controller_basin: /var/opt/distr_capture/

```

Vars are defaulted within sane margins: the platform specifics almost certainly will require minimal config effort.

License
-------

MIT

Author Information
------------------

Matthias Tafelmeier
