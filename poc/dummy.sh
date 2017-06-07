# This is a dummy autocompletion example (it doesn't really work, because it doesn't take into account what was typed so far).

complete_prog()
{
    # consider $COMP_LINE, $COMP_POINT, ...
    local OPTIONS="foo bar foobar"
    COMPREPLY=( $OPTIONS )
}

complete -F complete_prog prog
