import random
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

# Action definition:
# 0: Up (-1, 0)
# 1: Right (0, 1)
# 2: Down (1, 0)
# 3: Left (0, -1)
ACTION_DELTAS = {
    0: (-1, 0),
    1: (0, 1),
    2: (1, 0),
    3: (0, -1)
}

class GridWorld:
    def __init__(self, n, start, end, obstacles):
        self.n = n
        self.start = tuple(start) if start else None
        self.end = tuple(end) if end else None
        self.obstacles = set(tuple(obs) for obs in obstacles)
        self.gamma = 0.9
        self.reward = -1 # step penalty
        
    def get_next_state(self, state, action):
        r, c = state
        if state == self.end:
            return state # Terminal state absorbs
            
        dr, dc = ACTION_DELTAS[action]
        next_r, next_c = r + dr, c + dc
        
        # Check boundary
        if next_r < 0 or next_r >= self.n or next_c < 0 or next_c >= self.n:
            return state # hit wall
            
        # Check obstacle
        if (next_r, next_c) in self.obstacles:
            return state # hit obstacle
            
        return (next_r, next_c)
        
    def get_reward(self, state, action, next_state):
        if state == self.end:
            return 0 # No penalty when absorbing at terminal
        return self.reward

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/random_policy', methods=['POST'])
def random_policy():
    data = request.json
    n = data.get('n', 5)
    end = tuple(data.get('end', [-1,-1]))
    obstacles = set(tuple(obs) for obs in data.get('obstacles', []))
    
    policy = {}
    for r in range(n):
        for c in range(n):
            state = (r, c)
            if state == end or state in obstacles:
                continue
            # Assign a random action from 0 to 3
            policy[f"{r},{c}"] = random.randint(0, 3)
            
    return jsonify(policy)

@app.route('/api/policy_evaluation', methods=['POST'])
def policy_evaluation():
    data = request.json
    n = data.get('n', 5)
    start = data.get('start')
    end = data.get('end')
    obstacles = data.get('obstacles', [])
    policy_data = data.get('policy', {})
    
    # Restructure policy
    policy = {}
    for k, v in policy_data.items():
        r, c = map(int, k.split(','))
        policy[(r, c)] = v
        
    env = GridWorld(n, start, end, obstacles)
    
    V = { (r, c): 0.0 for r in range(n) for c in range(n) }
    theta = 1e-4
    
    # Iterate
    while True:
        delta = 0
        V_new = V.copy()
        for r in range(n):
            for c in range(n):
                state = (r, c)
                if state == env.end or state in env.obstacles:
                    continue # value is 0
                    
                a = policy.get(state)
                if a is not None:
                    next_s = env.get_next_state(state, a)
                    r_val = env.get_reward(state, a, next_s)
                    v_val = r_val + env.gamma * V[next_s]
                    V_new[state] = v_val
                    delta = max(delta, abs(V_new[state] - V[state]))
                    
        V = V_new
        if delta < theta:
            break
            
    # Serialize V
    V_serializable = {f"{r},{c}": round(V[(r, c)], 2) for r in range(n) for c in range(n)}
    return jsonify(V_serializable)

@app.route('/api/value_iteration', methods=['POST'])
def value_iteration():
    data = request.json
    n = data.get('n', 5)
    start = data.get('start')
    end = tuple(data.get('end', [-1,-1]))
    obstacles = set(tuple(obs) for obs in data.get('obstacles', []))
    
    env = GridWorld(n, start, end, obstacles)
    
    V = { (r, c): 0.0 for r in range(n) for c in range(n) }
    policy = {}
    theta = 1e-4
    
    # Value Iteration Loop
    while True:
        delta = 0
        V_new = V.copy()
        for r in range(n):
            for c in range(n):
                state = (r, c)
                if state == env.end or state in env.obstacles:
                    continue
                
                max_v = float('-inf')
                best_a = 0
                for a in range(4):
                    next_s = env.get_next_state(state, a)
                    r_val = env.get_reward(state, a, next_s)
                    v_val = r_val + env.gamma * V[next_s]
                    
                    if v_val > max_v:
                        max_v = v_val
                        best_a = a
                        
                V_new[state] = max_v
                policy[f"{r},{c}"] = best_a
                delta = max(delta, abs(V_new[state] - V[state]))
                
        V = V_new
        if delta < theta:
            break
            
    V_serializable = {f"{r},{c}": round(V[(r, c)], 2) for r in range(n) for c in range(n)}
    return jsonify({
        "values": V_serializable,
        "policy": policy
    })

if __name__ == '__main__':
    app.run(debug=True, port=5000)
