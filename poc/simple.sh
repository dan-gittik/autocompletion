# This is a very simple autocompletion example.

_complete_prog()
{
    local OPTIONS="foo bar foobar"
    local CURRENT="${COMP_WORDS[$COMP_CWORD]}"
    COMPREPLY=( $(compgen -W "$OPTIONS" -- "$CURRENT") )
}

complete -F _complete_prog prog
