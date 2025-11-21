#include <bits/stdc++.h>
#include "testlib.h"
using namespace std;

const int MAXN = 500'000;
const int MAXL = 1'000'000'000;

vector<int> adj[MAXN+5];
bool visited[MAXN+5] = {0};
vector<int> dfs_stack;

int main(int argc, char* argv[]) {
    registerValidation(argc, argv);

    int N = inf.readInt(2,MAXN,"N"); inf.readSpace();
    int K = inf.readInt(1,MAXL,"K"); inf.readSpace();
    int L = inf.readInt(K+1,MAXL,"L");
    inf.readEoln();

    int f1 = 0;
    for (int i=1; i<=N; i++) {
        int fi = inf.readInt(K,L,"fi"); if (i<N) {inf.readSpace();}
        if (validator.group() == "4") {
            if (i == 1) {f1 = fi;}
            else {inf.ensuref(f1 == fi, "Different frequencies");}
        }
    }
    inf.readEoln();

    for (int i=1; i<=N-1; i++) {
        int u = inf.readInt(1,N,"u"); inf.readSpace();
        int v = inf.readInt(1,N,"v");
        inf.readEoln();

        inf.ensure(u != v);

        adj[u].push_back(v);
        adj[v].push_back(u);
    }
    inf.readEof();

    dfs_stack.push_back(1);
    while (dfs_stack.size() > 0) {
        int v = dfs_stack.back();
        dfs_stack.pop_back();
        visited[v] = true;
        for (int u : adj[v]) {
            if (!visited[u]) {dfs_stack.push_back(u);}
        }
    }

    for (int i = 1; i <= N; i++) {
        inf.ensuref(visited[i], "Not a tree");
    }

	if (validator.group() == "0") {
        //inf.ensure();
    } else if (validator.group() == "1") {
        inf.ensure(N <= 10);
    } else if (validator.group() == "2") {
        inf.ensure(L == K+1);
    } else if (validator.group() == "3") {
        for (int i=1; i<=N; i++) {inf.ensure(adj[i].size() <= 2);}
    } else if (validator.group() == "4") {
        // Already checked
    } else if (validator.group() == "5") {
        // No additional constraints
    }
}
