#!/bin/bash
# Install the environment required for creating the CMOR CVs table
#
# Usually followed by a command to actually export the table, at the time of writing
# `esgvoc cmor-export-cvs-table --out-path cmor-cvs.json`
#
# Turn on verbose mode with `-v`
#
# If you're on windows, sorry.
# You should be able to more or less copy these commands out.

verbose=0

while getopts "v" OPTION; do
    case $OPTION in
    v) verbose=1 ;;
    *)
        echo "usage: $0 [-v]" >&2
        exit 1
        ;;
    esac
done

function log() {
    if [[ $verbose -eq 1 ]]; then
        echo "$@"
    fi
}

ESGVOC_FORK="${ESGVOC_FORK:=ESGF}"
ESGVOC_REVISION="${ESGVOC_REVISION:=4ee8e0f}" # v2.1.0
UNIVERSE_CVS_FORK="${UNIVERSE_CVS_FORK:='WCRP-CMIP'}"
UNIVERSE_CVS_BRANCH="${UNIVERSE_CVS_BRANCH:=esgvoc}"
CMIP7_CVS_FORK="${CMIP7_CVS_FORK:='WCRP-CMIP'}"
CMIP7_CVS_BRANCH="${CMIP7_CVS_BRANCH:='esgvoc_dev'}"

log "ESGVOC_FORK=$ESGVOC_FORK"
log "ESGVOC_REVISION=$ESGVOC_REVISION"
log "UNIVERSE_CVS_FORK=$UNIVERSE_CVS_FORK"
log "UNIVERSE_CVS_BRANCH=$UNIVERSE_CVS_BRANCH"
log "CMIP7_CVS_FORK=$CMIP7_CVS_FORK"
log "CMIP7_CVS_BRANCH=$CMIP7_CVS_BRANCH"

# TODO: update requirements-cmor-cvs-table.txt before calling so the version used is recorded
pip install -r requirements-cmor-cvs-table.txt
pip install --no-deps "git+https://github.com/$ESGVOC_FORK/esgf-vocab.git@$ESGVOC_REVISION"

esgvoc config create cmip7-cvs-ci
esgvoc config switch cmip7-cvs-ci

esgvoc config remove-project -f cmip6
esgvoc config remove-project -f cmip6plus
esgvoc config remove-project -f cmip7

esgvoc config set "universe:github_repo=https://github.com/$UNIVERSE_CVS_FORK/WCRP-universe" "universe:branch=$UNIVERSE_CVS_BRANCH"
esgvoc config add-project cmip7 --custom --repo "https://github.com/$CMIP7_CVS_FORK/CMIP7-CVs" --branch "$CMIP7_CVS_BRANCH"

esgvoc install
