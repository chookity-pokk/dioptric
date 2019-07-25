# -*- coding: utf-8 -*-
"""This script will archive branches. A branch should be archived if you're
done working with it so that it doesn't clutter the repo. Generally we want
a record of our work so we don't want to delete branches outright.

Archiving is done by tagging them as archive/<branchname> and removing them
both locally and remotely. Before each operation, the user is asked for
confirmation.

Created on Mon Jun 10 08:02:12 2019

@author: mccambria
"""


# %% Imports


import time
from git import Repo


# %% Functions


def parse_string_array(string_array):
    """Raw git commands return string arrays, such as:
    [' ', ' ', 'd', 'e', 'b', 'u', 'g', '-', 'f', 'u', 'n', 'c',
    't', 'i', 'o', 'n', '\n', ' ', 'm', 'a', 's', 't', 'e', 'r']
    How terrible is that. We need to parse them. White spaces mean nothing
    to us. New lines are delimiters.
    """
    vals = []
    val = ''
    for char in string_array:
        if char == ' ':
            continue
        elif char == '\n':
            vals.append(val)
            val = ''
        else:
            val += char
    return vals


# %% Main


def main(repo_path, branches_to_archive):

    # Get the repo and the remote origin
    repo = Repo(repo_path)
    repo_git = repo.git
    origin = repo.remotes.origin
    
    # Get fully merged branches
    merged_branches = parse_string_array(repo_git.branch('--merged', 'master'))
    merged_branches = [branch for branch in merged_branches
                        if branch != '' and not '*' in branch and not branch == 'master']
    print('Merged branches:')
    print(merged_branches)
    
    # Get all local branches
    local_branches = parse_string_array(repo_git.branch('-l'))
    local_branches  = [branch for branch in local_branches
                        if branch != '' and not '*' in branch and not branch == 'master']
    print('\nLocal branches:')
    print(local_branches)
    
    # Confirm that the branch should be deleted
    archived_branches = []
    tagged_branches = []
    for branch in branches_to_archive:
        archive = True
        if branch == 'master':
            print("I'm sorry Dave. I'm afraid I can't archive the master branch.")
            archive = False
        elif branch not in local_branches:
            print('Branch {} does not exist locally for this repo. Skipping.'.format(branch))
            archive = False
        elif branch not in merged_branches:
            msg = 'Branch {} is not fully merged with master. Archive anyway? '
        else:
            msg = 'Archive branch {}? '
        if archive and not input(msg.format(branch)).startswith('y'):
            archive = False
        if archive:  # Change to if True to override checks
            # Add a timestamp to the tagged branch
            inst = int(time.time())
            tagged_name = '{}-{}'.format(branch, inst)
            repo_git.tag(r'archive/{}'.format(tagged_name), branch)
            archived_branches.append(branch)
            tagged_branches.append(tagged_name)
    
    if archived_branches == []:
        print('No branches archived.')
    
    # Push archive tags to remote
    for branch in tagged_branches:
        try:
            print('tagging')
            origin.push(r'archive/{}'.format(branch))
            print('tagged')
        except Exception as e:
            print(e)
    
    # Delete remote branches
    for branch in archived_branches:
        try:
            print('deleting remote')
            origin.push(':{}'.format(branch))
            print('deleted remote')
        except Exception as e:
            print(e)
    
    # Delete local branches
    for branch in archived_branches:
        try:
            print('deleting local')
            repo_git.branch('-D', branch)
            print('deleted local')
        except Exception as e:
            print(e)


# %% Run the file


if __name__ == '__main__':

    
    # Path to your local checkout of the repo
    # repo_path = 'C:\\Users\\kolkowitz\\Documents\\GitHub\\kolkowitz-nv-experiment-v1.0'
    repo_path = 'C:\\Users\\matth\\Documents\\GitHub\\kolkowitz-nv-experiment-v1.0'
    #repo_path = 'C:\\Users\\Aedan\\Documents\\GitHub\\kolkowitz-nv-experiment-v1.0'
    
    # List of branches to archive
    branches_to_archive = ['ramsey3']

    main(repo_path, branches_to_archive)
