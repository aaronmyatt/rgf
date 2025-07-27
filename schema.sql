-- Table: flows
CREATE TABLE IF NOT EXISTS flows (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    parent_flow_id INTEGER NULL,         -- nullable for root flows
    parent_flow_match_id INTEGER NULL,   -- nullable for root flows, links to flow_matches
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE, -- indicates if the flow is archived
    FOREIGN KEY (parent_flow_id) REFERENCES flows(id),
    FOREIGN KEY (parent_flow_match_id) REFERENCES flow_matches(id)
);

-- Table: matches
CREATE TABLE IF NOT EXISTS matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    line TEXT NOT NULL,
    file_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    line_no INTEGER NOT NULL, -- stores the line number in the file
    grep_meta TEXT, -- stores grep metadata as JSON
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE -- indicates if the flow is archived
);

-- Add unique constraint to prevent duplicate matches in same location
-- will allow multiple flows to use the same data
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_match_location 
ON matches(line, file_path);

-- Table: flow_matches
CREATE TABLE IF NOT EXISTS flow_matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flows_id INTEGER NOT NULL,
    matches_id INTEGER NOT NULL,
    order_index INTEGER DEFAULT 0, -- tracks order within the flow
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE, -- indicates if the flow is archived
    FOREIGN KEY (flows_id) REFERENCES flows(id),
    FOREIGN KEY (matches_id) REFERENCES matches(id)
);

-- I want to allow matches to exist in the same flow multiple times, but not in the same place
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_position_in_flow
ON flow_matches(flows_id, matches_id, order_index);

-- Table: match_notes
CREATE TABLE IF NOT EXISTS match_notes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    description TEXT,
    note TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    archived BOOLEAN DEFAULT FALSE, -- indicates if the flow is archived
    FOREIGN KEY (match_id) REFERENCES matches(id)
);

-- Table: flow_history
CREATE TABLE IF NOT EXISTS flow_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    flow_id INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (flow_id) REFERENCES flows(id)
);
