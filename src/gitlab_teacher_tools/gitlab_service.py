import subprocess
from typing import Tuple

from gitlab import Gitlab
from gitlab.v4.objects import Group, Project


def get_group(gl: Gitlab, students_group_id: int) -> Group:
    return gl.groups.get(students_group_id)

class GitlabService:
    students_group: Group

    def __init__(self, gl: Gitlab, students_group_id: int, local_teams_dir: str, base_project_url: str):
        self.gl = gl
        self.students_group = get_group(gl, students_group_id)
        self.existing_projects = dict([(p.name, p) for p in self.students_group.projects.list(get_all=True)])
        self.local_teams_dir = local_teams_dir
        self.base_project_url = base_project_url

    def getOrCreateTeamProject(self, team: str) ->  Tuple[Project, str]:
        group_project = self.existing_projects.get(team)
        if group_project:
            project = self.gl.projects.get(group_project.id)
        else:
            project = self.gl.projects.create({'name': team, 'namespace_id': self.students_group.get_id()})

        git_url = project.ssh_url_to_repo
        result_clone=subprocess.call(['git', 'clone', git_url], cwd = self.local_teams_dir)

        local_team_project_dir = self.localTeamProjectDir(team)
        result_remote = subprocess.call(['git', 'remote', 'add', 'base_project', self.base_project_url], cwd = local_team_project_dir)

        if result_remote == 0 or result_remote == 3:
            return (project, local_team_project_dir)
        else:
            raise RuntimeError(f"Error while updating {local_team_project_dir}")

    def localTeamProjectDir(self, team: str) -> str:
        return f"{self.local_teams_dir}/{team.replace(" ", "-")}"
