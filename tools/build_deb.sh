#!/usr/bin/env bash

set -eu

export DH_VIRTUALENV_INSTALL_ROOT=/opt/venvs

main () {
    clean
    create_changelog
    get_source
    build_deb
}

clean () {
    rm -rf artifacts
    find laim -type f -name '*.pyc' -delete
    find laim -type d -name __pycache__ -empty -delete
}

create_changelog () {
    local author author_email
    author=$(git config user.name)
    author_email=$(git config user.email)
    ./tools/changelog_to_deb.py CHANGELOG.md laim "$author" "$author_email" \
        > debian/changelog
}

get_source () {
    tempdir=$(mktemp -d)
    trap 'rm -rf "$tempdir"' INT TERM EXIT
    cp tools/Dockerfile-template setup.py README.md LICENSE "$tempdir"/
    cp -r laim debian "$tempdir"/
}

build_deb () {
    local container_id
    for dist in buster bullseye; do
        cd "$tempdir"
        sed "s/DISTRO/$dist/" Dockerfile-template > "Dockerfile-$dist"
        sudo docker build . -f "Dockerfile-$dist" -t "laim-$dist"
        sudo docker run "laim-$dist"
        cd -
        container_id=$(sudo docker ps -qla)
        sudo docker cp "$container_id:/build/dist" .
        mkdir -p "artifacts/$dist"
        cp dist/*.deb "artifacts/$dist"
        sudo rm -rf dist
        chmod 644 "artifacts/$dist"/*.deb
    done
}

main
