import os
import subprocess

import gitlab
import pandas
from jinja2 import Template

import myenv
from gitlab_teacher_tools.brightspace_service import BrightspaceService
from gitlab_teacher_tools.gitlab_service import GitlabService


def sync_with_brightspace(students_group_id: str, dlo_class_export_csv: str, base_project_url: str, local_teams_dir: str, solution_project_url: str | None = None):
    gl = myenv.gl

    brightspaceService = BrightspaceService(dlo_class_export_csv)
    gitlabService = GitlabService(gl, students_group_id)

    teams = brightspaceService.teams

    emails_by_group = brightspaceService.emails_by_group
    students_by_group = brightspaceService.students_by_group

    # result_clone = subprocess.call(['git', 'clone', solution_project_url], cwd=local_teams_dir)
    # assert(result_clone == 0 or result_clone == 3)
    # solutions_dir = f"{local_teams_dir}/teamsolutions"
    # result_pull = subprocess.call(['git', 'pull'], cwd=solutions_dir)
    # assert (result_pull == 0)

    for team in teams:
        project = gitlabService.getOrCreateTeamProject(team)

        git_url = project.ssh_url_to_repo
        result_clone=subprocess.call(['git', 'clone', git_url], cwd = local_teams_dir)
        local_dir = f"{local_teams_dir}/{team.replace(" ", "-")}"
        result_remote = subprocess.call(['git', 'remote', 'add', 'base_project', base_project_url], cwd = local_dir)
        if result_remote == 0 or result_remote == 3:
            result_pull = subprocess.call(['git', 'pull'], cwd=local_dir)
            subprocess.call(['git', 'fetch', 'base_project'], cwd = local_dir)
            result_merge = subprocess.call(['git', 'merge', 'base_project/master'], cwd = local_dir)
            if result_merge == 0:
                # Open README.md.jinja
                tempfileFile = f"{local_dir}/README.md.jinja"
                if os.path.exists(tempfileFile):
                    template = Template(open(tempfileFile, "r").read())
                    templateVars = {"team": team}
                    output = template.render(templateVars)
                    with open(f"{local_dir}/README.md", "w") as f:
                        f.write(output)


                    subprocess.call(['git', 'add', 'README.md'], cwd=local_dir)
                    subprocess.call(['git', 'rm', '-f', 'README.md.jinja'], cwd=local_dir)
                    subprocess.call(['git', 'commit', '-m', 'Update README.md'], cwd=local_dir)

                subprocess.call(['git', 'push'], cwd = local_dir)
            else:
                # throw exception
                print(f"Merge failed for {team}")
            # result = subprocess.call(f"cp -rvp {solutions_dir}/src/test/* {local_dir}/", cwd=solutions_dir)
            # assert(result == 0)
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
