import itertools
import os

import gitlab
import pandas
import subprocess

from gitlab import GitlabCreateError
from jinja2 import Template
import argparse
import configparser


def main() -> None:
    # Group where teams repos for students will be created

    parser = argparse.ArgumentParser(prog='gitlab-brightspace', usage='Sync gitlab projects with teams in Brightspace')
    parser.add_argument("--subject", help="Subject for which to create or update projects. Should be one in config file",
                        type=str)
    args = parser.parse_args()

    config = configparser.ConfigParser()
    # config['wef'] = {
    #     'students_group_id': '67587',
    #     'dlo_class_export_csv': 'resources/Web Frameworks DT 20252026_AllGroups_20250905091127.csv',
    #     'base_project_url': 'git@gitlab.fdmci.hva.nl:WEF/teamxx.git',
    #     'local_teams_dir': '/home/gerbrand/workspace/HvA/WEF/teams'
    # }
    #
    # config['ads'] = {
    #     'students_group_id': '66447',
    #     'dlo_class_export_csv': 'resources/ADS DT 20252026_AllGroups_20250905091127.csv',
    #     'base_project_url': 'git@gitlab.fdmci.hva.nl:ads/teamxx.git',
    #     'local_teams_dir': '/home/gerbrand/workspace/HvA/ADS/teams'
    # }
    # with open('semester_in_gitlab.ini', 'w') as configfile:
    #     config.write(configfile)
    config.read('semester_in_gitlab.ini')

    subject_config = config[args.subject]
    # Settings for WEF
    # students_group_id = '67587'
    # # Csv file with team names and email addresses, as exported from DLO (Brightspace)
    # dlo_class_export_csv = 'resources/Web Frameworks DT 20252026_AllGroups_20250905091127.csv'
    # # Base project on which student repos will be based on
    # base_project_url = "git@gitlab.fdmci.hva.nl:WEF/teamxx.git"
    # # Directory where student repos will be cloned to
    # local_teams_dir = "/home/gerbrand/workspace/HvA/WEF/teams"
    # Settings for ADS
    students_group_id = subject_config['students_group_id']
    # Csv file with team names and email addresses, as exported from DLO (Brightspace)
    # Can be exported via Cursusbeheerder, Cursistenbeheer, Groepen
    dlo_class_export_csv = subject_config['dlo_class_export_csv']
    # Base project on which student repos will be based on
    base_project_url = subject_config['base_project_url']
    # Directory where student repos will be cloned to
    local_teams_dir = subject_config['local_teams_dir']

    gl = gitlab.Gitlab.from_config('hva', ['./gl.cfg'])

    group = gl.groups.get(students_group_id)
    print(group)

    df = pandas.read_csv(dlo_class_export_csv)
    #query unique teams from df
    teams = df['Group Name'].unique()

    #query email addresses grouped by group name from df
    emails_by_group = df.groupby('Group Name')['Email Address'].apply(list).to_dict()

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
        if result_remote == 0 or True:
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
        for email in emails:
            project.invitations.create(
                {
                    "email": email,
                    "access_level": gitlab.const.AccessLevel.MAINTAINER,
                }
            )
            print(f"invitation created for {email}")




if __name__ == "__main__":
    main()