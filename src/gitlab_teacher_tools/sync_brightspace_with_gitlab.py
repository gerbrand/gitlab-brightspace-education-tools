import os
import shlex
import subprocess

import gitlab
import pandas
from jinja2 import Template

from gitlab_teacher_tools import myenv
from gitlab_teacher_tools.brightspace_service import BrightspaceService
from gitlab_teacher_tools.gitlab_service import GitlabService


def sync_with_brightspace(brightspaceService:BrightspaceService, gitlabService:GitlabService):

    teams = brightspaceService.teams

    emails_by_group = brightspaceService.emails_by_group
    students_by_group = brightspaceService.students_by_group

    for team in teams:
        project, local_team_project_dir= gitlabService.getOrCreateTeamProject(team)

        gitlabService.mergeWithBaseProject(team)

        emails = emails_by_group.get(team)
        existingUsernames = [member.username for member in project.members.list()]
        projectInvitations = project.invitations.list()
        students = students_by_group[team]
        brightspaceUsernames = [n.split('@')[0] for n in students['Username']]

        for idx, brightspaceUsername in enumerate(brightspaceUsernames):
            if not brightspaceUsername in existingUsernames:
                # TODO solve this more elegantly
                email = [e for e in students['Email Address']][idx]
                project.invitations.create(
                    {
                        "email": email,
                        "access_level": gitlab.const.AccessLevel.MAINTAINER,
                    }
                )
                print(f"invitation created for {email}")

def add_teacher_tests(brightspaceService:BrightspaceService, gitlabService:GitlabService, solution_project_dir: str):

    teams = brightspaceService.teams

    for team in teams:
        project, local_team_project_dir = gitlabService.getOrCreateTeamProject(team)

        assignments: list[str] = filter(lambda d : d.startswith("Assignment"), os.listdir(solution_project_dir))
        for assignment in assignments:
            solution_assignment_dir = os.path.join(solution_project_dir, assignment,"src","test")
            team_assignment_dir = os.path.join(local_team_project_dir, assignment)
            if os.path.isdir(solution_assignment_dir):
                result = subprocess.call(shlex.split(f"cp -rvp {solution_assignment_dir} {team_assignment_dir}/src/"))
                if result != 0:
                    raise RuntimeError(f"Error while copying tests for assignment {assignment} to {local_team_project_dir}")