import heapq
import json

graph = json.loads(open('gpt_generated_graph.json').read())

def dijkstra(graph, start, end, transfer_penalty):
    distances = {node: float('inf') for node in graph}
    distances[start] = 0
    visited = {}
    previous_nodes = {node: None for node in graph}
    previous_edge = {node: None for node in graph}
    previous_bus_service = {node: None for node in graph}

    heap = [(0, start)]

    while heap:
        (distance, current_node) = heapq.heappop(heap)

        if current_node == end:
            path = []
            while previous_nodes[current_node] is not None:
                path.append(current_node)
                current_node = previous_nodes[current_node]
            path.append(start)
            path.reverse()

            instructions = []
            for i in range(len(path)-1):
                from_node = path[i]
                to_node = path[i+1]
                edge = previous_edge[to_node][0]
                bus_service = edge['Bus Service']
                if previous_bus_service[from_node] is not None and previous_bus_service[from_node] != bus_service:
                    instructions.append(f"Transfer at {from_node} to {bus_service}")
                instructions.append(f"Take bus service {bus_service} from {from_node} to {to_node}")
                previous_bus_service[to_node] = bus_service
            return instructions

        visited[current_node] = True

        for neighbor, edge_info in graph[current_node].items():
            neighbor_distance = distances[current_node] + edge_info[0]['Distance']
            bus_service = edge_info[0]['Bus Service']
            if neighbor not in visited:
                if previous_bus_service[current_node] is not None and previous_bus_service[current_node] != bus_service:
                    neighbor_distance += transfer_penalty
                if neighbor_distance < distances[neighbor]:
                    distances[neighbor] = neighbor_distance
                    previous_nodes[neighbor] = current_node
                    previous_edge[neighbor] = edge_info
                    heapq.heappush(heap, (neighbor_distance, neighbor))
                    previous_bus_service[neighbor] = bus_service

    return None

start = "bef Jalan Masai Baru"
end = "Opp Kia Motors"
instructions = dijkstra(graph, start, end,5)

if instructions is not None:
    print("Shortest path instructions:")
    for instruction in instructions:
        print(instruction)
else:
    print(f"No path found from {start} to {end}.")
