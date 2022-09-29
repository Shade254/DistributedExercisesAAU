from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class GossipMessage(MessageStub):

    def __init__(self, sender: int, destination: int, secrets):
        super().__init__(sender, destination)
        # we use a set to keep the "secrets" here
        self.secrets = secrets

    def __str__(self):
        return f'{self.source} -> {self.destination} : {self.secrets}'


class Gossip(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        # for this exercise we use the index as the "secret", but it could have been a new routing-table (for instance)
        # or sharing of all the public keys in a cryptographic system
        self._secrets = set([index])

    def run(self):
        # the following is your termination condition, but where should it be placed?
        # if len(self._secrets) == self.number_of_devices():
        #    return
        return

    def print_result(self):
        print(f'\tDevice {self.index()} got secrets: {self._secrets}')


class AllToAllGossip(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._secrets = set([index])
        # select master node
        self._master_index = 2

    def run(self):
        if self.index() == self._master_index:
            self.run_master()
        else:
            self.run_slave()

    def run_master(self):
        # master receives all secrets
        while len(self._secrets) < self.number_of_devices():
            ingoing = self.medium().receive()
            if ingoing == None:
                continue
            self._secrets = self._secrets.union(ingoing.secrets)

            if len(self._secrets) == self.number_of_devices():
                break

        # and then distributes them
        for i in range(0, self.number_of_devices()):
            if i != self.index():
                outgoing = GossipMessage(self.index(), i, self._secrets)
                self.medium().send(outgoing)

    def run_slave(self):
        # send own secret to the master
        outgoing = GossipMessage(self.index(), self._master_index, self._secrets)
        self.medium().send(outgoing)

        # receive complete info from master
        while len(self._secrets) < self.number_of_devices():
            ingoing = self.medium().receive()
            if ingoing == None:
                continue

            self._secrets = self._secrets.union(ingoing.secrets)

    def print_result(self):
        print(f'\tDevice {self.index()} got secrets: {self._secrets}')


class NeighboursGossip(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._secrets = set([index])
        # select initiator
        self._master_index = 0
        # create topology
        self._left_link = self.index() - 1
        if self._left_link < 0:
            self._left_link = self.number_of_devices() - 1
        self._right_link = (self.index() + 1) % self.number_of_devices()

    def run(self):
        if self.index() == self._master_index:
            self.run_master()
        else:
            self.run_slave()

    def run_master(self):
        # initiator sends his secret in a chosen direction
        initial_direction = self._right_link
        outgoing = GossipMessage(self.index(), initial_direction, self._secrets)
        self.medium().send(outgoing)

        # and waits until he gets all the information back
        while len(self._secrets) < self.number_of_devices():
            ingoing = self.medium().receive()
            if ingoing == None:
                continue
            self._secrets = self._secrets.union(ingoing.secrets)

    def run_slave(self):
        # ordinary node listens for a message
        while len(self._secrets) < self.number_of_devices():
            ingoing = self.medium().receive()
            if ingoing == None:
                continue
            # updates own secrets
            self._secrets = self._secrets.union(ingoing.secrets)
            # and forward them along the ring
            self.forward(ingoing)

    def forward(self, msg):
        forward_to = self._right_link

        if msg.source == self._right_link:
            forward_to = self._left_link
        # last slave in the line (master's neighbour) reverts the direction
        # this ensures that all secrets are distributed in minimal (2*N-1) number of messages
        if forward_to == self._master_index and len(msg.secrets) == self.number_of_devices() - 1:
            self.reply(msg)
        else:
            outgoing = GossipMessage(self.index(), forward_to, self._secrets)
            self.medium().send(outgoing)

    def reply(self, msg):
        reply_to = self._right_link

        if msg.source == self._left_link:
            reply_to = self._left_link

        outgoing = GossipMessage(self.index(), reply_to, self._secrets)
        self.medium().send(outgoing)

    def print_result(self):
        print(f'\tDevice {self.index()} got secrets: {self._secrets}')
