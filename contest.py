# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.

# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

# Copyright 2009 Abraham Flaxman

from sys import stdout
import time
import random

from numpy import arange, log, ones
from networkx import *
from ppr import ppr



# if holdout is true, don't use the test.txt users, and instead
# remove random known edges, for testing purposes
holdout = True
num_to_holdout = 10
num_to_predict = 10  # ten for contest, possibly more for testing
notes = 'G = undirected users <-> repos, directed repos <-> forked repos, undirected repos <-> language'

user_repo_wt = 1.
repo_user_wt = 1.
user_user_wt = .1
repo_fork_wt = .5
fork_repo_wt = 2.
repo_owner_wt = 1.
owner_repo_wt = 1.
repo_lang_wt = .1
lang_repo_wt = .1

# alpha = .4  # ppr 1-reset probability
# loop through a range of alphas
for alpha in arange(.15, .5, .05):
#for alpha in [.3]:
    G = LabeledDiGraph()
    G.users = []
    G.repos = []

    # convenience functions for node names
    user = lambda x: 'user_%s' % str(x)
    repo = lambda x: 'repo_%s' % str(x)

    # load the (user,repo)-pairs
    f = open('download/data.txt')
    for l in f:
        u_id, r_id = l.strip().split(':')
        G.add_edge(user(u_id), repo(r_id), user_repo_wt)
        G.add_edge(repo(r_id), user(u_id), repo_user_wt)
        
        G.users.append(user(u_id))
        G.repos.append(repo(r_id))


    # load the users to  make predictions for
    f = open('download/test.txt')
    real_test_id_list = [u.strip() for u in f]


    # find core graph
    print 'finding core'
    nbunch = [n for n in G if len(G[n]) <= 1 and n.replace('user_','') not in real_test_id_list]
    while len(nbunch) > 0:
        G.delete_nodes_from(nbunch)
        nbunch = [n for n in G if len(G[n]) <= 1 and n.replace('user_','') not in real_test_id_list]


    # if holdout is true, don't use the test.txt users, and instead
    # remove random known edges, for testing purposes
    if holdout:
        print 'removing edges for validation'
        test_id_list = []
        test_holdout = {}
        for u_id in [i for i in random.sample(range(50000), 1000)]:
            u = user(u_id)

            # only holdout edges for users that are are watching at least
            # 10 repos in the core
            if not G.has_node(user(u_id)) or len(G[u]) < 10:
                continue

            # don't holdout edges for users that are in the real test set
            if u_id in real_test_id_list:
                continue

            holdout_set = set(random.sample(G[u], num_to_holdout))
            for r in holdout_set:
                G.remove_edge(u,r)

            test_id_list.append(str(u_id))
            test_holdout[u] = holdout_set
        total_predicted = 0
    else:
        test_id_list = real_test_id_list


    # add edges between users with same rare tastes
    print 'connecting users who are only 2 watching same repo together'
    for u in [n for n in G if n.find('user') != -1]:
        for r in G[u].keys():
            if len(G[r]) == 2:
                u, v = G[r].keys()
                G.add_edge(u, v, user_user_wt)
                G.add_edge(v, u, user_user_wt)


    # add edges between repos that are forks
    # This file lists out the 120,867 repositories that are used in the data.txt
    # set, providing the repository name, date it was created and (if applicable)
    # the repository id that it was forked off of.  The data looks like this:
    #   123335:seivan/portfolio_python,2009-02-18,53611
    #   123336:sikanrong/Nautilus-OGL,2009-05-19

    print 'adding edges between forked repos'
    f = open('download/repos.txt')
    owned_by = {}
    for l in f:
        r_id, r_desc = l.strip().split(':')

        u = r_desc.split('/')[0]
        if not owned_by.has_key(u):
            owned_by[u] = []
        owned_by[u].append(repo(r_id))
        
        r_desc = r_desc.split(',')
        # add edge from repo to repo it forked from
        if len(r_desc) == 3:
            G.add_edge(repo(r_id), repo(r_desc[2]), fork_repo_wt)
            G.add_edge(repo(r_desc[2]), repo(r_id), repo_fork_wt)

    # add star on all repos owned by same user
    for ii, u in enumerate(owned_by.keys()):
        if len(owned_by[u]) > 1:
            o = 'owner_%d' % ii
            for r in owned_by[u]:
                G.add_edge(o, r, owner_repo_wt)
                G.add_edge(r, o, repo_owner_wt)


    # add edges from repo to language and size
    # The last dataset included is the language breakdown data. The data
    # looks like this:
    #   57493:C;29382
    #   73920:JavaScript;9759,ActionScript;12781
    print 'adding edges between repos and languages and sizes'
    f = open('download/lang.txt')
    for l in f:
        r_id, r_desc = l.strip().split(':')
        lang_size_list = [ls.split(';') for ls in r_desc.split(',')]
        lang_list = ['language_%s' % ls[0] for ls in lang_size_list]
        size_list = ['size_%d' % int(log(max(1., float(ls[1])))) for ls in lang_size_list]

        for lang in lang_list:
            G.add_edge(repo(r_id), lang, repo_lang_wt)
            G.add_edge(lang, repo(r_id), lang_repo_wt)
        #G.add_star([repo(r_id)] + size_list, ones(len(lang_list)))


    # make predictions for each user on the user list
    print 'making predictions for %d users' % len(test_id_list)
    print 'alpha = %f' % alpha
    f = open('results.txt', 'w')
    for ii, u_id in enumerate(test_id_list):
        start_time = time.time()
        u = 'user_%s' % u_id

        if not G.has_node(u):
            continue

        # calculate the ppr for each test user
        print '\n', u
        stdout.flush()
        #node_pr = ppr(G, {u: 1.}, alpha, nstart=pr)
        node_pr = ppr(G, {u: 1.}, alpha)


        # make the predictions
        ordered_repos = sorted([r for r in node_pr if r.find('repo') != -1 and not G.has_edge(u, r)],
                               key=lambda x: node_pr[x],
                               reverse=True)
        top_ids = [r.replace('repo_', '') for r in ordered_repos[0:num_to_predict]]


        # save the predictions
        f.write('%s:%s\n' % (u_id, ','.join(top_ids)))
        f.flush()
        print top_ids


        # if there is a hold out set, use it to check prediction accuracy
        if holdout:
            holdout_set = test_holdout[u]
            num_predicted = len(set(ordered_repos[0:10]) & holdout_set)
            print '%d of hold-out set %s predicted' % (num_predicted, str(sorted(holdout_set)))
            total_predicted += num_predicted
            print '%.2fpct correct so far' % (100 * total_predicted / float(ii * num_to_holdout))
        print 'elapsed time: %ds' % (time.time() - start_time)
    f.close()

    if holdout:
        total_holdout = len(test_id_list) * num_to_holdout
        frac_predicted = float(total_predicted) / total_holdout
        print 'predicted %d of %d (%.2fpct)' % (total_predicted, total_holdout, frac_predicted*100)
        f = open('metrics.csv', 'a')
        f.write('%f,%f,%d,%d,%d,%d,%s\n' % (alpha, frac_predicted, total_predicted, total_holdout, num_to_predict, num_to_holdout, notes))
        f.close()
