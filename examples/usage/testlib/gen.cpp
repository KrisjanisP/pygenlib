#include "testlib.h"
#include <iostream>
#include <vector>
#include <algorithm>
#include <string>
#include <queue>
#include <set>
#include <map>
#include <random>
#include <cassert>

using namespace std;

// Generate a tree of n vertices with the specified type
vector<pair<int, int>> generateTree(int n, const string& type) {
    vector<pair<int, int>> edges;
    
    if (type == "star") {
        // Star tree: one central node connected to all others
        for (int i = 2; i <= n; i++) {
            edges.push_back({1, i});
        }
    } else if (type == "line") {
        // Line tree: vertices in a single line
        for (int i = 1; i < n; i++) {
            edges.push_back({i, i + 1});
        }
    } else if (type == "binary") {
        // Binary tree: each node has at most 2 children
        for (int i = 2; i <= n; i++) {
            int parent = (i / 2);
            edges.push_back({parent, i});
        }
    } else if (type == "random") {
        for (int i = 2; i <= n; i++) {
            int j = rnd.next(1, i - 1);
            edges.push_back({j, i});
        }
    } else {
        throw runtime_error("Unknown tree type: " + type);
    }
    
    return edges;
}

// Shuffle the vertices of the tree
vector<pair<int, int>> shuffleTree(const vector<pair<int, int>>& tree, int n) {
    vector<int> perm(n + 1);
    for (int i = 1; i <= n; i++) {
        perm[i] = i;
    }
    
    shuffle(perm.begin() + 1, perm.end());
    
    vector<pair<int, int>> shuffled_tree;
    for (auto [u, v] : tree) {
        shuffled_tree.push_back({perm[u], perm[v]});
    }
    
    return shuffled_tree;
}

// Assign frequencies to vertices
vector<int> assignFrequencies(int n, int l, int r, const string& way, const vector<pair<int, int>>& tree) {
    vector<int> frequencies(n + 1);
    
    if (way == "random") {
        // Random frequencies in range [l, r]
        for (int i = 1; i <= n; i++) {
            frequencies[i] = rnd.next(l, r);
        }
    } else if (way == "walk") {
        // Incremental walk algorithm
        vector<vector<int>> adj(n + 1);
        for (auto [u, v] : tree) {
            adj[u].push_back(v);
            adj[v].push_back(u);
        }
        
        vector<bool> visited(n + 1, false);
        queue<int> q;
        
        // Start from a random vertex with random frequency
        int start = rnd.next(1, n);
        frequencies[start] = rnd.next(l, r);
        visited[start] = true;
        q.push(start);
        
        // Random direction (increment or decrement)
        bool increment = rnd.next(0, 1) == 1;
        
        while (!q.empty()) {
            int u = q.front();
            q.pop();
            
            for (int v : adj[u]) {
                if (!visited[v]) {
                    visited[v] = true;
                    
                    // Determine next frequency
                    if (increment) {
                        frequencies[v] = frequencies[u] + 1;
                        if (frequencies[v] > r) {
                            frequencies[v] = frequencies[u];
                            increment = false;
                        }
                    } else {
                        frequencies[v] = frequencies[u] - 1;
                        if (frequencies[v] < l) {
                            frequencies[v] = frequencies[u];
                            increment = true;
                        }
                    }
                    
                    q.push(v);
                }
            }
        }
    } else if (way == "same") {
        // All frequencies are the same (for subtask 5)
        int freq = rnd.next(l, r);
        for (int i = 1; i <= n; i++) {
            frequencies[i] = freq;
        }
    } else {
        throw runtime_error("Unknown frequency assignment method: " + way);
    }
    
    return frequencies;
}

int main(int argc, char* argv[]) {
    registerGen(argc, argv, 1);
    
    // Parse command line arguments
    int n = atoi(argv[1]);  // Number of vertices
    int l = atoi(argv[2]);  // Min frequency
    int r = atoi(argv[3]);  // Max frequency
    string tree_type = argv[4];  // Type of tree
    string freq_way = argv[5];   // Way to assign frequencies
    int L = atoi(argv[6]); // lower bound on frequency
    int R = atoi(argv[7]); // upper bound on frequency

    
    // Generate tree
    vector<pair<int, int>> tree = generateTree(n, tree_type);
    
    // Shuffle vertices
    tree = shuffleTree(tree, n);
    
    // Assign frequencies
    vector<int> frequencies = assignFrequencies(n, l, r, freq_way, tree);

    cout<<n<<" "<<L<<" "<<R<<endl;
    
    // Output frequencies
    for (int i = 1; i <= n; i++) {
        cout << frequencies[i] << (i < n ? " " : "\n");
    }
    
    // Output edges
    for (auto [u, v] : tree) {
        cout << u << " " << v << endl;
    }
    
    return 0;
}
