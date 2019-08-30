# Copyright 2013-2015, The James Hutton Insitute
# Author: Leighton Pritchard
#
# This code is part of the pyani package, and is governed by its licence.
# Please see the LICENSE file that should have been included as part of
# this package.

"""Code to run a set of command-line jobs using SGE/Grid Engine

For parallelisation on multi-node system, we use some custom code to submit
jobs.
"""

import itertools
import os

from collections import defaultdict

from . import pyani_config
from .pyani_jobs import (Job, JobGroup)


def split_seq(iterable, size):
    """Splits a passed iterable into chunks of a given size."""
    elm = iter(iterable)
    item = list(itertools.islice(elm, size))
    while item:
        yield item
        item = list(itertools.islice(elm, size))


# Build a list of SGE jobs from a graph
def build_joblist(jobgraph):
    """Returns a list of jobs, from a passed jobgraph."""
    jobset = set()
    for job in jobgraph:
        jobset = populate_jobset(job, jobset, depth=1)
    return list(jobset)


# Convert joblist into jobgroups
def compile_jobgroups_from_joblist(joblist, jgprefix, sgegroupsize):
    """Return list of jobgroups, rather than list of jobs."""
    jobgroups = []
    
    # Break arglist up into batches of sgegroupsize (default: 10,000)
    sublists = split_seq(joblist, sgegroupsize)
    count = 0

    for sublist in sublists:
        count += 1
        sge_jobcmds = ""
        for jc in sublist:
            sge_jobcmds += jc + "\n"
        jobgroups.append(Job("%s_%d" % (jgprefix, count), sge_jobcmds, "0"))
    return jobgroups


# Run a job dependency graph, with SGE
def run_dependency_graph(jobdir, jobgraph, logger=None, jgprefix="ANIm_SGE_JG",
                         sgegroupsize=10000, sgeargs=None):
    """Creates and runs GridEngine scripts for jobs based on the passed
    jobgraph.

    - jobgraph - list of jobs, which may have dependencies.
    - verbose - flag for multiprocessing verbosity
    - logger - a logger module logger (optional)
    - jgprefix - a prefix for the submitted jobs, in the scheduler
    - sgegroupsize - the maximum size for an array job submission
    - sgeargs - additional arguments to qsub

    The strategy here is to loop over each job in the list of jobs (jobgraph),
    and create/populate a series of Sets of commands, to be run in
    reverse order with multiprocessing_run as asynchronous pools.

    The strategy here is to loop over each job in the dependency graph, and
    add the job to a new list of jobs, swapping out the Job dependency for
    the name of the Job on which it depends.
    """
    joblist = build_joblist(jobgraph)

    # Try to be informative by telling the user what jobs will run
    dep_count = 0  # how many dependencies are there
    if logger:
        logger.info("Jobs to run with scheduler")
        for job in joblist:
            logger.info("{0}: {1}".format(job.name, job.command))
            if len(job.dependencies):
                dep_count += len(job.dependencies)
                for dep in job.dependencies:
                    logger.info("\t[^ depends on: %s]" % dep.name)
    logger.info("There are %d job dependencies" % dep_count)

    # If there are no job dependencies, we can use an array (or series of
    # arrays) to schedule our jobs. This cuts down on problems with long
    # job lists choking up the queue.
    if dep_count == 0:
        logger.info("Compiling jobs into JobGroups")
        joblist = compile_jobgroups_from_joblist(joblist, jgprefix,
                                                 sgegroupsize)

    # Send jobs to scheduler
    logger.info("Running jobs with scheduler...")
    logger.info("Jobs passed to scheduler in order:")
    for job in joblist:
        logger.info("\t%s" % job.name)
    build_and_submit_jobs(jobdir, joblist, sgeargs)
    logger.info("Waiting for SGE-submitted jobs to finish (polling)")
    for job in joblist:
        job.wait()


def populate_jobset(job, jobset, depth):
    """ Creates a set of jobs, containing jobs at difference depths of the
    dependency tree, retaining dependencies as strings, not Jobs.
    """
    jobset.add(job)
    if len(job.dependencies) == 0:
        return jobset
    for j in job.dependencies:
        jobset = populate_jobset(j, jobset, depth+1)
    return jobset


def build_directories(root_dir, jobs):
    """Constructs the subdirectories output, stderr, stdout, and jobs in the
    passed root directory. These subdirectories have the following roles:

        jobs             Stores the scripts for each job
        stderr           Stores the stderr output from SGE
        stdout           Stores the stdout output from SGE
        output           Stores output (if the scripts place the output here)

    - root_dir   Path to the top-level directory for creation of subdirectories
    """
    # If the root directory doesn't exist, create it
    if not os.path.exists(root_dir):
        os.mkdir(root_dir)
    sge_dir = os.path.join(root_dir, "sge")
    if not os.path.exists(sge_dir):
        os.mkdir(sge_dir)

    # Create subdirectories
    jobdir = os.path.join(sge_dir, "jobs")
    stdout_dir = os.path.join(sge_dir, "stdout")
    stderr_dir = os.path.join(sge_dir, "stderr")
    os.makedirs(jobdir, exist_ok=True)
    os.makedirs(stdout_dir, exist_ok=True)
    os.makedirs(stderr_dir, exist_ok=True)

    for job in jobs:
        sub_job_dir = os.path.join(jobdir, job.index)
        sub_out_dir = os.path.join(stdout_dir, job.index)
        sub_err_dir = os.path.join(stderr_dir, job.index)
        os.makedirs(sub_job_dir, exist_ok=True)
        os.makedirs(sub_out_dir, exist_ok=True)
        os.makedirs(sub_err_dir, exist_ok=True)


