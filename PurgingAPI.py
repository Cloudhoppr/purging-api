import os
import re
import sched
import time
from datetime import datetime, timedelta

from flask import Flask
from flask_restful import Api


# Validates a JSON request that it takes as a dictionary parameter
def requestValidation(request: dict):
    ## Checks if src_zip and src_clear are a subset of {0,1} i.e. each have value of either 0 or 1
    src_zip = request["src_zip"]
    src_clear = request["src_clear"]
    binaryValuesCheck = {src_zip, src_clear} <= {0, 1}

    ## Checks if retention_period is of the format xD/xW/xM where x is an integer
    retentionPeriodMatchObject = re.search(r"^\d[DWM]$", request["retention_period"], re.IGNORECASE)
    retentionPeriodCheck = retentionPeriodMatchObject is not None

    ## Checks if frequency is either 1, 2, or 3
    frequency = request["frequency"]
    frequencyCheck = frequency in range(1, 4)

    ## Checks that dayofexe is valid only if frequency is 2 or 3
    dayOfExe = request["dayofexe"]
    dayOfExeValidation = frequency in range(2, 4)

    ## Assigned a value so that NameError does not occur
    dayOfExeCheck = True
    ## Checks that dayofexe is in acceptable ranges according to the value of frequency
    if dayOfExeValidation:
        if frequency == 2:
            dayOfExeCheck = dayOfExe in range(1, 8)
        elif frequency == 3:
            dayOfExeCheck = dayOfExe in range(1, 29)

    ## Assigns every check to a key of the same name in a global dictionary (mapping will be used in error handling)
    global checks
    checks = {"binaryValuesCheck": binaryValuesCheck,
              "retentionPeriodCheck": retentionPeriodCheck,
              "frequencyCheck": frequencyCheck,
              "dayOfExeValidation": dayOfExeValidation,
              "dayOfExeCheck": dayOfExeCheck}

    ## Validates that every condition is true, else a runtime error is raised
    if all(checks.values()):
        return True
    else:
        raise RuntimeError


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
            #### Appends absolute file path as a string to the list
            matchedFileAbsPath = createAbsFilePath(baseDirectory=baseFolder, fileName=matchedFile[0])
            matchedFilesList.append(matchedFileAbsPath)
        else:
            raise FileNotFoundError

    ## Returns list of absolute paths of all matching files
    return matchedFilesList


# List of files purged
purgeConfirmations = []


# Iterates through a list of files, deletes them, and passes purged file paths into list
def filePurger(fileList: list):
    ## Iterates through file list to purge
    for filePath in fileList:
        os.remove(filePath)
        ### If file no longer exists, append a confirmation message to the list
        if not os.path.exists(filePath):
            purgeConfirmations.append(f"{filePath} purged")


# Initialize API
app = Flask(__name__)
api = Api(app)

# Sample JSON Request
req = {"name": "App1 BackUp", "src_ip": "10.11.163.1", "src_user": "backup", "src_pass": "1234",
       "src_loc": "/appdata/backup/", "src_fileslist": " file1.zip|*.bkp ", "src_zip": 1, "src_clear": 0,
       "dest_sftp_cmd": "sftp backup1@90.207.237.1", "dest_pass": "85f3e32aabb", "dest_loc": "/nedata/backup/",
       "retention_period": "3W", "frequency": 2, "dayofexe": 1}


# Purge files at the given directory in the URL on threshold date
@app.route('/<path:sourceFolder>')  # r"C://Users/trivi/Desktop/sample"
def main(sourceFolder):
    try:
        # Runs operations only if validation is True
        validity = requestValidation(req)
        if validity is True:
            ## Returns list of files to be purged
            purgeFilesList = findMatchedFiles(baseFolder=sourceFolder)

            ## Calculate threshold date from current date and execute the file purging
            scheduler = sched.scheduler(time.time, time.sleep)
            givenDate = datetime.now()
            retentionDuration = timedelta(days=5)
            thresholdDate = givenDate - retentionDuration
            scheduler.enterabs(thresholdDate.timestamp(), 1, filePurger, argument=(purgeFilesList,))
            scheduler.run()
    except FileNotFoundError:
        return f"{FileNotFoundError.__name__} has occurred, please try a different file name or extension."
    except RuntimeError:
        wrongParameters = []
        for i in checks.keys():
            if checks[i] is False:
                match i:
                    case "binaryValuesCheck":
                        wrongParameters.extend(["src_zip", "src_clear"])
                    case "retentionPeriodCheck":
                        wrongParameters.append("retention_period")
                    case "frequencyCheck" | "dayOfExeValidation":
                        wrongParameters.append("frequency")
                    case "dayOfExeCheck":
                        wrongParameters.append("dayofexe")

        return f"A {RuntimeError.__name__} has occurred. Please check the following parameter: {wrongParameters}"
    else:
        return purgeConfirmations


# Runs in debug mode
if __name__ == "__main__":
    app.run(debug=True)
