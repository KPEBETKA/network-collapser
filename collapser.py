#!/usr/local/bin/python3

import re
import sys
import argparse
import tree

parser = argparse.ArgumentParser()
parser.add_argument('-f', '--file', action='store', type=str, default='')
parser.add_argument('-s', '--size', action='store', type=int, default=0)
args = parser.parse_args()

file = open(args.file, "r")
if not file:
    print('Cant open file')
    sys.exit()

lines = 0
Root = tree.Node(tree.Net(0,0), 0)

for line in file.readlines():

    result = re.search('(\d+)\.(\d+)\.(\d+)\.(\d+)(?:\/(\d+))?', line)

    if result:

        ip = 0
        for i in range(1, 5):
            ip = ip * 256 + int(result.group(i))

        mask_size = 32
        if result.group(5):
            mask_size = int(result.group(5))

        Root.addSubnet(tree.Node(tree.Net(ip, mask_size), 1))

        lines += 1

Root.finishTree()

if args.size:
    Root.collapseRoot(True, Root.real_ip_records_count - args.size)
else:
    Root.collapseRoot(False, Root.real_ip_records_count - 1)

Root.printCollapsedTree()

print('\n### File size: %d lines' % lines, file=sys.stderr)
print('### Collapse result: %d networks' % Root.real_ip_records_count, file=sys.stderr)
print('### Added unnecessary ip addresses: %d' % Root.added_fake_ip_volume, file=sys.stderr)
