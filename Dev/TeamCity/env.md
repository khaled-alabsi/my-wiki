### Determine Tag Name
```bash
COMMIT_HASH="$(git rev-parse --short HEAD)"
BRANCH="%teamcity.build.branch%"
 
if [[ -z "$COMMIT_HASH" ]]; then
    echo "COMMIT_HASH=$COMMIT_HASH is unset!" 1>&2
    exit 1
fi
 
echo "##teamcity[setParameter name='env.COMMIT_HASH' value='$COMMIT_HASH']"
echo "##teamcity[setParameter name='env.DOCKER_IMAGE_TAG' value='$COMMIT_HASH']"
```