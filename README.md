# Introduction

An API that purges files in a directory chosen by the user that match a user-defined file pattern, powered by Flask.

# Usage

To use the API, append the absolute path of the required directory at the end of the URL where the server is run.
If matching files are found, a list of purged files will be returned with their absolute paths.
If no matching files are found, an error message will be returned instead.

## Syntax

`http://127.0.0.1:5000/<directory>`
