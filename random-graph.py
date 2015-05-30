import random
from collections import deque
import matplotlib.pyplot as plt
import time
import argparse
import sys

parser = argparse.ArgumentParser(description='Generate a random network graph and calculate the number of flows that go through every link.')
parser.add_argument('-k', dest='k', type=int, default=14, help='The number of ports per switch.  This determines the number of servers and switches based on the fat-tree architecture.')
parser.add_argument('--num_paths', dest='numPaths', type=int, default=8, help='The number of paths to find through the graph between every pair of servers')

# Different options for the program
parser.add_argument('--even', dest='even', action='store_true', help='Make the servers evenly distributed among the switches')
parser.add_argument('--gen_graph', dest='genGraph', action='store_true', help='Generate a new graph to analyze')
parser.add_argument('--gen_stats', dest='genStats', action='store_true', help='Generate and store new flows/link stats instead of using the provided stats')
parser.add_argument('--use_flow', dest='useFlow', action='store_true', help='Calculate the amount of flow per link as opposed to simply the number of paths.')
parser.add_argument('--scale', dest='scale', action='store_true', help='Scale the stats by the total amount before generating the graph')

args = parser.parse_args()

if (args.useFlow and args.scale):
    print 'The total amount of flow for k-shortest paths and ECMP is the same - scaling doesn\'t do anything.'
    sys.exit()

class Edge:
    def __init__(self):
        self.leftNode = None
        self.rightNode = None
        self.pathsLeft = 0.0
        self.pathsRight = 0.0

    def remove(self):
        self.leftNode.edges.remove(self)
        self.rightNode.edges.remove(self)
        self.leftNode = None
        self.rightNode = None

class Node:
    def __init__(self, id):
        self.edges = []
        self.visited = False
        self.id = id

    def addEdge(self, node):
        edge = Edge()
        edge.leftNode = self
        edge.rightNode = node
        self.edges.append(edge)
        node.edges.append(edge)
        return edge

    def isNeighbor(self, node):
        for edge in self.edges:
            if (edge.leftNode == node or edge.rightNode == node):
                return True
        return False

class Path:
    def __init__(self, start, edges, end):
        self.start = start
        self.edges = edges
        self.end = end

