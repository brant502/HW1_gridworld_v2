import random
import streamlit as st

# --- Action and Symbol Definitions ---
ACTION_DELTAS = {0: (-1, 0), 1: (0, 1), 2: (1, 0), 3: (0, -1)}
ACTION_SYMBOLS = {0: "↑", 1: "→", 2: "↓", 3: "←"}

# --- Environment Logic ---
class GridWorld:
    def __init__(self, n, start, end, obstacles):
        self.n = n
        self.start = tuple(start) if start else None
        self.end = tuple(end) if end else None
        self.obstacles = set(tuple(obs) for obs in obstacles)
        self.gamma = 0.9
        self.reward = -1
        
    def get_next_state(self, state, action):
        r, c = state
        if state == self.end: # Terminal state absorbs
            return state
        dr, dc = ACTION_DELTAS[action]
        next_r, next_c = r + dr, c + dc
        
        # Check boundary
        if next_r < 0 or next_r >= self.n or next_c < 0 or next_c >= self.n:
            return state
        # Check obstacle
        if (next_r, next_c) in self.obstacles:
            return state
        return (next_r, next_c)
        
    def get_reward(self, state, action, next_state):
        if state == self.end:
            return 0
        return self.reward

# --- Streamlit Configurations ---
st.set_page_config(page_title="Grid World RL", layout="wide")
st.title("Grid World 強化學習 (Streamlit 點擊版)")

# Initialize session state variables
if "n" not in st.session_state:
    st.session_state.n = 5
if "start" not in st.session_state:
    st.session_state.start = (0, 0)
if "end" not in st.session_state:
    st.session_state.end = (4, 4)
if "obstacles" not in st.session_state:
    st.session_state.obstacles = set([(1, 1), (2, 2)])
if "grid_values" not in st.session_state:
    st.session_state.grid_values = {}
if "policy" not in st.session_state:
    st.session_state.policy = {}
if "path" not in st.session_state:
    st.session_state.path = set()

# Calculate dynamic height based on n and columns layout
def handle_click(r, c, tool):
    state = (r, c)
    if tool == '🟢 設為起點 (S)':
        st.session_state.start = state
        if state in st.session_state.obstacles: 
            st.session_state.obstacles.remove(state)
    elif tool == '🔴 設為終點 (E)':
        st.session_state.end = state
        if state in st.session_state.obstacles: 
            st.session_state.obstacles.remove(state)
    elif tool == '⬛ 設為障礙物 (OBS)':
        if state != st.session_state.start and state != st.session_state.end:
            st.session_state.obstacles.add(state)
    elif tool == '⬜ 橡皮擦 (清除)':
        if state in st.session_state.obstacles:
            st.session_state.obstacles.remove(state)

# --- Sidebar UI ---
with st.sidebar:
    st.header("⚙️ 環境設定")
    
    def on_n_change():
        n = st.session_state.n_input
        st.session_state.n = n
        # Reset out of bounds coords
        if st.session_state.start[0] >= n or st.session_state.start[1] >= n:
            st.session_state.start = (0, 0)
        if st.session_state.end[0] >= n or st.session_state.end[1] >= n:
            st.session_state.end = (n-1, n-1)
        st.session_state.obstacles = {obs for obs in st.session_state.obstacles if obs[0] < n and obs[1] < n}
        st.session_state.grid_values = {}
        st.session_state.policy = {}
        st.session_state.path = set()
        
    st.number_input("網格大小 (N)", min_value=3, max_value=20, value=st.session_state.n, key="n_input", on_change=on_n_change)
    n = st.session_state.n
    
    st.markdown("---")
    st.header("🖌️ 點擊編輯畫筆")
    st.markdown("選取後在右側的 **地圖編輯器** 中直接點擊格子")
    edit_tool = st.radio(
        "選擇畫筆工具：",
        ['🟢 設為起點 (S)', '🔴 設為終點 (E)', '⬛ 設為障礙物 (OBS)', '⬜ 橡皮擦 (清除)'],
        index=2
    )

    st.markdown("---")
    st.header("🧠 演算法控制")
    
    start = st.session_state.start
    end = st.session_state.end
    obstacles = st.session_state.obstacles
    
    if st.button("生成隨機策略 (Random Policy)", use_container_width=True):
        policy = {}
        for r in range(n):
            for c in range(n):
                state = (r, c)
                if state == end or state in obstacles:
                    continue
                policy[state] = random.randint(0, 3)
        st.session_state.policy = policy
        st.session_state.grid_values = { (r, c): 0.0 for r in range(n) for c in range(n) }
        st.session_state.path = set()
        
    if st.button("執行策略評估 (Policy Evaluation)", use_container_width=True):
        if not st.session_state.policy:
            st.warning("請先生成策略！")
        else:
            env = GridWorld(n, start, end, obstacles)
            if not st.session_state.grid_values:
                V = { (r, c): 0.0 for r in range(n) for c in range(n) }
            else:
                V = st.session_state.grid_values.copy()
            theta = 1e-4
            while True:
                delta = 0
                V_new = V.copy()
                for r in range(n):
                    for c in range(n):
                        state = (r, c)
                        if state == env.end or state in env.obstacles:
                            continue
                        a = st.session_state.policy.get(state)
                        if a is not None:
                            next_s = env.get_next_state(state, a)
                            r_val = env.get_reward(state, a, next_s)
                            v_val = r_val + env.gamma * V[next_s]
                            V_new[state] = v_val
                            delta = max(delta, abs(V_new[state] - V[state]))
                V = V_new
                if delta < theta:
                    break
            st.session_state.grid_values = V
            st.session_state.path = set()

    if st.button("執行價值迭代 (Value Iteration)", use_container_width=True):
        env = GridWorld(n, start, end, obstacles)
        V = { (r, c): 0.0 for r in range(n) for c in range(n) }
        policy = {}
        theta = 1e-4
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
                    policy[state] = best_a
                    delta = max(delta, abs(V_new[state] - V[state]))
            V = V_new
            if delta < theta:
                break
        st.session_state.grid_values = V
        st.session_state.policy = policy

        # Trace shortest path
        path_set = set()
        current = start
        visited = set()
        
        while current and current != end and current not in visited:
            visited.add(current)
            path_set.add(current)
            a = policy.get(current)
            if a is None:
                break
            next_s = env.get_next_state(current, a)
            if next_s == current or next_s in obstacles:
                break
            current = next_s
            
        if current == end:
            path_set.add(end)
        else:
            path_set = set() # Invalid path

        st.session_state.path = path_set


