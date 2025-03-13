#!/bin/bash

## parse command line args ####################################################
skip_lint=0
skip_mypy=0

# Check optional arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --skip-pylint)
            skip_lint=1
            shift
            ;;
        --skip-mypy)
            skip_mypy
            shift
            ;;            
        *)
            # Ignore unknown options
            shift
            ;;
    esac
done

if [ $skip_lint -eq 0 ]; then
    git diff --name-only main | grep -E '\.py$' | grep '^apps/bluebirds_platform/sequences' | sed 's#^apps/bluebirds_platform/sequences/##' | grep -Ev '^migrations/' | xargs poetry run pylint
fi

if [ $skip_mypy -eq 0 ]; then
    git diff --name-only main | grep -E '\.py$' | grep '^apps/bluebirds_platform/sequences' | sed 's#^apps/bluebirds_platform/sequences/##' | grep -Ev '^migrations/' | xargs poetry run mypy
fi