class RandomGraph:
    def __init__(self, file=None, numServers=686, numSwitches=245, numPorts=14):
        if (file is None):
            self.genGraph(numServers, numSwitches, numPorts)
        else:
            self.readGraph(file)

    def genGraph(self,numServers,numSwitches,numPorts):
        while (True):
            print 'Creating Servers'
            idNum = 0
            self.servers = []
            for i in xrange(int(numServers)):
                self.servers.append(Node(idNum))
                idNum += 1
            print 'Creating Switches'
            self.switches = []
            remainingSwitches = []
            for i in xrange(numSwitches):
                self.switches.append(Node(idNum))
                remainingSwitches.append(self.switches[len(self.switches)-1])
                idNum += 1

            print 'Adding Server Links'
            for server in self.servers:
                switchNum = random.randint(0,len(remainingSwitches)-1)
                if (args.even):
                    switchNum = server.id % len(remainingSwitches)
                server.addEdge(remainingSwitches[switchNum])
                if (len(remainingSwitches[switchNum].edges) >= numPorts):
                    remainingSwitches.remove(remainingSwitches[switchNum])

            print 'Adding Switch Links'
            edges = []
            while (len(remainingSwitches) > 1 and
                   self.isNotFullyConnected(remainingSwitches)):
                firstSwitchNum = random.randint(0,len(remainingSwitches)-1)
                secSwitchNum = random.randint(0,len(remainingSwitches)-2)
                if (secSwitchNum >= firstSwitchNum):
                    secSwitchNum += 1

                firstSwitch = remainingSwitches[firstSwitchNum]
                secSwitch = remainingSwitches[secSwitchNum]
                if (firstSwitch.isNeighbor(secSwitch)):
                    continue

                edge = firstSwitch.addEdge(secSwitch)
                edges.append(edge)
                if (len(firstSwitch.edges) >= numPorts):
                    remainingSwitches.remove(firstSwitch)
                if (len(secSwitch.edges) >= numPorts):
                    remainingSwitches.remove(secSwitch)

            print 'Reconnecting the remaining switches'
            while (len(remainingSwitches) > 0):
                switchNum = random.randint(0, len(remainingSwitches)-1)
                switch = remainingSwitches[switchNum]

                edge = edges[random.randint(0, len(edges)-1)]

                if (switch.isNeighbor(edge.leftNode) or
                    switch.isNeighbor(edge.rightNode)):
                    continue

                switch.addEdge(edge.leftNode)
                switch.addEdge(edge.rightNode)
                edge.remove()
                if (len(switch.edges) >= numPorts):
                    remainingSwitches.remove(switch)
                    
            print 'Checking for Connectivity'
            nodes = []
            nodes.append(self.servers[0])
            self.servers[0].visited = True
            nodes = deque(nodes)
            numNodes = 1
            while (len(nodes) > 0):
                node = nodes.popleft()
                for edge in node.edges:
                    if (not edge.leftNode.visited):
                        edge.leftNode.visited = True
                        nodes.append(edge.leftNode)
                        numNodes += 1
                    if (not edge.rightNode.visited):
                        edge.rightNode.visited = True
                        nodes.append(edge.rightNode)
                        numNodes += 1

            for server in self.servers:
                server.visited = False
            for switch in self.switches:
                switch.visited = False

            if (numNodes != numServers+numSwitches):
                print 'Graph is not connected - Restarting'
                continue

            print 'Checking number of edges'
            numEdgesCorrect = True
            for server in self.servers:
                if (len(server.edges) != 1):
                    numEdgesCorrect = False
            for switch in self.switches:
                if (len(switch.edges) > numPorts):
                    numEdgesCorrect = False
            
            if (not numEdgesCorrect):
                print 'Number of edges is wrong - restarting'
                continue

            print 'All checks passed - finished generation'
            break

    def isNotFullyConnected(self, nodes):
        for i in xrange(len(nodes)):
            for j in xrange(len(nodes)):
                if (not nodes[i].isNeighbor(nodes[j])):
                    return True
        return False

    def printGraph(self, file):
        f = open(file, 'w')
        f.write('%d\n' % (len(self.servers)))
        f.write('%d\n' % (len(self.switches)))
        f.write('\n')

        print 'Printing servers'
        for server in self.servers:
            for edge in server.edges:
                if (server == edge.leftNode):
                    f.write('%d %d\n' % (edge.leftNode.id, edge.rightNode.id))

        print 'Printing switches'
        for switch in self.switches:
            for edge in switch.edges:
                if (switch == edge.leftNode):
                    f.write('%d %d\n' % (edge.leftNode.id, edge.rightNode.id))
        f.close()

    def readGraph(self, file):
        f = open(file, 'r')
        lines = f.readlines()
        f.close()
        numServers = int(lines[0])
        numSwitches = int(lines[1])
        lines.remove(lines[0])
        lines.remove(lines[0])
        lines.remove(lines[0])

        print 'Creating servers'
        idNum = 0
        nodes = []
        self.servers = []
        for i in xrange(int(numServers)):
            node = Node(idNum)
            self.servers.append(node)
            nodes.append(node)
            idNum += 1
        print 'Creating Switches'
        self.switches = []
        for i in xrange(numSwitches):
            node = Node(idNum)
            self.switches.append(node)
            nodes.append(node)
            idNum += 1

        print 'Reading Edges'
        for line in lines:
            ends = line.split(' ')
            nodes[int(ends[0])].addEdge(nodes[int(ends[1])])
        print 'Done reading in graph'

    def findPaths(self, source, sink, useECMP=False, numPaths=8):
        paths = []
        count = []
        for i in xrange(len(self.servers)+len(self.switches)):
            count.append(0)

        currPaths = []
        currPaths.append(Path(source, [], source))
        numSearched = 0
        while (len(currPaths) > 0 and count[sink.id] < numPaths):
            shortestPath = None
            for path in currPaths:
                if (shortestPath is None or
                    len(path.edges) < len(shortestPath.edges)):
                    shortestPath = path

            #if (numSearched % 500 == 0):
                #print 'NumSearched: %d, Num Paths: %d' % (numSearched, len(currPaths))
            numSearched += 1
            
            currPaths.remove(shortestPath)
            count[shortestPath.end.id] += 1
            if (shortestPath.end == sink and
                (not useECMP or len(paths) == 0 or
                 len(paths[0].edges) == len(shortestPath.edges))):
                paths.append(shortestPath)

            if (count[shortestPath.end.id] <= numPaths):
                for edge in shortestPath.end.edges:
                    nextNode = edge.leftNode
                    if (shortestPath.end == nextNode):
                        nextNode = edge.rightNode

                    hasLoop = False
                    for tempEdge in shortestPath.edges:
                        if (nextNode == tempEdge.leftNode or
                            nextNode == tempEdge.rightNode):
                            hasLoop = True
                            break
                    
                    if (not hasLoop):
                        newPath = list(shortestPath.edges)
                        newPath.append(edge)
                        currPaths.append(Path(source,newPath,nextNode))

        return paths

    def fillOutTraffic(self, useECMP=False, numPaths=8):
        remainingServers = list(self.servers)

        for fromServer in self.servers:
            toServer = fromServer
            while (toServer == fromServer):
                toServerNum = random.randint(0,len(remainingServers)-1)
                if (len(remainingServers) == 2):
                    if (remainingServers[0].id + 1 == len(self.servers)):
                        toServerNum = 0
                    if (remainingServers[1].id + 1 == len(self.servers)):
                        toServerNum = 1
                toServer = remainingServers[toServerNum]

            startTime = time.time()
            paths = self.findPaths(fromServer, toServer, useECMP, numPaths)
            endTime = time.time()

            print 'Seconds per Path: %d' % (endTime-startTime)

            print 'Num Paths: %d -> %d: %d' % (fromServer.id, toServer.id, len(paths))

            increment = 1.0
            if (args.useFlow):
                increment = (1.0/(float(len(paths))))

            for path in paths:
                currentNode = fromServer
                for edge in path.edges:
                    if (currentNode == edge.leftNode):
                        edge.pathsRight += increment
                        currentNode = edge.rightNode
                    elif (currentNode == edge.rightNode):
                        edge.pathsLeft += increment
                        currentNode = edge.leftNode

            remainingServers.remove(toServer)

    def genStats(self):
        pathNums = []
        for switch in self.switches:
            for edge in switch.edges:
                if (switch == edge.leftNode):
                    pathNums.append(edge.pathsLeft)
                    pathNums.append(edge.pathsRight)

        pathNums.sort()
        return pathNums
        
