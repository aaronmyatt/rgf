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
        [] highlight flow_matches for actived flow
        [] maybe a count somewhere?
    [x] create flow if it doesn't exist
    [x] add match to flow
    [] grep pattern history?
    <!-- [] use `/` to search for patterns in the current flow
    [] use `?` to search for patterns in all flows
    [] use `!` to search for patterns in all matches
    [] use `@` to search for patterns in all notes
    [] use `#` to search for patterns in all tags
    [] use `*` to search for patterns in all files -->
    [] use broot like search syntax
        [] start search with /
        [] regex support
        [] exact match
    [] vim like nav h,j
    
[] flows screen
    [] rename screen!
[] list flows from db
    [] just show a datatable for now
[] CRUD flows
    [] bindings?
[] command pallete to find flows
[] flow name / description

[] flow/steps (singular) screen
[] rename screen
[] list FlowMatches
[] Add title/notes to matches
[x] BUG: fix datatable throwing when the same rows are added. How can we defend against it? Always clear the table on input submission? Or iterate through existing rows for rows with the same key/id?