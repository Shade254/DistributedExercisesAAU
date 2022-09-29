from emulators.Device import Device
from emulators.Medium import Medium
from emulators.MessageStub import MessageStub


class RipMessage(MessageStub):
    def __init__(self, sender: int, destination: int, table):
        super().__init__(sender, destination)
        self.table = table

    def __str__(self):
        return f'RipMessage: {self.source} -> {self.destination} : {self.table}'


class RoutableMessage(MessageStub):
    def __init__(self, sender: int, destination: int, first_node: int, last_node: int, content):
        super().__init__(sender, destination)
        self.content = content
        self.first_node = first_node
        self.last_node = last_node

    def __str__(self):
        return f'RoutableMessage: {self.source} -> {self.destination} : {self.content}'


class RipCommunication(Device):

    def __init__(self, index: int, number_of_devices: int, medium: Medium):
        super().__init__(index, number_of_devices, medium)
        self._left_link = self.index() - 1
        if self._left_link < 0:
            self._left_link = self.number_of_devices() - 1
        self._right_link = (self.index() + 1) % self.number_of_devices()

        self.neighbors = [self._left_link, self._right_link]

        self.routing_table = dict()

        self.messages = [(0, 1, "message")]
        self.sent = False

    def run(self):
        for neigh in self.neighbors:
            self.routing_table[neigh] = (neigh, 1)
        self.routing_table[self.index()] = (self.index(), 0)
        for neigh in self.neighbors:
            self.medium().send(RipMessage(self.index(), neigh, self.routing_table))

        while True:
            ingoing = self.medium().receive()
            if ingoing is None:
                # this call is only used for synchronous networks
                self.medium().wait_for_next_round()
                continue

            # create routing tables
            if type(ingoing) is RipMessage:
                returned_table = self.merge_tables(ingoing.source, ingoing.table)
                print(
                    f"Device {self.index()}: Got new table from {ingoing.source} new info? {returned_table is not None}")
                if returned_table is not None:
                    self.routing_table = returned_table
                    for neigh in self.neighbors:
                        self.medium().send(RipMessage(self.index(), neigh, self.routing_table))

            # relay or accept routable messages
            if type(ingoing) is RoutableMessage:
                print(
                    f"Device {self.index()}: Routing from {ingoing.first_node} to {ingoing.last_node} via #{self.index()}: [#{ingoing.content}]")
                if ingoing.last_node is self.index():
                    print(
                        f"\tDevice {self.index()}: delivered message from {ingoing.first_node} to {ingoing.last_node}: {ingoing.content}")
                    self.medium().wait_for_next_round()
                    continue
                if self.routing_table[ingoing.last_node] is not None:
                    (next_hop, distance) = self.routing_table[ingoing.last_node]
                    self.medium().send(
                        RoutableMessage(self.index(), next_hop, ingoing.first_node, ingoing.last_node, ingoing.content))
                    self.medium().wait_for_next_round()
                    continue
                print(
                    f"\tDevice {self.index()}:  DROP Unknown route #{ingoing.first_node} to #{ingoing.last_node} via #{self.index()}, message #{ingoing.content}")

            # sent messages after routing table complete (just once)
            if self.routing_table_complete() and not self.sent:
                for (s, d, m) in self.messages:
                    if s == self.index():
                        message = RoutableMessage(s, self.routing_table[d][0], s, d, m)
                        self.medium().send(message)

                self.sent = True

            self.medium().wait_for_next_round()

    # merge tables - updates entries for nodes we dont know path to yet or we know worse path to
    # return None is none entry was updated
    def merge_tables(self, src, new_table):
        updated_table = self.routing_table.copy()
        updated = False

        for dest in new_table.keys():
            if dest not in self.routing_table or self.routing_table[dest][1] > (new_table[dest][1] + 1):
                updated_table[dest] = (src, new_table[dest][1] + 1)
                updated = True

        if updated:
            return updated_table

        return None

    # routing tables complete if we have an optimal distance to every node (we need to know network topology for that)
    def routing_table_complete(self):
        if len(self.routing_table) < self.number_of_devices():
            return False
        for row in self.routing_table:
            (next_hop, distance) = self.routing_table[row]
            if distance > (self.number_of_devices() / 2):
                return False
        return True

    def print_result(self):
        sorted_keys = sorted(self.routing_table.keys())
        sorted_table = {key: self.routing_table[key] for key in sorted_keys}
        print(f'\tDevice {self.index()} has routing table: {sorted_table}')