def genGraph(file, numServers=686, numSwitches=245, numPorts=14):
    graph = RandomGraph(numServers=numServers,numSwitches=numSwitches,
                        numPorts=numPorts)
    graph.printGraph(file)
    return graph

def printList(file, list):
    f = open(file, 'w')

    print 'Printing List'
    for elem in list:
        f.write('%f\n' % (elem))
    f.close()

def readList(file):
    f = open(file, 'r')

    print 'Reading List'
    list = []
    for line in f:
        list.append(float(line))
    f.close()
    return list

def scaleStats(stats):
    total = 0.0
    for elem in stats:
        total += elem

    newStats = []
    for elem in stats:
        newStats.append(elem/total)
    return newStats

graph_type = 'random'
if (args.even):
    graph_type = 'even'
desc = '%s-graph-k%d' % (graph_type, args.k)

graph_filename = '%s.txt' % (desc)

if (args.genGraph):
    genGraph(graph_filename, numServers=((args.k**3)/4), numSwitches=int(((5.0/4.0)*(args.k**2))), numPorts=args.k)

statsFile = '%s-paths' % (desc)
if (args.useFlow):
    statsFile = '%s-flow' % (desc)

if (args.genStats):
    graphK = RandomGraph(graph_filename)
    graphK.fillOutTraffic(useECMP=False, numPaths=args.numPaths)
    statsK = graphK.genStats()
    printList('%s-statsK.txt' % (statsFile), statsK)
    graphECMP = RandomGraph(graph_filename)
    graphECMP.fillOutTraffic(useECMP=True, numPaths=args.numPaths)
    statsECMP = graphECMP.genStats()
    printList('%s-statsECMP.txt' % (statsFile), statsECMP)

statsK = readList('%s-statsK.txt' % (statsFile))
statsECMP = readList('%s-statsECMP.txt' % (statsFile))

scaled = 'non-scaled'
if (args.scale):
    statsK = scaleStats(statsK)
    statsECMP = scaleStats(statsECMP)
    scaled = 'scaled'

usePaths = 'paths'
if (args.useFlow):
    usePaths = 'flow'

plt.figure()
plt.plot(range(len(statsK)), statsK, color='b', label="K Shortest Paths")
plt.plot(range(len(statsECMP)), statsECMP, color='g', label="ECMP")
plt.title("CDF of # of paths through links")
plt.xlabel('Rank of Link')
yLabel = ''
if (args.scale):
    if (args.useFlow):
        yLabel = 'Amount of flow through link (Scaled by total amount of flow)'
    else:
        yLabel = '# of Distinct Paths link is on (Scaled by total number of paths)'
else:
    if (args.useFlow):
        yLabel = 'Amount of flow through link'
    else:
        yLabel = '# of Distinct Paths link is on'
plt.ylabel(yLabel)
plt.legend()
plt.savefig('%s-%s-%s-plot.png' % (scaled, desc, usePaths))
