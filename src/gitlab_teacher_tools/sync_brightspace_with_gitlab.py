import os
import subprocess

import gitlab
import pandas
from jinja2 import Template

import myenv


def sync_with_brightspace(students_group_id: str, dlo_class_export_csv: str, base_project_url: str, local_teams_dir: str):
    gl = myenv.gl

    group = gl.groups.get(students_group_id)

    df = pandas.read_csv(dlo_class_export_csv)
    #query unique teams from df
    teams = df['Group Name'].unique()

    #query email addresses grouped by group name from df
    emails_by_group = df.groupby('Group Name')['Email Address'].apply(list).to_dict()
    students_by_group = dict([(g,s.apply(list)) for g,s in df.groupby('Group Name')])

    existing_projects = dict([(p.name, p) for p in group.projects.list(get_all=True)])

    for team in teams:
        group_project = existing_projects.get(team)
        if group_project:
            project = gl.projects.get(group_project.id)
        else:
            project = gl.projects.create({'name': team, 'namespace_id': students_group_id})
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
