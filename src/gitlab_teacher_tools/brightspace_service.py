import pandas


class BrightspaceService:
    def __init__(self, dlo_class_export_csv: str):


        df = pandas.read_csv(dlo_class_export_csv)
        # query unique teams from df
        self.teams = df['Group Name'].unique()

        # query email addresses grouped by group name from df
        self.emails_by_group = df.groupby('Group Name')['Email Address'].apply(list).to_dict()
        self.students_by_group = dict([(g, s.apply(list)) for g, s in df.groupby('Group Name')])


