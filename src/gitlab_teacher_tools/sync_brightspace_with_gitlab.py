import os
import subprocess

import gitlab
import pandas
from jinja2 import Template

from gitlab_teacher_tools import myenv
from gitlab_teacher_tools.brightspace_service import BrightspaceService
from gitlab_teacher_tools.gitlab_service import GitlabService


def sync_with_brightspace(students_group_id: int, dlo_class_export_csv: str, base_project_url: str, local_teams_dir: str):
    gl = myenv.gl

    brightspaceService = BrightspaceService(dlo_class_export_csv)
    gitlabService = GitlabService(gl, students_group_id, local_teams_dir)

    teams = brightspaceService.teams

    emails_by_group = brightspaceService.emails_by_group
    students_by_group = brightspaceService.students_by_group

    for team in teams:
        project = gitlabService.getOrCreateTeamProject(team)

        git_url = project.ssh_url_to_repo
        result_clone=subprocess.call(['git', 'clone', git_url], cwd = local_teams_dir)
        local_team_project_dir = gitlabService.localTeamProjectDir(team)
        result_remote = subprocess.call(['git', 'remote', 'add', 'base_project', base_project_url], cwd = local_team_project_dir)
        if result_remote == 0 or result_remote == 3:
            result_pull = subprocess.call(['git', 'pull'], cwd=local_team_project_dir)
            subprocess.call(['git', 'fetch', 'base_project'], cwd = local_team_project_dir)
            result_merge = subprocess.call(['git', 'merge', 'base_project/master'], cwd = local_team_project_dir)
            if result_merge == 0:
                # Open README.md.jinja
                tempfileFile = f"{local_team_project_dir}/README.md.jinja"
                if os.path.exists(tempfileFile):
                    template = Template(open(tempfileFile, "r").read())
                    templateVars = {"team": team}
                    output = template.render(templateVars)
                    with open(f"{local_team_project_dir}/README.md", "w") as f:
                        f.write(output)


                    subprocess.call(['git', 'add', 'README.md'], cwd=local_team_project_dir)
                    subprocess.call(['git', 'rm', '-f', 'README.md.jinja'], cwd=local_team_project_dir)
                    subprocess.call(['git', 'commit', '-m', 'Update README.md'], cwd=local_team_project_dir)

                subprocess.call(['git', 'push'], cwd = local_team_project_dir)
            else:
                # throw exception
                print(f"Merge failed for {team}")
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