# --- Main Interface Tabs ---
tab1, tab2 = st.tabs(["🖌️ 地圖編輯器 (點擊設定)", "🗺️ 演算法視覺化 (結果)"])

with tab1:
    st.subheader("點擊格子設置起點、終點或障礙物")
    
    # 建立可用於點擊的按鈕網格
    for r in range(n):
        cols = st.columns(n)
        for c in range(n):
            state = (r, c)
            
            # 設定按鈕標籤
            if state == start:
                lbl = "🟢 S"
            elif state == end:
                lbl = "🔴 E"
            elif state in obstacles:
                lbl = "⬛ OBS"
            else:
                lbl = "⬜"
            
            # 使用 on_click Callback 即時更新變數
            cols[c].button(lbl, key=f"btn_{r}_{c}", use_container_width=True, on_click=handle_click, args=(r, c, edit_tool))

with tab2:
    st.subheader("執行結果視覺化")
    st.write("執行左側的演算法後，這裡會顯示 **State Value** 與 **Policy 最佳方向**。")
    
    # 動態產生帶有 CSS 與資料的方格
    html_code = f"<div style='display: grid; grid-template-columns: repeat({n}, 70px); gap: 4px;'>"
    
    for r in range(n):
        for c in range(n):
            state = (r, c)
            bg_color = "#ffffff"
            font_color = "#333333"
            border = "1px solid #cccccc"
            text = ""
            
            if state in obstacles:
                bg_color = "#555555"
                text = "OBS"
                font_color = "white"
            elif state == start:
                bg_color = "#d4edda"  # Green
            elif state == end:
                bg_color = "#f8d7da"  # Red
                text = "END"
            elif state in st.session_state.get('path', set()):
                bg_color = "#a3d3af"  # Distinct Highlighted Green for path
            
            if state not in obstacles and state != end:
                val = st.session_state.grid_values.get(state, 0.0)
                act = st.session_state.policy.get(state, None)
                val_text = f"{val:.2f}" if val != 0.0 else "0.00"
                act_text = ACTION_SYMBOLS[act] if act is not None else ""
                
                if state == start:
                    text = f"<b>START</b><br><span style='font-size:12px'>{val_text}</span><br><b style='font-size:16px'>{act_text}</b>"
                else:
                    text = f"<span style='font-size:12px'>{val_text}</span><br><b style='font-size:16px'>{act_text}</b>"
            
            cell_html = f"<div style='background-color: {bg_color}; border: {border}; color: {font_color}; width: 70px; height: 70px; display: flex; flex-direction: column; align-items: center; justify-content: center; font-size: 14px; text-align: center; line-height: 1.2; border-radius: 4px;'>{text}</div>"
            html_code += cell_html
            
    html_code += "</div>"
    import streamlit.components.v1 as components
    components.html(html_code, height=n*75 + 20)
