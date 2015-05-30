# CS244-15-The-Intuition-Behind-Why-a-Randomly-Networked-Data-Center-Works

There is only one file with code in it, specifically random_graph.py.  This file is set up to take in command arguments depending upon what you want to do with it.  Here is a list of the command line arguments and what they do:

-h, --help           : Displays a help message for this program with standard formatting

-k K                 : The number of ports per switch.  This determines the number of servers, switches, and links based on the
                       standard Fat-tree topology.
                       
--num_paths NUMPATHS : The number of paths to find for every server-server pair

--even               : Tells the program to distribute the servers as evenly as possible across the switches - without this flag
                       the program distributes the servers randomly among the switches.

--gen_graph          : Tells the program to generate a new graph to use for the computation and save it at <type>-graph-k<k>.txt
                       where type is even or random depending upon whether the --even flag is set, and k is the value in k -
                       without this flag the program uses the graph already saved at that location

--use_flow           : Tells the program to use the estimated throughput through each link as a metric instead of the paths/link

--gen_stats          : Tells the program to generate new paths/link stats for the computation and save it at
                       <type>-graph-k<k>-<flow_type>-stats<Algo>.txt where type is even or random depending upon the --even
                       flag, k is the value stored at k, flow_type is either paths or flow depending upon the use_flow flag, and
                       Algo is either K or ECMP depending upon whether the stats are for the K-shortest paths or ECMP algorithm
                       (note that one run of the program generates stats for both K shortest paths and ECMP) -
                       without this flag the program just reads the stats from the file at the above location

--scale              : Tells the program whether to scale the paths/link by the total amount of paths/link in the graph for the
                       generated plot.  Note that --use_flow and --scale cannot be used together since the throughput metric is
                       already designed to give an accurate distribution of bytes, which doesn't depend on scaling.

All you need to do to run the program is select what parameters you want to send to random_graph.py and run it.
