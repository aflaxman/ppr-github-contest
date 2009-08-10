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

from networkx import *
from ppr import ppr


G = Graph()


# load the (user,repo)-pairs
f = open('download/data.txt')
for l in f:
    u_id, r_id = l.strip().split(':')
    G.add_edge('user_%s' % u_id, 'repo_%s' % r_id)


# make a prediction for each user
f = open('download/test.txt')
f_out = open('results.txt', 'w')

for l in f:
    # calculate the ppr for each test user
    u_id = l.strip()
    node_pr = ppr(G, {'user_%s' % u_id: 1.})
    print u_id,
    stdout.flush()

    top_ten = sorted(node_pr,
                     key=lambda x: (x.find('repo') != -1) and node_pr[x],
                     reverse=True)[0:10]

    # save the predictions
    f_out.write('%s:%s' % (u_id, ','.join(top_ten)))
    f_out.flush()
    print top_ten
    
f_out.close()