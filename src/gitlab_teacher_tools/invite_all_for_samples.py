"""
Invite students to any sample projects, that should be available for all students.

Use this if you have sample code which you do not wanto make public but do want accessible for all.

"""
import configparser

import gitlab
import pandas

def main():
    config = configparser.ConfigParser()
    config.read('semester_in_gitlab.ini')

    subject_config = config['ads']
    # Csv file with team names and email addresses, as exported from DLO (Brightspace)
    # Can be exported via Cursusbeheerder, Cursistenbeheer, Groepen
    dlo_class_export_csv = subject_config['dlo_class_export_csv']

    sample_project_ids = subject_config['sample_project_ids'].split(',')

    gl = gitlab.Gitlab.from_config('hva', ['./gl.cfg'])

    df = pandas.read_csv(dlo_class_export_csv)

    for email in df['Email Address'].unique():
        for project_id in sample_project_ids:
            project = gl.projects.get(project_id)
            project.invitations.create(
                {
                    "email": email,
                    "access_level": gitlab.const.AccessLevel.REPORTER,
                }
            )

if __name__ == "__main__":
    main()