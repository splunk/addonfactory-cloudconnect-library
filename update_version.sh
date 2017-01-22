#!/bin/bash

if [[ $BRANCH == develop ]];
then
    version=$(grep __version__ package/cloudconnectlib/__init__.py | awk '{print $3}')
    version=$(echo $version | sed "s/'//g")
    sed -i '' "s/$version/$version.dev$BUILDNUMBER/g" package/cloudconnectlib/__init__.py
fi
