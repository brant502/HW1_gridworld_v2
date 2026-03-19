let n = 5;
let startCell = null;
let endCell = null;
let obstacles = [];
let currentPolicy = {};

const ACTION_ARROWS = {
    0: '↑',
    1: '→',
    2: '↓',
    3: '←'
};

document.addEventListener('DOMContentLoaded', () => {
    initGrid();
});

function initGrid() {
    const nInput = document.getElementById('grid-n').value;
    n = parseInt(nInput);
    if (isNaN(n) || n < 5 || n > 9) {
        alert("n must be between 5 and 9.");
        return;
    }

    // Reset state
    startCell = null;
    endCell = null;
    obstacles = [];
    currentPolicy = {};
    updateInstructionMsg();

    const container = document.getElementById('grid-container');
    container.style.gridTemplateColumns = `repeat(${n}, 1fr)`;
    container.innerHTML = '';

    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.dataset.r = r;
            cell.dataset.c = c;
            cell.id = `cell-${r}-${c}`;
            cell.onclick = () => handleCellClick(r, c);

            const content = document.createElement('div');
            content.className = 'cell-content';
            content.id = `content-${r}-${c}`;

            cell.appendChild(content);
            container.appendChild(cell);
        }
    }
}

function handleCellClick(r, c) {
    const isObstacle = obstacles.some(obs => obs[0] === r && obs[1] === c);

    if (!startCell) {
        startCell = [r, c];
        renderCellClasses();
    } else if (!endCell) {
        if (startCell[0] === r && startCell[1] === c) return;
        endCell = [r, c];
        renderCellClasses();
    } else {
        // Handle obstacle logic
        if ((startCell && startCell[0] === r && startCell[1] === c) ||
            (endCell && endCell[0] === r && endCell[1] === c)) return;

        if (isObstacle) {
            // Remove
            obstacles = obstacles.filter(obs => obs[0] !== r || obs[1] !== c);
        } else {
            // Add (limit n - 2)
            if (obstacles.length < n - 2) {
                obstacles.push([r, c]);
            } else {
                alert(`You can only set up to ${n - 2} obstacles.`);
            }
        }
        renderCellClasses();
    }
    updateInstructionMsg();
}

function renderCellClasses() {
    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            const cell = document.getElementById(`cell-${r}-${c}`);
            cell.className = 'grid-cell';

            if (startCell && startCell[0] === r && startCell[1] === c) {
                cell.classList.add('cell-start');
            } else if (endCell && endCell[0] === r && endCell[1] === c) {
                cell.classList.add('cell-end');
            } else if (obstacles.some(obs => obs[0] === r && obs[1] === c)) {
                cell.classList.add('cell-obstacle');
            }
        }
    }
}

function updateInstructionMsg() {
    const msgEl = document.getElementById('instruction-msg');
    if (!startCell) {
        msgEl.innerText = "Please click a cell to set the Start state (Green).";
    } else if (!endCell) {
        msgEl.innerText = "Please click a cell to set the End state (Red).";
    } else {
        msgEl.innerText = `You can now click empty cells to toggle Obstacles (Gray, up to ${n - 2}).`;
    }
}

function renderContent(policy = null, values = null) {
    for (let r = 0; r < n; r++) {
        for (let c = 0; c < n; c++) {
            const content = document.getElementById(`content-${r}-${c}`);
            content.innerHTML = '';

            const key = `${r},${c}`;
            let hasPolicy = policy && policy[key] !== undefined;
            let hasValue = values && values[key] !== undefined;

            if (hasPolicy) {
                const arr = document.createElement('div');
                arr.className = 'policy-arrow';
                arr.innerText = ACTION_ARROWS[policy[key]];
                content.appendChild(arr);
            }
            if (hasValue) {
                const val = document.createElement('div');
                val.className = 'value-text';
                val.innerText = values[key];
                content.appendChild(val);
            }
        }
    }
}

async function fetchRandomPolicy() {
    if (!startCell || !endCell) { alert("Please set start and end states."); return; }

    const res = await fetch('/api/random_policy', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n, end: endCell, obstacles })
    });
    const policy = await res.json();
    currentPolicy = policy;
    renderContent(policy, null);
}

async function fetchPolicyEvaluation() {
    if (!startCell || !endCell || Object.keys(currentPolicy).length === 0) {
        alert("Please generate a policy first (e.g., Random Policy)."); return;
    }

    const res = await fetch('/api/policy_evaluation', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n, start: startCell, end: endCell, obstacles, policy: currentPolicy })
    });
    const values = await res.json();
    renderContent(currentPolicy, values);
}

async function fetchValueIteration() {
    if (!startCell || !endCell) { alert("Please set start and end states."); return; }

    const res = await fetch('/api/value_iteration', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ n, start: startCell, end: endCell, obstacles })
    });
    const data = await res.json();
    currentPolicy = data.policy;
    renderContent(data.policy, data.values);
}
