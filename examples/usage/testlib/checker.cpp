#include "testlib.h"
#include <vector>
#include <set>
#include <utility>
#include <algorithm>

using namespace std;

bool hasConflicts(const vector<int>& frequencies, const vector<vector<int>>& adj) {
    int n = frequencies.size() - 1;
    for (int i = 1; i <= n; i++) {
        for (int neighbor : adj[i]) {
            if (i < neighbor) { // Check each edge only once
                if (frequencies[i] == frequencies[neighbor]) {
                    return true;
                }
            }
        }
    }
    return false;
}

int main(int argc, char *argv[]) {
    registerTestlibCmd(argc, argv);

    // Read input data
    int n = inf.readInt();
    int k = inf.readInt();
    int l = inf.readInt();

    // Read initial frequencies
    vector<int> initial_freq(n + 1);
    for (int i = 1; i <= n; i++) {
        initial_freq[i] = inf.readInt();
    }

    // Read tower connections as adjacency list
    vector<vector<int>> adj(n + 1);
    for (int i = 0; i < n - 1; i++) {
        int a = inf.readInt();
        int b = inf.readInt();
        adj[a].push_back(b);
        adj[b].push_back(a);
    }

    // Read participant's output
    int participant_changes = ouf.readInt();
    
    // Read the participant's final frequencies
    vector<int> participant_freq(n + 1);
    for (int i = 1; i <= n; i++) {
        participant_freq[i] = ouf.readInt();
    }

    // Read jury's output for reference (minimal number of changes)
    int jury_changes = ans.readInt();
    
    // Read jury's solution frequencies to verify its correctness
    vector<int> jury_freq(n + 1);
    for (int i = 1; i <= n; i++) {
        jury_freq[i] = ans.readInt();
    }

    // Verify jury's solution is correct
    for (int i = 1; i <= n; i++) {
        if (jury_freq[i] < k || jury_freq[i] > l) {
            quitf(_fail, "Jury's solution: Frequency for tower %d is outside the valid range [%d, %d]", i, k, l);
        }
        
        int diff = abs(jury_freq[i] - initial_freq[i]);
        if (diff > 1) {
            quitf(_fail, "Jury's solution: Tower %d frequency was changed by %d, which exceeds the allowed +/-1", i, diff);
        }
    }
    
    // Verify jury's solution has no conflicts
    if (hasConflicts(jury_freq, adj)) {
        quitf(_fail, "Jury's solution still has frequency conflicts");
    }
    
    // Verify jury's actual changes match their reported changes
    int jury_actual_changes = 0;
    for (int i = 1; i <= n; i++) {
        if (jury_freq[i] != initial_freq[i]) {
            jury_actual_changes++;
        }
    }
    
    if (jury_actual_changes != jury_changes) {
        quitf(_fail, "Jury's solution: Reported %d changes, but actually performed %d changes", 
              jury_changes, jury_actual_changes);
    }

    // Check 1: Verify that all frequencies are within the valid range [K, L]
    for (int i = 1; i <= n; i++) {
        if (participant_freq[i] < k || participant_freq[i] > l) {
            quitf(_wa, "Frequency for tower %d is outside the valid range [%d, %d]", i, k, l);
        }
    }

    // Check 2: Verify that each tower's frequency was changed by at most +/-1
    int actual_changes = 0;
    for (int i = 1; i <= n; i++) {
        int diff = abs(participant_freq[i] - initial_freq[i]);
        if (diff > 1) {
            quitf(_wa, "Tower %d frequency was changed by %d, which exceeds the allowed +/-1", i, diff);
        }
        if (diff > 0) {
            actual_changes++;
        }
    }

    // Check 3: Verify that the reported number of changes matches the actual changes
    if (actual_changes != participant_changes) {
        quitf(_wa, "Reported %d changes, but actually performed %d changes", participant_changes, actual_changes);
    }

    // Check 4: Verify that there are no frequency conflicts among connected towers
    if (hasConflicts(participant_freq, adj)) {
        quitf(_wa, "Solution still has frequency conflicts");
    }

    // Check 5: Verify that the number of changes is minimal compared to jury's
    if (participant_changes > jury_changes) {
        quitf(_wa, "Solution is not optimal: performed %d changes, but %d is the minimal possible", 
              participant_changes, jury_changes);
    } else if (participant_changes < jury_changes) {
        // Contestant found a better solution than the jury!
        quitf(_fail, "Contestant's solution (%d changes) is better than jury's solution (%d changes)",
              participant_changes, jury_changes);
    }

    // All checks passed
    quitf(_ok, "Correct solution with %d changes", participant_changes);
}
