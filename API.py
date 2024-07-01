import os
import re
import sched
import time
from datetime import datetime, timedelta

from flask import Flask
from flask_restful import Api


# Creates an absolute path for a given file
def createAbsFilePath(baseDirectory: str, fileName: str):
    absFilePath: str = os.path.join(baseDirectory, fileName)
    absFilePath = os.path.normpath(absFilePath)
    return absFilePath


# Matches files to be purged, creates an absolute path for them, and returns a list of such paths
def findMatchedFiles(baseFolder: str, sourceFilePatternPrefix: str = "DATA_", sourceFilePatternSuffix: str = ".txt"):
    ## Takes directory to search in and stores list of files in them
    filesList = os.listdir(baseFolder)

    ## Takes the file name pattern prefix and suffix to search for and concatenates into a single RegEx
    sourceFilePattern = f"{sourceFilePatternPrefix}.*{sourceFilePatternSuffix}"

    ## Finds file names matching RegEx and pushes them into a new list
    matchedFilesList = []
    for file in filesList:
        matchedFile = re.findall(sourceFilePattern, file)
        if not matchedFile == []:
            ### Appends absolute file path as a string to the list
            matchedFileAbsPath = createAbsFilePath(baseDirectory=baseFolder, fileName=matchedFile[0])
            matchedFilesList.append(matchedFileAbsPath)

    ## Returns list of absolute paths of all matching files
    return matchedFilesList


# Iterates through a list of files, deletes them, and passes purged file paths into list
def filePurger(fileList: list):
    ## List of files purged
    purgeConfirmations = []

    ## Iterates through file list to purge
    for filePath in fileList:
        os.remove(filePath)
        ### If file no longer exists, append a confirmation message to the list
        if not os.path.exists(filePath):
            purgeConfirmations.append(f"{filePath} purged")

    return purgeConfirmations


# Initialize API
app = Flask(__name__)
api = Api(app)


# Purge files at the given directory in the URL on threshold date
@app.route('/<path:sourceFolder>')  # r"C://Users/trivi/Desktop/sample"
def purgeFiles(sourceFolder):
    ## Returns list of files to be purged
    purgeFilesList = findMatchedFiles(baseFolder=sourceFolder)

    ## Calculate threshold date from current date and execute the file purging
    scheduler = sched.scheduler(time.time, time.sleep)
    givenDate = datetime.now()
    retentionDuration = timedelta(days=5)
    thresholdDate = givenDate - retentionDuration
    scheduler.enterabs(thresholdDate.timestamp(), 1, filePurger, argument=(purgeFilesList,))
    scheduler.run()


# Runs in debug mode
if __name__ == "__main__":
    app.run(debug=True)
