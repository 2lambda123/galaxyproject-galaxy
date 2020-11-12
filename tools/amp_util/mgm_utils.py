import sys
import os


ERR_SUFFIX = ".err"

# Note for the methods below:
# Since Galaxy creates all output files with size 0 upon starting a job, we can't use the existence of output file 
# to decide if the output has been created; rather, we can use its file size and/or content as the criteria.


# Exit with error code 1 if the given (output) file already generated previously.
# This method is typically called by a command with following command depending on it, both called repeatedly, such as in HMGM. 
def exit_if_file_generated(file):        
    # if the file has already been generated, for ex, by the HMGM converter, exit calling command with error code 1 
    # to avoid redundant process, and inform HMGM job runner to reschedule the job till all commands complete.     
    if os.path.exists(file) and os.stat(file).st_size > 0:
        print("File " + file + " has already been generated, exit 1")
        exit(1)
 
 
# Raise exception if the given (input) file does not exist for processing.
# This method is typically called by a command depending on the previous command's success in a multi-command MGM.
def exception_if_file_not_exist(file):       
    # the exception should stop further processing in the calling command, which could either exit with the exception, 
    # or handle the exception and exit with error code -1, to signal HMGM job runner to fail the whole job in ERROR status
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        raise Exception("Exception: File " + file + " doesn't exist or is empty, the previous command generating it must have failed.")
 
 
# Check if the given (input) file is in error or doesn't exist for processing, exit with error code -1 or 1 respectively.
# This method is typically called by a command repeatedly waiting on the previous command's completion in a multi-command HMGM.
def exit_if_file_not_ready(file):
    # if error file for the given file exists, then previous command (conversion or HMGM task) must have failed,
    # in which case raise exception so the HMGM job runner will fail the whole job in ERROR status
    err_file = file + ERR_SUFFIX
    if os.path.exists(err_file):
        raise Exception("Exception: File " + file + " is in error, the previous command generating it must have failed.")

    # otherwise, if the given file hasn't been generated, for ex, by the HMGM editor, exit with error code 1, 
    # so the HMGM job runner can requeue the job, and process will continue to wait for HMGM task to be completed
    if not os.path.exists(file) or os.stat(file).st_size == 0:
        print("File " + file + " has not been generated, exit 1")
        exit(1)
         
 
# Create an empty error file for the given (output) file.
# This method is typically called by an MGM command exiting with error code -1 upon exceptions.
def create_err_file(file):
    # error file has the .err suffix added to the original file path
    err_file = file + ERR_SUFFIX
    with open(err_file, 'w') as fp: 
        pass
    print("Error file for " + file + " has been created")
    
 
# Clean up error file if existing for the given (output) file. 
# This method is typically called by an MGM command which could be rerun using the same dependencies after failing with previous error file.
def cleanup_err_file(file):
    err_file = file + ERR_SUFFIX
    if os.path.exists(err_file):
        os.remove(err_file)
        print("Error file for " + file + " has been cleaned up")
