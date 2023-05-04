import os


tenants = [
    {
        'name': 'designsafe',
        'proper_name': 'DesignSafe',
        'directories': ['CommunityData', 'MyData', 'MyProjects', 'NEES', 'NHERI-Published'],
        'primary_receiver': os.environ.get('DS_PRIMARY_RECIPIENT', []),
        'recipients': os.environ.get('DS_EMAIL_RECIPIENTS', [])
    },
    {
        'name': 'tacc',
        'proper_name': 'TACC',
        'directories': ['team_classify', 'Hobby-Eberly-Telesco', 'HETDEX-Work', 'Hobby-Eberly-Public', 'work'],
        'primary_receiver': os.environ.get('TACC_PRIMARY_RECIPIENT', []),
        'recipients': os.environ.get('TACC_EMAIL_RECIPIENTS', [])
    },
]