# Network Collapser
a tool to combine networks list to desired size with the best possible accuracy

## How it works
* We build a binary tree out of all the nets in passed list. Finding the smallest common nets and creating fake net nodes.
* Then we calculate weight for all the nets. Weight is as bigger as much we can reduce the list size if we collapse the net. And as lower as many bad IPs are covered by that net.
* Then we recursively collapse nets starting from those who has the biggest weight (the biggest weight is infinity) until we have desired list size.

The difficult thing is that weight of the parent nets is changed when we collapse it's child.

Based on original idea and codebase [net_list_minimizer](https://github.com/phoenix-mstu/net_list_minimizer) of @phoenix-mstu

## How to run
* For collapse network list without adding unnecessary ip addresses
`python3 collapser.py -f example.txt > result.txt`
* For collapse network list until desired list size
`python3 collapser.py -f example.txt -s 30000 > result.txt`
