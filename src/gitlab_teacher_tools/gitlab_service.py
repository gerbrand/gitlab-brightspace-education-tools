from gitlab import Gitlab
from gitlab.v4.objects import Group, Project


def get_group(gl: Gitlab, students_group_id: int) -> Group:
    return gl.groups.get(students_group_id)

class GitlabService:
    students_group: Group

    def __init__(self, gl: Gitlab, students_group_id: int, local_teams_dir: str):
        self.gl = gl
        self.students_group = get_group(gl, students_group_id)
        self.existing_projects = dict([(p.name, p) for p in self.students_group.projects.list(get_all=True)])
        self.local_teams_dir = local_teams_dir

    def getOrCreateTeamProject(self, team: str) -> Project:
        group_project = self.existing_projects.get(team)
        if group_project:
            project = self.gl.projects.get(group_project.id)
        else:
            project = self.gl.projects.create({'name': team, 'namespace_id': self.students_group.get_id()})
        return project

    def localTeamProjectDir(self, team: str) -> str:
        return f"{self.local_teams_dir}/{team.replace(" ", "-")}"
