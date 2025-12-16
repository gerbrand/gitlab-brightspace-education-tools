import argparse
import sys

from gitlab_teacher_tools import myenv
from gitlab_teacher_tools import sync_brightspace_with_gitlab
from gitlab_teacher_tools.brightspace_service import BrightspaceService
from gitlab_teacher_tools.gitlab_service import GitlabService


def main() -> None:
    parser = argparse.ArgumentParser(prog='gitlab-brightspace', usage='Sync gitlab projects with teams in Brightspace')
    parser.add_argument("--subject",
                        help="Subject for which to create or update projects. Should be one in config file",
                        type=str)
    parser.add_argument( "action",
                         choices=["sync"],
                        help="What to do, by default sync with Brightspace with gitlab using supplied csv export",
                        type=str)
    args = parser.parse_args()

    config = myenv.config

    subject_config = config[args.subject]
    maybe_students_group_id = subject_config.getint('students_group_id')
    students_group_id: int
    if maybe_students_group_id:
        students_group_id = maybe_students_group_id



        # Csv file with team names and email addresses, as exported from DLO (Brightspace)
        # Can be exported via Cursusbeheerder, Cursistenbeheer, Groepen
        dlo_class_export_csv = subject_config['dlo_class_export_csv']
        # Base project on which student repos will be based on
        base_project_url = subject_config['base_project_url']
        # Directory where student repos will be cloned to
        local_teams_dir = subject_config['local_teams_dir']

        gl = myenv.gl
        brightspaceService = BrightspaceService(dlo_class_export_csv)
        gitlabService = GitlabService(gl, students_group_id, local_teams_dir, base_project_url = base_project_url)

        if args.action == "sync":
            sync_brightspace_with_gitlab.sync_with_brightspace(brightspaceService, gitlabService)
    else:
        # TODO should solve this in a more proper way. Can I define a config parser?
        sys.stderr.writelines("Missing students_group_id")
        sys.exit(1)



if __name__ == "__main__":
    main()