def build_job_scripts(root_dir, jobs):
    """Constructs the script for each passed Job in the jobs iterable

    - root_dir      Path to output directory
    """
    # Loop over the job list, creating each job script in turn, and then adding
    # scriptPath to the Job object
    job_dir = os.path.join(root_dir, "sge/jobs")
    for job in jobs:
        subjob_dir = os.path.join(job_dir, job.index)
        scriptpath = os.path.join(subjob_dir, job.name)
        with open(scriptpath, "w") as scriptfile:
            scriptfile.write("#!/bin/sh\n#$ -S /bin/bash\n%s\n" % job.script)
        job.scriptpath = scriptpath


def extract_submittable_jobs(waiting):
    """Obtain a list of jobs that are able to be submitted from the passed
    list of pending jobs

    - waiting           List of Job objects
    """
    submittable = set()            # Holds jobs that are able to be submitted
    # Loop over each job, and check all the subjobs in that job's dependency
    # list.  If there are any, and all of these have been submitted, then
    # append the job to the list of submittable jobs.
    for job in waiting:
        unsatisfied = sum([(subjob.submitted is False) for subjob in
                           job.dependencies])
        if unsatisfied == 0:
            submittable.add(job)
    return list(submittable)


def submit_safe_jobs(root_dir, jobs, sgeargs=None):
    """Submit the passed list of jobs to the Grid Engine server, using the
    passed directory as the root for scheduler output.

    - root_dir      Path to output directory
    - jobs          Iterable of Job objects
    """
    # Loop over each job, constructing SGE command-line based on job settings
    for job in jobs:
        job.out = os.path.join(root_dir, "sge/stdout/%s" % job.index)
        job.err = os.path.join(root_dir, "sge/stderr/%s" % job.index)

        # Add the job name, current working directory, and SGE stdout/stderr
        # directories to the SGE command line
        args = " -N %s " % (job.name)
        args += " -cwd "
        args += " -o %s -e %s " % (job.out, job.err)

        # If a queue is specified, add this to the SGE command line
        # LP: This has an undeclared variable, not sure why - delete?
        #if job.queue is not None and job.queue in local_queues:
        #    args += local_queues[job.queue]

        # If the job is actually a JobGroup, add the task numbering argument
        if isinstance(job, JobGroup):
            args += "-t 1:%d " % (job.tasks)

        # If there are dependencies for this job, hold the job until they are
        # complete
        if len(job.dependencies) > 0:
            args += "-hold_jid "
            for dep in job.dependencies:
                args += dep.name + ","
            args = args[:-1]

        # Build the qsub SGE commandline (passing local environment)
        qsubcmd = ("%s -V %s" % (pyani_config.QSUB_DEFAULT, args))
        if sgeargs is not None:
            qsubcmd = "%s %s %s" % (qsubcmd, sgeargs, job.scriptpath)
        os.system(qsubcmd)               # Run the command
        job.submitted = True             # Set the job's submitted flag to True


def submit_jobs(root_dir, jobs, sgeargs=None):
    """ Submit each of the passed jobs to the SGE server, using the passed
    directory as root for SGE output.

    - root_dir       Path to output directory
    - jobs           List of Job objects
    """
    waiting = list(jobs)                 # List of jobs still to be done
    # Loop over the list of pending jobs, while there still are any
    while len(waiting) > 0:
        # extract submittable jobs
        submittable = extract_submittable_jobs(waiting)
        # run those jobs
        submit_safe_jobs(root_dir, submittable, sgeargs)
        # remove those from the waiting list
        for job in submittable:
            waiting.remove(job)


def build_and_submit_jobs(root_dir, jobs, sgeargs=None):
    """Submits the passed iterable of Job objects to SGE, placing SGE's
    output in the passed root directory

    - root_dir   Root directory for SGE and job output
    - jobs       List of Job objects, describing each job to be submitted
    - sgeargs    Additional arguments to qsub
    """
    # If the passed set of jobs is not a list, turn it into one. This makes the
    # use of a single JobGroup a little more intutitive
    if not isinstance(jobs, list):
        jobs = [jobs]

    # Build and submit the passed jobs
    build_directories(root_dir, jobs)        # build all necessary directories
    build_job_scripts(root_dir, jobs)  # build job scripts
    submit_jobs(root_dir, jobs, sgeargs)        # submit the jobs to SGE
