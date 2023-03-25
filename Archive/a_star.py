from collections import deque
import pprint
import json

graph = json.loads(open('gpt_generated_graph.json').read())

class Graph:
    def __init__(self, adjacency_list):
        self.adjacency_list = adjacency_list
    
    def get_neighbors(self, v):
        return self.adjacency_list[v]

    def a_star_algorithm(self, start_node, end_node):
        open_set = set([start_node])
        closed_set = set()
        g = {}
        parents = {}

        g[start_node] = 0
        parents[start_node] = start_node
        while len(open_set) > 0:
            n = None
            for v in open_set:
                if n == None or g[v] < g[n]:
                    n = v
            if n == end_node or graph[n] == None:
                pass
            else:
                for (m, data) in self.get_neighbors(n).items():
                    if m not in open_set and m not in closed_set:
                        open_set.add(m)
                        parents[m] = n
                        lowest_index = 0
                        for i in range(len(data)):
                            if float(data[lowest_index]['Weight']) > float(data[i]['Weight']):
                                lowest_index = i
                        g[m] = g[n] + data[i]['Weight']
                    else:
                        if g[m] > g[n] + data[0]['Weight']:
                            g[m] = g[n] + data[0]['Weight']
                            parents[m] = n
                            if m in closed_set:
                                closed_set.remove(m)
                                open_set.add(m)
            if n == None:
                print('Path does not exist!')
                return None
            
            # if the current node is the stop_node
            # then we begin reconstructin the path from it to the start_node
            if n == end_node:
                path = []
                while parents[n] != n:
                    path.append(n)
                    n = parents[n]
                path.append(start_node)
                path.reverse()
                pprint.pprint('Path found: {}'.format(path))
                return path
            # remove n from the open_list, and add it to closed_list
            # because all of his neighbors were inspected
            open_set.remove(n)
            closed_set.add(n)
        print('Path does not exist!')
        return None

    def heuristic(a, b):
        return abs(a[0] - b[0]) + abs(a[1] - b[1])

# Graph_nodes = {
#     'A': [('B', 6), ('F', 3)],
#     'B': [('A', 6), ('C', 3), ('D', 2)],
#     'C': [('B', 3), ('D', 1), ('E', 5)],
#     'D': [('B', 2), ('C', 1), ('E', 8)],
#     'E': [('C', 5), ('D', 8), ('I', 5), ('J', 5)],
#     'F': [('A', 3), ('G', 1), ('H', 7)],
#     'G': [('F', 1), ('I', 3)],
#     'H': [('F', 7), ('I', 2)],
#     'I': [('E', 5), ('G', 3), ('H', 2), ('J', 3)],
# }

graph_2 = Graph(graph)
graph_2.a_star_algorithm('Kulai Terminal', 'Senai Airport Terminal')
