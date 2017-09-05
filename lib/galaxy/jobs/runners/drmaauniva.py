"""
Kind of fail save job control via the DRMAA API.
Tested for UNIVA grid engine
"""
import logging
import os
import re
import signal
import subprocess
import time

# from galaxy import model
from galaxy.jobs.runners.drmaa import DRMAAJobRunner
from galaxy import util 

log = logging.getLogger( __name__ )

__all__ = ( 'UnivaJobRunner', )

MEMORY_LIMIT_SCAN_SIZE = 1024 * 1024  # 1MB

"""
TODO
find out what it means if there is no error code file (.ec)
can this also be used

tool wrapper:
- A tool that is the bash script itself.
- bash script (create long array, dd into variable)
- C
- C++
- python
- java
- perl
"""


class DRMAAWaitUnusable( Exception ):
    pass


class UnivaJobRunner( DRMAAJobRunner ):
    runner_name = "UnivaJobRunner"
    # restrict job name length as in the DRMAAJobRunner
    # restrict_job_name_length = 15

    def check_watched_item( self, ajs, new_watched ):
        # get state with job_info/qstat
        state = self._get_drmaa_state(ajs.job_id, self.ds, False)
        log.debug("UnivaJobRunner:check_watched_item ({jobid}) -> state {state}".format(jobid=ajs.job_id, state=self.drmaa_job_state_strings[state]))
        return state

    def _complete_terminal_job( self, ajs, drmaa_state, **kwargs ):
        extinfo = dict()
        # get state with job_info/qstat + wait/qacct
        state = self._get_drmaa_state(ajs.job_id, self.ds, True, extinfo)
        log.debug("UnivaJobRunner:_complete_terminal_job ({jobid}) -> state {state} info {info}".format(jobid=ajs.job_id, state=self.drmaa_job_state_strings[state], info=extinfo))

        # for any job that is finished (regardless of successful or failed) check if there
        # were memory or time deletions or if the job was deleted
        if state in [ self.drmaa.JobState.DONE, self.drmaa.JobState.FAILED ]:
            # get configured job destination
            job_destination = ajs.job_wrapper.job_destination
            native_spec = job_destination.params.get('nativeSpecification', None)
            # determine time and memory that was granted for the job
            time_granted, mem_granted = _parse_native_specs( ajs.job_id, native_spec )
            time_wasted = extinfo["time_wasted"]
            mem_wasted = extinfo["memory_wasted"]

            # check if the output contains indicators for a memory violation
            #memviolation = _check_memory_limit( ajs.error_file )
            memerrors = set(["xrealloc: cannot allocate",
                 "MemoryError",
                 "std::bad_alloc",
                 "java.lang.OutOfMemoryError: Java heap space",
                 "Out of memory!"])
            memviolation = util.grep_tail( ajs.error_file, memerrors, MEMORY_LIMIT_SCAN_SIZE )
            
            log.debug("UnivaJobRunner:_complete_terminal_job ({jobid}) memviolation {mv}".format(jobid=ajs.job_id, mv=memviolation))

            # check job for run time or memory violation
            if "deleted" in extinfo and extinfo["deleted"]:
                log.info( '(%s/%s) Job was cancelled (e.g. with qdel)', ajs.job_wrapper.get_id_tag(), ajs.job_id )
                ajs.fail_message = "This job failed because it was cancelled by an administrator."
                drmaa_state = self.drmaa.JobState.FAILED
            elif ("signal" in extinfo and extinfo["signal"] == "SIGKILL") and time_wasted > time_granted:
                log.info( '({tag}/{jobid}) Job hit walltime'.format(tag=ajs.job_wrapper.get_id_tag(), jobid=ajs.job_id) )
                ajs.fail_message = "This job was terminated because it ran longer than the maximum allowed job run time."
                ajs.runner_state = ajs.runner_states.WALLTIME_REACHED
                drmaa_state = self.drmaa.JobState.FAILED
            elif memviolation or mem_wasted > mem_granted:
                log.info( '({idtag}/{jobid}) Job hit memory limit ({used}>{limit})'.format(idtag=ajs.job_wrapper.get_id_tag(), jobid=ajs.job_id, used=mem_wasted, limit=mem_granted) )
                ajs.fail_message = "This job was terminated because it used more than the maximum allowed memory."
                ajs.runner_state = ajs.runner_states.MEMORY_LIMIT_REACHED
                drmaa_state = self.drmaa_job_states.FAILED
        elif state in [ self.drmaa.JobState.QUEUED_ACTIVE, self.drmaa.JobState.SYSTEM_ON_HOLD, self.drmaa.JobState.USER_ON_HOLD, self.drmaa.JobState.USER_SYSTEM_ON_HOLD, self.drmaa.JobState.RUNNING, self.drmaa.JobState.SYSTEM_SUSPENDED, self.drmaa.JobState.USER_SUSPENDED ]:
            log.warning( '({tag}/{jobid}) Job is {state}, returning to monitor queue'.format(tag=ajs.job_wrapper.get_id_tag(), jobid=ajs.job_id, state=self.drmaa_job_state_strings[state] ))
            # TODO return True?
            return True  # job was not actually terminal
        else:
            log.error( "DRMAAUniva: job {job_id} determined unknown state {state}".format(job_id=ajs.job_id, state=state) )
            drmaa_state = self.drmaa_job_states.FAILED
        # by default, finish the job with the state from drmaa
        return super( UnivaJobRunner, self )._complete_terminal_job( ajs, drmaa_state=drmaa_state )

    def _drmaa_state_is_refined( self, statep, staten ):
        """
        check if staten is more 'severe' than statep
        """
        # definition of the severity of job states, the hex codes are
        # from the drmaa C library which seem to define a useful order
        drmaa_job_state_order = {
            self.drmaa.JobState.UNDETERMINED: 0x00,
            self.drmaa.JobState.QUEUED_ACTIVE: 0x10,
            self.drmaa.JobState.SYSTEM_ON_HOLD: 0x11,
            self.drmaa.JobState.USER_ON_HOLD: 0x12,
            self.drmaa.JobState.USER_SYSTEM_ON_HOLD: 0x13,
            self.drmaa.JobState.RUNNING: 0x20,
            self.drmaa.JobState.SYSTEM_SUSPENDED: 0x21,
            self.drmaa.JobState.USER_SUSPENDED: 0x22,
            self.drmaa.JobState.DONE: 0x30,
            self.drmaa.JobState.FAILED: 0x40 }
        return drmaa_job_state_order[staten] > drmaa_job_state_order[statep]

    def _get_drmaa_state_qstat( self, job_id, extinfo=set()):
        """
        get a (drmaa) job state with qstat. qstat only returns infos for jobs that
        are queued, suspended, ..., or just finished (i.e. jobs are still
        in the system).
        information on finished jobs can only be found by qacct.
        Hence if qstat does not contain information on the job
        the state is assumed as DONE
        job_id the job id
        extinfo a set that additional information can be stored in, i.e., "deleted"
        returns the drmaa state
        """
        log.debug("UnivaJobRunner._get_drmaa_state_qstat ({jobid})".format(jobid=job_id))
        # TODO using -u "*" is the simplest way to query the jobs of all users which
        # allows to treat the case where jobs are submitted as real user it would
        # be more efficient to specify the user (or in case that the galaxy user
        # submits the job -> to ommit the -u option)
        cmd = ['qstat', '-u', '"*"']
        p = subprocess.Popen( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        stdout, stderr = p.communicate()
        if p.returncode != 0 or stderr != "":
            log.exception( '`%s` returned %d, stderr: %s' % ( ' '.join( cmd ), p.returncode, stderr ) )
            raise self.drmaa.InternalException()
        state = None
        for line in stdout.split('\n'):
            line = line.split()
            if len(line) >= 5 and line[0] == str(job_id):
                state = self._map_qstat_drmaa_states( job_id, line[5], extinfo )
                break
        if state is None:
            state = self.drmaa.JobState.DONE
        log.debug("UnivaJobRunner._get_drmaa_state_qstat ({jobid}) -> {state}".format(jobid=job_id, state=self.drmaa_job_state_strings[state]))
        return state

    def _get_drmaa_state_qstatj( self, job_id, extinfo ):
        """
        get the drmaa job status for a specific job using qstat -j.
        - For finished jobs an error message is given:
          Following jobs do not exist or permissions are not sufficient:
          JOBID
          Hence we can not determine with qstat if the job is in DONE (successfully) or FAILED state
          and assume UNDETERMINED
        - For queued jobs there is no output of the job_state
          This could be obtained using qstat without the -j option and grepping for the jobID
        """
        cmd = ['qstat', '-j', job_id]
        p = subprocess.Popen( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        stdout, stderr = p.communicate()
        # the return code of qstat or stderr is not checked directly
        # because if an invalid jobid is given (e.g. for a finished job)
        # return code is 1 and stderr is
        # "Following jobs do not exist or permissions are not sufficient:
        # 264210"
        # hence it is checked if the stderr contains the job_id
        jobnumber = None
        se = []
        # try to get jobid from stderr
        for line in stderr.split('\n'):
            se.append( line )
            if str(job_id) in line:
                jobnumber = str(job_id)
        stderr = "\n".join(se)
        # check sanity of qstat output
        state = None
        if len(stderr) > 0:
            if jobnumber is not None and jobnumber == str(job_id):
                state = self.drmaa.JobState.UNDETERMINED
            else:
                stderr = stderr.strip()
                log.exception( '`%s` returned %d, stderr: %s' % ( ' '.join( cmd ), p.returncode, stderr ) )
                raise self.drmaa.InternalException()
        for line in stdout.split('\n'):
            if not line.startswith("job_state"):
                continue
            log.exception( "DRMAAUniva: job {job_id} qstat -j job_state line '{line}".format(job_id=job_id, linee=line) )
            line = line.split()
            extinfo["state"] = self._map_qstat_drmaa_states( job_id, line[-1], extinfo )
        if state is None:
            state = self.drmaa.JobState.UNDETERMINED
        return state

    def _get_drmaa_state_qacct(self, job_id, extinfo):
        '''
        get the job (drmaa) state with qacct.
        extinfo dict where signal, exit_status, deleted = True, time_wasted, and memory_wasted can be stored
        return state
        '''
        log.debug("UnivaJobRunner._get_drmaa_state_qacct ({jobid})".format(jobid=job_id))
        signals = dict((k, v) for v, k in reversed(sorted(signal.__dict__.items()))
           if v.startswith('SIG') and not v.startswith('SIG_'))
        cmd = ['qacct', '-j', job_id]
        slp = 1
        # run qacct -j JOBID (since the accounting data for the job might not be available immediately a simple retry mechanism is implemented .. max wait is approx 1min)
        while True:
            p = subprocess.Popen( cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
            stdout, stderr = p.communicate()
            stderr = stderr.strip()
            if p.returncode != 0:
                if slp < 32 and "job id {jobid} not found".format(jobid=job_id) in stderr:
                    log.exception( '`%s` returned %s, stderr: %s => retry after %ds' % ( ' '.join( cmd ), p.returncode, stderr, slp ) )
                    time.sleep( slp )
                    slp *= 2
                    continue
                else:
                    log.exception( '`%s` returned %s, stderr: %s' % ( ' '.join( cmd ), p.returncode, stderr ) )
                    return self.drmaa.JobState.UNDETERMINED
            else:
                break
        qacct = dict()
        for line in stdout.split("\n"):
            # remove header
            if line.startswith("=") or line == "":
                continue
            line = line.split()
            qacct[ line[0] ] = " ".join(line[1:])
        # qacct has three fields of interest: failed, exit_status, deleted_by
        # experiments
        #            failed  exit_status deleted_by
        # BASH ------------------------------------
        # time-limit 100     137
        # mem-limit  0       2
        # python --------------------------------------------------------------
        # time-limit
        # mem-limit
        # C -------------------------------------------------------------------
        # time-limit
        # mem-limit
        # C++ -----------------------------------------------------------------
        # time-limit
        # mem-limit
        # JAVA ----------------------------------------------------------------
        # time-limit
        # mem-limit
        # perl ----------------------------------------------------------------
        # time-limit
        # mem-limit
        # bash other tests ----------------------------------------------------
        # qdel       100     137          user@mail

        extinfo["time_wasted"] = _parse_time( qacct["wallclock"] )
        extinfo["memory_wasted"] = util.size_to_bytes( qacct["maxvmem"] )
#         extinfo["memory_wasted"] = _parse_mem( qacct["maxvmem"] )

        log.debug("DRMAAUniva: ({job_id}) qacct {qacct}".format(job_id=job_id, qacct=qacct))

#         for q in qacct:
#             log.debug("%s : %s"%(q, qacct[q]))
#
        # deleted_by
        # If the job (the array task) has been deleted via qdel, "<username>@<hostname>", else
        # "NONE". If qdel was called multiple times, every invocation is recorded in a comma
        # separated list.
        if "deleted_by" in qacct and qacct["deleted_by"] != "NONE":
            log.error( "DRMAAUniva: job {job_id} was aborted by {culprit}".format(job_id=job_id, culprit=qacct["deleted_by"]) )
            extinfo["deleted"] = True
            return self.drmaa.JobState.FAILED

        state = self.drmaa.JobState.UNDETERMINED
        # exit_status
        # Exit status of the job script (or Univa Grid Engine specific status in case of certain
        # error conditions). The exit status is determined by following the normal shell conventions
        # If the command terminates normally the value of the command is its exit status.
        # However, in the case that the command exits abnormally, a value of 0200 (octal), 128
        # (decimal) is added to the value of the command to make up the exit status.
        # For example: If a job dies through signal 9 (SIGKILL) then the exit status
        # becomes 128 + 9 = 137.
        if "exit_status" in qacct:
            qacct["exit_status"] = int(qacct["exit_status"])
            if qacct["exit_status"] < 1:
                log.error( "DRMAAUniva: job {job_id} has exit status {status}".format(job_id=job_id, status=qacct["exit_status"]) )
                state = self.drmaa.JobState.DONE
            elif 0 < qacct["exit_status"] < 129:
                log.error( "DRMAAUniva: job {job_id} has exit status {status}".format(job_id=job_id, status=qacct["exit_status"]) )
                extinfo[ 'exit_status' ] = qacct["exit_status"]
                state = self.drmaa.JobState.FAILED
            else:
                log.error( "DRMAAUniva: job {job_id} was killed by signal {signal}".format(job_id=job_id, signal=qacct["exit_status"] - 128) )
                state = self.drmaa.JobState.FAILED
                extinfo[ "signal" ] = signals[ qacct["exit_status"] - 128 ]

        # failed
        # Indicates the problem which occurred in case a job could not be started on the execution
        # host (e.g. because the owner of the job did not have a valid account on that
        # machine). If Univa Grid Engine tries to start a job multiple times, this may lead to
        # multiple entries in the accounting file corresponding to the same job ID.
        # for the codes see https://docs.oracle.com/cd/E19957-01/820-0699/chp11-2/index.html
        if "failed" in qacct:
            code = int(qacct["failed"].split()[0])
            # this happens in case of no error or exit_code!=0 (0) or a signal (100).
            # both cases are covered already
            if code in [ 0, 100 ]:
                pass
            # these seem to be OK to
            elif code in [ 24, 25 ]:
                state = self.drmaa.JobState.RUNNING
            else:
                log.error( "DRMAAUniva: job {job_id} failed with failure {failure}".format(job_id=job_id, failure=qacct["failed"]) )
                state = self.drmaa.JobState.FAILED
        log.debug("UnivaJobRunner._get_drmaa_state_qacct ({jobid}) -> {state}".format(jobid=job_id, state=self.drmaa_job_state_strings[state]))
        return state

    def _get_drmaa_state_wait( self, job_id, ds, extinfo ):
        '''
        get the (drmaa) job state with the python-drmaa wait function
        this function will not work if the job was started as real user
        since the external runner uses a different drmaa session.
        the advantage over the qacct based method is speed (in particular
        if the accounting data is stored in a huge file)
        jobid: the jobid
        ds: drmaa session
        extinfo dict where signal, exit_status, deleted = True, time_wasted, and memory_wasted can be stored
        '''
        log.debug("UnivaJobRunner._get_drmaa_state_wait ({jobid})".format(jobid=job_id))
        # experiments
        #            exitStatus coreDump hasExited hasSignal Signal  wasAborted
        # BASH ----------------------------------------------------------------
        # time-limit 0          0        0         1         SIGKILL 0
        # mem-limit  2          0        1         0                 0            with creating a large array and dd into variable
        # python --------------------------------------------------------------
        # time-limit 0          0        0         1         SIGKILL 0
        # mem-limit  1          0        1         0                 0
        # C -------------------------------------------------------------------
        # time-limit 0          0        0         1         SIGKILL 0
        # mem-limit  0          1        0         1         SIGSEGV 0          SegFault when accessing unallocated memory
        # C++ -----------------------------------------------------------------
        # time-limit 0          0        0         1         SIGKILL 0
        # mem-limit  0          1        0         1         SIGABRT 0          because of memory
        # JAVA ----------------------------------------------------------------
        # time-limit 0          0        0         1         SIGKILL 0
        # mem-limit  1          0        1         0                 0
        # perl ----------------------------------------------------------------
        # time-limit 0          0        0         0         SIGKILL 0
        # mem-limit  1          0        1         0                 0

        # bash other tests ----------------------------------------------------
        # no exit    0          0        1         0                 0
        # qdel       0          0        0         0                 1
        # TODO just return 0 if external runner is used
        # TODO do not run for running jobs
        try:
            # Note: drmaa refers to the parent galaxy module which has a global
            # variable drmaa which is the drmaa python library
            rv = ds.session.wait(job_id, self.drmaa.session.Session.TIMEOUT_NO_WAIT)
        except self.drmaa.errors.DrmaaException:
        #except self.drmaa.errors.DrmaaException as e:
            # log.exception("could not determine status of job {jobid} using drmaa.wait error was {error}".format(jobid=job_id, error=str( e )))
            raise DRMAAWaitUnusable()

        # documentation of the variables adapted from the drmaa C library documentation at
        # https://linux.die.net/man/3/drmaa_wait
        # currently not used are
        # - rv.jobId
        # - rv.resourceUsage (which contains info on runtime and memory usage)
        # - rv.hasSignal (since we test the terminatedSignal anyway, and the meaning
        #    of hasSignal=0 could be anything from success to failure)
        # - hasExited
        # ** wasAborted**
        # wasAborted is a non-zero value for a job that ended before entering the running state.
        # Note: seems to be non-zero also if it is already running
        # **exitStatus**
        # If hasExited is a non-zero value, the exitStatus variable gives the
        # exit code that the job passed to exit or the value that the child
        # process returned from main.
        # **hasCoreDump**
        # If hasSignal is a non-zero value, hasCoreDump is a non-zero value if a core image
        # of the terminated job was created.

        # **hasExited**
        # non-zero value for a job that terminated normally. A zero value can also indicate
        # that although the job has terminated normally, an exit status is not available,
        # or that it is not known whether the job terminated normally.
        # In both cases exitStatus will not provide exit status information.
        # A non-zero value returned in exited indicates more detailed diagnosis can be
        # provided by means of hasSignal, terminatedSignal and hasCoreDump.
        # **hasSignal**
        # non-zero integer for a job that terminated due to the receipt of a signal.
        # A zero value can also indicate that although the job has terminated due to the
        # receipt of a signal, the signal is not available, or it is not known whether
        # the job terminated due to the receipt of a signal.
        # In both cases terminatedSignal will not provide signal information.
        # A non-zero value returned in signaled indicates signal information can be
        # retrieved from terminatedSignal.
        # **terminatedSignal**
        # If hasSignal is a non-zero value, the terminatedSignal is a
        # a string representation of the signal that caused the termination
        # of the job. For signals declared by POSIX.1, the symbolic names
        # are returned (e.g., SIGABRT, SIGALRM).
        # For signals not declared by POSIX, any other string may be returned.
        # check if job was aborted

        # get the used time and memory
        extinfo["time_wasted"] = float(rv.resourceUsage['wallclock'])
        extinfo["memory_wasted"] = float(rv.resourceUsage['maxvmem'])

        log.debug("wait -> \texitStatus {0}\thasCoreDump {1}\thasExited {2}\thasSignal {3}\tjobId {4}\t\tterminatedSignal {5}\twasAborted {6}\tresourceUsage {7}".format(rv.exitStatus, rv.hasCoreDump, rv.hasExited, rv.hasSignal, rv.jobId, rv.terminatedSignal, rv.wasAborted, rv.resourceUsage))
        if rv.wasAborted:
            log.error( "DRMAAUniva: job {job_id} was aborted according to wait()".format(job_id=job_id) )
            extinfo["deleted"] = True
            return self.drmaa.JobState.FAILED

        # determine if something went wrong. this could be application errors
        # but also violation of scheduler constraints
        state = self.drmaa.JobState.DONE
        if rv.exitStatus != 0:
            log.error( "DRMAAUniva: job {job_id} has exit status {status}".format(job_id=job_id, status=rv.exitStatus) )
            extinfo["state"] = self.drmaa.JobState.FAILED

        if not rv.hasExited or rv.hasSignal:
            if rv.hasCoreDump != 0:
                log.error( "DRMAAUniva: job {job_id} has core dump".format(job_id=job_id) )
                extinfo["state"] = self.drmaa.JobState.FAILED
            elif len(rv.terminatedSignal) > 0:
                log.error( "DRMAAUniva: job {job_id} was kill by signal {signal}".format(job_id=job_id, signal=rv.terminatedSignal) )
                state = self.drmaa.JobState.FAILED
                extinfo["signal"] = rv.terminatedSignal
            elif rv.wasAborted == 0:
                log.error( "DRMAAUniva: job {job_id} has finished in unclear condition".format(job_id=job_id) )
                state = self.drmaa.JobState.FAILED
        log.debug("UnivaJobRunner._get_drmaa_state_wait ({jobid}) -> {state}".format(jobid=job_id, state=self.drmaa_job_state_strings[state]))
        return state

    def _get_drmaa_state(self, job_id, ds, waitqacct, extinfo=dict()):
        """
        get the state using drmaa.job_info/qstat and drmaa.wait/qacct using the above functions
        qacct/wait is only called if waitqacct is True.
        the function returns the state (one of the drmaa states) and extended
        information in the extinfo dict
        """
        log.debug("UnivaJobRunner._get_drmaa_state ({jobid}) {qw}".format(jobid=job_id, qw=waitqacct))
        state = self.drmaa.JobState.UNDETERMINED
        # try to get the state with drmaa.job_status (does not work for jobs
        # started as real user) or  qstat (works only for jobs that are running)
        try:
            log.debug("UnivaJobRunner trying job_status ({jobid})".format(jobid=job_id))
            state = ds.job_status( job_id )
        except self.drmaa.errors.DrmaaException:
            state = self._get_drmaa_state_qstat(job_id, extinfo)
        # if the job is finished (in whatever state) get (additional) infos
        # drmaa.wait or qacct
        if waitqacct and state in [self.drmaa.JobState.UNDETERMINED, self.drmaa.JobState.DONE, self.drmaa.JobState.FAILED ]:
            try:
                wstate = self._get_drmaa_state_wait(job_id, ds, extinfo)
            except DRMAAWaitUnusable:
                log.debug("DRMAAUniva: job {job_id} catched DRMAAWaitUnusable".format(job_id=job_id))
                wstate = self._get_drmaa_state_qacct(job_id, extinfo)
            if self._drmaa_state_is_refined( state, wstate ):
                log.debug("DRMAAUniva: job {job_id} wait/qacct {qacct} refines qacct {qstat}".format(job_id=job_id, qacct=self.drmaa_job_state_strings[wstate], qstat=self.drmaa_job_state_strings[state]))
                state = wstate
            else:
                log.debug("DRMAAUniva: job {job_id} wait/qacct {qacct} does NOT refines qacct {qstat}".format(job_id=job_id, qacct=self.drmaa_job_state_strings[wstate], qstat=self.drmaa_job_state_strings[state]))

        log.debug("UnivaJobRunner._get_drmaa_state ({jobid}) -> {state}".format(jobid=job_id, state=self.drmaa_job_state_strings[state]))
        return state

    def _map_qstat_drmaa_states( self, job_id, state, extinfo ):
        """
        helper function that tries to map the states that are in the output
        of `qstat` and `qstat -j ID` to the states that are returned by the
        jobStatus function of the drmaa python library.

        useful information that can not be mapped to a drmaa state
        is stored in the extinfo dict. this is extinfo["deleted"] = True
        for jobs that are deleted.

        note 1: DONE is not found here, since qstat contains not output
        for jobs that are 'done' (i.e. left the queueing system sucessfully
        of unsuccessfully)

        note 2: the *suspend and *hold are mapped 'sloppily', but this
        should be OK since galaxy does not evaluate them at all (it only
        checks for QUEUED_ACTIVE, RUNNING, DONE, and FAILED)

        the drmaa states are:
        UNDETERMINED:       'process status cannot be determined',
        QUEUED_ACTIVE:      'job is queued and active',
        SYSTEM_ON_HOLD:     'job is queued and in system hold',
        USER_ON_HOLD:       'job is queued and in user hold',
        USER_SYSTEM_ON_HOLD:'job is queued and in user and system hold',
        RUNNING:		'job is running',
        SYSTEM_SUSPENDED: 	'job is system suspended',
        USER_SUSPENDED: 	'job is user suspended',
        DONE:               'job finished normally',
        FAILED:             'job finished, but failed',

        the qstat states are
        Pending   qw 	pending, pending (user hold)
                  hqw 	pending (system hold), pending (user and system hold)
                  hRqw 	pending (user and/or system hold, re-queue)
        Running   r 	running
                  t 	transferring, i.e. the job is transferred to the node(s) and about to be started
                  Rr 	running (re-submit)
                  Rt 	transferring (re-submit)
        Suspended s, ts 	job suspended
                  S, tS 	queue suspended
                  iT, tT 	queue suspended by alarm, e.g. the grid engine suspended the queue (and the job), because the queue is overloaded
                  Rs, Rts, RS, RtS, RT, RtT 	all suspended states with re-submit
        Error 	Eqw, Ehqw, EhRqw 	all pending states with error == GE tried to execute a job in a queue, but it failed for a reason that is specific to the job
        Deleted 	dr, dt, dRr, ds, dS, dT, dRs, dRS, dRT 	all running and suspended states with deletion, i.e. these jobs have been deleted, but have not yet been purged from the system

        the qstat -j ID states are
        d(eletion),             qdel has been used
        E(rror),                pending jobs hat couldn't be started due to job properties
        h(old),                 job currently is not eligible for execution due to a hold state assigned to it
        r(unning),              job is about to be executed or is already executing
        R(estarted),            the job was restarted. This can be caused by a job migration or because of one of the reasons described in the -r section
        s(uspended),            caused by suspending the job via qmod -s
        S(uspended),            either that the queue containing the job is suspended ... or that a pending job got suspended due to a preemptive action that was either triggered automatically by the system or by a manual preemption request triggered via qmod(1) -p ... S
        e(N)hanced suspended,   preemptive states shown for pending jobs triggered either automatically or via qmod(1) -p ... N or -p ... P
        (P)reempted,            -"-
        t(ransfering),          job is about to be executed or is already executing
        T(hreshold) or          shows that at least one suspend threshold of the corresponding queue was exceeded (see queue_conf(5)) and that the job has been suspended as a consequence
        w(aiting).              or that the job is waiting for completion of the jobs to which job dependencies have been assigned to the job

        job_id: the jobid (for logging)
        state: a state from the qstat output
        return: one of the drmaa states
        """
        if "d" in state:
            extinfo["deleted"] = True
            return self.drmaa.JobState.FAILED
        if "E" in state:
            return self.drmaa.JobState.FAILED
        elif "s" in state:
            return self.drmaa.JobState.USER_SUSPENDED
        elif "S" in state or "T" in state or 'N' in state or 'P' in state:
            return self.drmaa.JobState.SYSTEM_SUSPENDED
        elif "h" in state:
            return self.drmaa.JobState.USER_SYSTEM_ON_HOLD
        elif "r" in state.lower() or "t" in state:
            return self.drmaa.JobState.RUNNING
        elif "w" in state:
            return self.drmaa.JobState.QUEUED_ACTIVE
        else:
            log.error("DRMAAUniva: job {job_id} unknown state from qstat: {state}".format(job_id=job_id, state=state))
            return self.drmaa.JobState.UNDETERMINED


# def _check_memory_limit( efile_path ):
#     """
#     A very poor implementation of tail, but it doesn't need to be fancy
#     since we are only searching the last 2K
#     checks for an error message that indicates an memory constraint violation
#     returns True if such an indicator is found and False otherwise
#     """
#     # list of error output from different programming languages in case
#     # of memory allocation errors for bash, Python, C++, JAVA, Perl
#     memerrors = set(["xrealloc: cannot allocate",
#                      "MemoryError",
#                      "std::bad_alloc",
#                      "java.lang.OutOfMemoryError: Java heap space",
#                      "Out of memory!"])
# 
#     try:
#         log.debug( 'Checking %s for exceeded memory messages from programs', efile_path )
#         with open( efile_path ) as f:
#             if os.path.getsize(efile_path) > MEMORY_LIMIT_SCAN_SIZE:
#                 f.seek(-MEMORY_LIMIT_SCAN_SIZE, os.SEEK_END)
#                 f.readline()
#             for line in f.readlines():
#                 stripped_line = line.strip()
#                 for err in memerrors:
#                     if err in stripped_line:
#                         return True
#     except:
#         log.exception('Error reading end of %s:', efile_path)
# 
#     return False


# def _parse_mem( mstring ):
#     mem = None
#     m = re.search( "([0-9.]+)([KGM]?)", mstring )
#     if m is not None:
#         mem = float(m.group(1))
#         if m.group(2) == 'K':
#             mem *= 1024
#         elif m.group(2) == 'M':
#             mem *= 1024 * 1024
#         elif m.group(2) == 'G':
#             mem *= 1024 * 1024 * 1024
#         elif m.group(2) == '':
#             pass
#         else:
#             log.error( "DRMAAUniva: unparsable memory spec {spec}".format(spec=mstring) )
#     return mem


def _parse_time( tstring ):
    tme = None
    m = re.search( "([0-9:.]+)", tstring )
    if m is not None:
        timespl = m.group(1).split(':')
        tme = float( timespl[-1] )  # sec
        if len( timespl ) > 1:     # min
            tme += float( timespl[-2] ) * 60
        if len( timespl ) > 2:     # hour
            tme += float( timespl[-3] ) * 3600
        if len( timespl ) > 3:     # day
            tme += float( timespl[-4] ) * 86400
    return tme


def _parse_native_specs( job_id, native_spec ):
    """
    determine requested run time and memory from native specs
    native_spec (e.g. h_rt=01:00:02 -l h_vmem=1G) the native
    job_id the job ID (only used for logging)
    specification string passed to GE
    return time,mem (or None,None if nothing found)
    """
    tme = None
    mem = None
    # parse time
    m = re.search( "rt=([0-9:]+)[\s,]*", native_spec )
    if m is not None:
        tme = _parse_time( m.group(1) )
        if tme is None:
            log.error( "DRMAAUniva: job {job_id} has unparsable time native spec {spec}".format(job_id=job_id, spec=native_spec) )
    # parse memory
    m = re.search( "mem=([\d.]+[KGMT]?)[\s,]*", native_spec )
    if m is not None:
        mem = util.size_to_bytes( m.group(1) )
        # mem = _parse_mem( m.group(1) )
        if mem is None:
            log.error( "DRMAAUniva: job {job_id} has unparsable memory native spec {spec}".format(job_id=job_id, spec=native_spec) )
    return tme, mem
