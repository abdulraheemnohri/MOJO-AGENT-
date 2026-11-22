# MOJO AGENT - Mojo BFS computational core starter.
# Requires a supported Modular Mojo toolchain.
from collections import List
fn bfs_distance(graph: List[List[Int]], start: Int, goal: Int) -> Int:
    var visited = List[Int]()
    var distance = List[Int]()
    var queue = List[Int]()
    for i in range(len(graph)):
        visited.append(0)
        distance.append(-1)
    if start < 0 or goal < 0 or start >= len(graph) or goal >= len(graph):
        return -1
    queue.append(start)
    visited[start] = 1
    distance[start] = 0
    var head = 0
    while head < len(queue):
        var node = queue[head]
        head += 1
        if node == goal:
            return distance[node]
        for neighbor in range(len(graph[node])):
            if graph[node][neighbor] != 0 and visited[neighbor] == 0:
                visited[neighbor] = 1
                distance[neighbor] = distance[node] + 1
                queue.append(neighbor)
    return -1
fn main():
    var graph = List[List[Int]]()
    graph.append(List[Int](0, 1, 1, 0))
    graph.append(List[Int](1, 0, 0, 1))
    graph.append(List[Int](1, 0, 0, 1))
    graph.append(List[Int](0, 1, 1, 0))
    print('MOJO AGENT core')
    print('BFS shortest distance:', bfs_distance(graph, 0, 3))
