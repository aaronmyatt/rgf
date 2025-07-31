[x] database schema
    [x] flows
    [x] matches
    [x] flow_matches
    [x] match_notes
[x] mark/save match
    [x] save to db
    [x] keybinding (s)
    [x] show notification on save
    [x] highlight saved rows
        [x] highlight flow_matches for activated flow
        [] maybe a count somewhere?
    [x] create flow if it doesn't exist
    [x] add match to flow
    [] grep pattern history?
[x] BUG: up arrow with no data in datatable throws error
    <!-- [] use `/` to search for patterns in the current flow
    [] use `?` to search for patterns in all flows
    [] use `!` to search for patterns in all matches
    [] use `@` to search for patterns in all notes
    [] use `#` to search for patterns in all tags
    [] use `*` to search for patterns in all files -->

[x] start on the flow screen is no pattern is passed on the cli
[x] use broot like search syntax
    [x] start search with /
    [x] regex support (added a test to verify)
    [-] exact match
[x] vim like nav h,j
[] track which git project the flow is from
[] track the last commit hash at the time of saving the match
    [] check whether the match is out of sync if hash has changed
[] dynamically refine preview window
    [] expand (lines up or down) the file preview 
    [] include top of file (to show imports)
[] dynamically refine search window
    [] search in the file of the match
    [] search in the directory of the match
    [] add parent directories
    > I'm thinking to use +/- bindings to increase/decrease the search scope
[x] start new search from anywhere with '/'?
    
[x] flows screen
    [x] rename screen!
[x] list flows from db
    [x] just show a datatable for now
[x] CRUD flows
    [x] update/edit
    [x] create new flow (n)
    [x] archive flow (d)
    [-] bindings? (dont recall what this is!)
[] command palette to find flows
[x] flow name / description

[x] BUG: match count does not update on flow_screen after adding new matches
[x] BUG: match highlight (bg green) does not update (or clear) when changing flow

[x] flow/steps (singular) screen
[x] rename screen
[x] list FlowMatches
[x] Add title/notes to matches
    [x] display title/description in step list
[x] BUG: fix datatable throwing when the same rows are added. How can we defend against it? Always clear the table on input submission? Or iterate through existing rows for rows with the same key/id?

[] copy steps to clipboard for early llm usage
[] integrate with aider/`llm` libs
[] user defined commands/bindings to send steps to llm or other tools
[] export as:
    [] markdown
    [] pdf
    [] webpage

[] exclude file/pattern from results moving forward
[x] move Matches to the top of the datatable
[x] BUG: selecting rows in the search screen datatable is duplicating the displayed rows
    - not an error, a design... 🙈
    - we were adding the same file_no + line, but with a different order_index
    - However, we were highlighting the count(*) of flowmatches, woops.
BUG: [] highlighted rows are now cleared when starting a new search