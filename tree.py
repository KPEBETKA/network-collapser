BIG_MASK = (1 << 32) - 1

def getMaskByMaskSize(mask_size):
    return BIG_MASK ^ ((1 << (32 - mask_size)) - 1)

def getIpVolumeByMaskSize(mask_size):
    return 1 << (32 - mask_size)

class Net:
    def __init__(self, net: int, mask_size: int):
        self.mask_size = mask_size
        self.net = net & getMaskByMaskSize(mask_size)
        self.mask = getMaskByMaskSize(self.mask_size)
        self.ip_volume = getIpVolumeByMaskSize(mask_size)

    def hasSubnet(self, Net: 'Net'):
        if Net.mask_size <= self.mask_size:
            return False
        return self.net == Net.net & self.mask

    def isSameNet(self, Net: 'Net'):
        return (Net.mask_size == self.mask_size) and (Net.net == self.net)

    def getCommonNet(self, OtherNet: 'Net', min_mask_size: int):
        if self.mask_size <= min_mask_size:
            return False
        if OtherNet.mask_size <= min_mask_size:
            return False
        for mask_size in range(min(self.mask_size, OtherNet.mask_size) - 1, min_mask_size - 1, -1):
            mask = getMaskByMaskSize(mask_size)
            if (self.net & mask) == (OtherNet.net & mask):
                return Net(self.net, mask_size)
        return False

    def getAsString(self):
        net = self.net
        bytes = []
        for i in range(4):
            bytes.append(str(net % 256))
            net = net >> 8
        if self.mask_size == 32:
            return '%s' % '.'.join(reversed(bytes))
        else:
            return '%s/%d' % ('.'.join(reversed(bytes)), self.mask_size)

class Node:
    def __init__(self, net: Net, is_real_net: int):
        self.net = net
        self.children = []
        self.is_real_net = is_real_net
        self.real_ip_volume = 0
        self.real_ip_records_count = 0
        self.weight = 0.0
        self.max_child_weight = 0.0
        self.added_fake_ip_volume = 0

    def getNet(self):
        return self.net

    def addSubnet(self, NewNode: 'Node'):
        if self.net.isSameNet(NewNode.net):
            if not self.is_real_net and NewNode.is_real_net:
                self.is_real_net = 1
                self.children = []
            return True

        if self.is_real_net and self.net.hasSubnet(NewNode.net):
            return True

        if not self.net.hasSubnet(NewNode.net):
            return False

        for Child in self.children:
            if Child.addSubnet(NewNode):
                return True

        for i, Child in enumerate(self.children):
            CommonNet = Child.net.getCommonNet(NewNode.net, self.net.mask_size + 1)
            if CommonNet:
                CommonNode = Node(CommonNet, 0)
                CommonNode.addSubnet(NewNode)
                CommonNode.addSubnet(Child)
                self.children[i] = CommonNode
                return True

        self.children.append(NewNode)
        return True

    def finishTree(self):
        if self.is_real_net:
            self.real_ip_volume = self.net.ip_volume
            self.real_ip_records_count = 1
            self.weight = 0
            self.max_child_weight = 0
        else:
            self.real_ip_volume = 0
            self.real_ip_records_count = 0
            self.max_child_weight = 0
            for Child in self.children:
                Child.finishTree()
                self.real_ip_volume += Child.real_ip_volume
                self.real_ip_records_count += Child.real_ip_records_count
                self.max_child_weight = max(self.max_child_weight, Child.weight, Child.max_child_weight)
            self.recalcWeight()

    def collapse(self, min_weight, max_net_delta):
        # trying to collapse self
        if self.weight >= min_weight:
            self.weight = 0
            self.max_child_weight = 0
            delta = (self.net.ip_volume - self.real_ip_volume) - self.added_fake_ip_volume
            self.added_fake_ip_volume = self.net.ip_volume - self.real_ip_volume
            return self.real_ip_records_count - 1, delta

        net_delta = 0
        fake_ip_delta = 0
        self.max_child_weight = 0
        for Child in self.children:
            if net_delta < max_net_delta and min_weight <= max(Child.weight, Child.max_child_weight):
                child_net_delta, child_fake_ip_count = Child.collapse(min_weight, max_net_delta - net_delta)
                net_delta += child_net_delta
                fake_ip_delta += child_fake_ip_count
            self.max_child_weight = max(self.max_child_weight, Child.weight, Child.max_child_weight)

        if net_delta > 0:
            self.added_fake_ip_volume += fake_ip_delta
            self.real_ip_records_count -= net_delta
            self.recalcWeight()

        # trying to collapse self
        if self.weight >= min_weight:
            self.weight = 0
            self.max_child_weight = 0
            delta = (self.net.ip_volume - self.real_ip_volume) - (self.added_fake_ip_volume - fake_ip_delta)
            self.added_fake_ip_volume = self.net.ip_volume - self.real_ip_volume
            return self.real_ip_records_count - 1, delta
        else:
            return net_delta, fake_ip_delta

    def collapseRoot(self, recursive, required_net_delta):
        if recursive:
            while required_net_delta > 0:
                delta, fake_ip_volume = self.collapse(self.max_child_weight, required_net_delta)
                required_net_delta -= delta
        else:
            delta, fake_ip_volume = self.collapse(self.max_child_weight, required_net_delta)

    def printCollapsedTree(self):
        if self.is_real_net or self.weight == 0:
            print(self.net.getAsString())
        else:
            for Child in self.children:
                Child.printCollapsedTree()

    def recalcWeight(self):
        fake_ip_delta = self.net.ip_volume - self.real_ip_volume - self.added_fake_ip_volume
        if fake_ip_delta:
            self.weight = (self.real_ip_records_count - 1) / fake_ip_delta
        else:
            self.weight = float('Inf')
