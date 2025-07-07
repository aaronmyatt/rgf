sanitize_input() {
    printf '%q' "$1"
}

rgf() {
  local pattern
  pattern="$1"
  shift
  rg --color=always -n "$pattern" "$@" | fzf \
    --ansi \
    --nth 1 \
    --delimiter : \
    --preview-window 'up,60%,border-bottom,+{2}/2' \
    --preview 'grep-ast $(printf "%q" "{3..}") "{1}"' \
    --bind "enter:execute(micro {1} +{2})"
}

