import os
import re

# Set the directory you want to start from
rootDir = 'C:/Users/Patrik/Desktop/test/scrape/Reptile Guide'

for dirName, subdirList, fileList in os.walk(rootDir):
    for fileName in fileList:
        # Only process text files
        if fileName.endswith('.txt'):
            filePath = os.path.join(dirName, fileName)
            # Open the file and read its contents
            with open(filePath, 'r') as f:
                lines = f.readlines()
            # Process each line
            for i, line in enumerate(lines):
                # Remove everything after the first hyphen or parentheses
                lines[i] = re.sub(r'\s*[-()+\[\]&].*', '', line)
            # Write the modified lines back to the file
            with open(filePath, 'w') as f:
                f.writelines(lines)
