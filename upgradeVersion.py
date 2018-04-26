import os
import re
filePattern = '\.csproj$'
nodePattern = '<TargetFrameworkVersion>([\w\.]*)</TargetFrameworkVersion>'
finalNode = '<TargetFrameworkVersion>v4.6.1</TargetFrameworkVersion>'
matchingFiles = list()

# checkout branches

for root, dirs, files in os.walk(".", topdown=False):
    for name in files:
        if bool(re.search('\.csproj$', name, flags=re.I)):
            matchingFiles.append(os.path.join(root, name))

for file in matchingFiles:
    with open(file, 'r+') as f:
    	content = f.read()
    	content = re.sub(nodePattern, finalNode, content)
    	f.seek(0)
    	f.write(content)

# commit and push
