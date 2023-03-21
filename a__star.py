import json
import heapq
import math
import gpt_generated_graph

graph = json.loads(open('gpt_generated_graph.json').read())



# Define a function to calculate the heuristic value between two points
def heuristic(point_a, point_b):
    location = json.loads(open('bus_stops_to_coordinates.json').read())
    a_loc = location[point_a].split(", ")
    b_loc = location[point_b].split(", ")
    return gpt_generated_graph.haversine(float(a_loc[0]),float(a_loc[1]),float(b_loc[0]),float(b_loc[1]))

# Define the A* algorithm function
def astar(graph, start, goal):
    # Initialize the frontier and explored sets
    frontier = [(0, start)]
    explored = set()


    # Initialize the path and cost dictionaries
    path = {}
    cost = {}
    path[start] = None
    cost[start] = 0


    # Start the search loop
    while frontier:
        # Get the node with the lowest f-cost from the frontier
        f, current_node = heapq.heappop(frontier)
        # If the current node is the goal node, return the path
        if current_node == goal:
            final_path = []
            while current_node:
                final_path.append(current_node)
                current_node = path[current_node]
            return final_path[::-1]
        # Add the current node to the explored set
        explored.add(current_node)


        # Check each neighbor of the current node
        for neighbor, list in graph[current_node].items():
            for values in list:
                cost_to_neighbor = values["Weight"]
            # Calculate the g-cost to reach the neighbor
                tentative_g_cost = cost[current_node] + cost_to_neighbor
            # If the neighbor is already explored and the tentative cost is higher, skip it
            if neighbor in explored and tentative_g_cost >= cost.get(neighbor, float('inf')):
                continue
            # If the neighbor is not in the frontier or the tentative cost is lower than the existing cost, add it to the frontier
            if tentative_g_cost < cost.get(neighbor, float('inf')):
                cost[neighbor] = tentative_g_cost
                f_cost = tentative_g_cost + heuristic(neighbor, goal)
                heapq.heappush(frontier, (f_cost, neighbor))
                path[neighbor] = current_node
    # If the frontier is empty and the goal has not been found, return None
    return None



start = "bef Jalan Masai Baru"
end = "Opp Kia Motors"
path = astar(graph, start, end)
print(path)

# point_a = "bef Jalan Masai Baru"
# point_b = "Opp Kia Motors"
# print(heuristic(point_a,point_b))

# for neighbour, list in graph[start].items():
#     for values in list:
#         print(values["Weight"])