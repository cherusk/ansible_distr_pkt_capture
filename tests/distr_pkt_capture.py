#!/usr/bin/python

from mininet.net import Containernet
from mininet.node import Controller
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.node import Node
from mininet.log import info, setLogLevel
from mininet.util import waitListening

setLogLevel('info')


def open_ssh_channel(net, opts='', containers=[]):
    cmd_base = '/usr/sbin/sshd %s'
    for c in containers:
        c.sendCmd(cmd_base % opts)

    for server in net.hosts:
        waitListening(server=server, port=22, timeout=30)

net = Containernet(controller=Controller)
info('*** Adding controller\n')
net.addController('c0')
info('*** Adding docker containers\n')
ubuntu1 = net.addDocker('ubuntu1', ip='10.0.0.251', dimage="ubuntu:with_ss2")
ubuntu2 = net.addDocker('ubuntu2', ip='10.0.0.252', dimage="ubuntu:with_ss2") # with_ss2")


info('*** Adding switches\n')
s1 = net.addSwitch('s1')
s2 = net.addSwitch('s2')

info('*** Creating links\n')
net.addLink(ubuntu1, s1)
net.addLink(s1, s2, cls=TCLink, delay='100ms', bw=1)
net.addLink(s2, ubuntu2)

# Create a node in root namespace and link to a switch
info('*** Setup rootNS network\n')
root = Node('root', inNamespace=False)
intf = net.addLink(root, s1).intf1
root.setIP('10.0.0.1/24', intf=intf)

info('*** Starting network\n')
net.start()

root.cmd('ip r add ' + '10.0.0.0/24' + ' dev ' + str(intf))

info('*** Preparing nodes net stack\n')
ubuntu1.sendCmd("ip l set dev ubuntu1-eth0 up")
ubuntu2.sendCmd("ip l set dev ubuntu2-eth0 up")

ubuntu1.sendCmd("ip a add 10.0.0.251/24 dev ubuntu1-eth0")
ubuntu2.sendCmd("ip a add 10.0.0.252/24 dev ubuntu2-eth0")

info('*** form Automation ssh access \n')
open_ssh_channel(net, containers=[ubuntu1, ubuntu2])

info('*** Running CLI\n')
CLI(net)
info('*** Stopping network')
net.stop()
