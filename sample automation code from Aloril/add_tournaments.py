#!/usr/bin/env python3
import sys, os.path, argparse

TOP_MARKER = "lczero10_KEEP-TOP:nodes:1000 sf9:nodes:10000000 1000\n"

def iterate_new_net(test_flag):
    directory_lst = ("./", "2/", "3/", "4/", "5/", "6/")
    for directory in directory_lst:
        if test_flag:
            new_net_filename = directory + "new_net_test%s.lst" % test_flag
        else:
            new_net_filename = directory + "new_net.lst"
        if not os.path.exists(new_net_filename):
            continue
        yield new_net_filename

if __name__=="__main__":
    parser = argparse.ArgumentParser(description="Add tournaments")
    parser.add_argument('weights', nargs='+', help="weights for which tournaments are added")
    parser.add_argument('-s', '--stdout', help="output to console", action='store_const', const=True, default=False)
    parser.add_argument('-t', '--test', help="test net", type=str, default="")
    args = parser.parse_args()
    if args.stdout:
        for new_net_filename in iterate_new_net(args.test):
            for line in open(new_net_filename):
                for net_id in args.weights:
                    print(line % locals(), end="")
    else:
        for net_id in args.weights:
            for new_net_filename in iterate_new_net(args.test):
                new_tournaments = open(new_net_filename).read() % locals()
                if not new_tournaments:
                    continue
                directory = os.path.dirname(new_net_filename)
                tournament_file = directory + os.sep + "tournament.lst"
                old_tournament = open(tournament_file).read()
                with open(tournament_file, "w") as fp:
                    l = old_tournament.split(TOP_MARKER)
                    if len(l)==2:
                        fp.write(l[0])
                        fp.write(TOP_MARKER)
                        fp.write(new_tournaments)
                        fp.write(l[1])
                    else:
                        fp.write(new_tournaments)
                        fp.write(old_tournament)
            print("new tournaments added for " + net_id)
