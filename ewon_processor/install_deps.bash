pip install ~/pydoover -t ./ --upgrade --no-dependencies
rm -rf ./pydoover/docker

pip install pydatamailbox -t ./ --upgrade --no-dependencies
# pip install python-dateutil -t ./ --upgrade --no-dependencies
find . | grep -E "(/__pycache__$|\.pyc$|\.pyo$)" | xargs rm -rf

