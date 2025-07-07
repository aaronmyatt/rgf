-- Table: flows
CREATE TABLE IF NOT EXISTS flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    parent_flow_id INTEGER NULL,         -- nullable for root flows
    parent_flow_match_id INTEGER NULL,   -- nullable for root flows, links to flow_matches
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_flow_id) REFERENCES flows(id),
    FOREIGN KEY (parent_flow_match_id) REFERENCES flow_matches(id)
);

-- Table: matches
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    date_played DATE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Table: flow_matches
CREATE TABLE IF NOT EXISTS flow_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL,
    match_id INTEGER NOT NULL,
    order_index INTEGER NOT NULL, -- tracks order within the flow
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flow_id) REFERENCES flows(id),
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

-- Table: match_notes
CREATE TABLE IF NOT EXISTS match_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    note TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (match_id) REFERENCES matches(id)
);