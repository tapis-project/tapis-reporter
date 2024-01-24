services = [
    {
        "name": "jupyterhub",
        "admins": ["gcurbelo"],
        "tenants": [
            {
                'name': 'designsafe',
                'proper_name': 'DesignSafe',
                'directories': ['CommunityData', 'MyData', 'MyProjects', 'NEES', 'NHERI-Published'],
                'primary_receiver': 'gcurbelo@tacc.utexas.edu',
                'recipients': ['gcurbelo@tacc.utexas.edu']
            },
            {
                'name': 'tacc',
                'proper_name': 'TACC',
                'directories': ['team_classify', 'Hobby-Eberly-Telesco', 'HETDEX-Work', 'Hobby-Eberly-Public', 'work'],
                'primary_receiver': 'jstubbs@tacc.utexas.edu',
                'recipients': ['jstubbs@tacc.utexas.edu', 'ajamthe@tacc.utexas.edu', 'gcurbelo@tacc.utexas.edu', 'hammock@tacc.utexas.edu']
            },
        ]
    },
    {
        "name": "tapis",
        "admins": ["gcurbelo", "jstubbs"],
        "tenants": [
            {
                'name': 'tacc',
                'proper_name': 'TACC',
                'primary_receiver': 'jstubbs@tacc.utexas.edu',
                'key_name': 'TAPIS_SERVICE_TOKEN'
            },
            {
                'name': 'dev.develop',
                'proper_name': 'Dev',
                'primary_receiver': 'jstubbs@tacc.utexas.edu',
                'key_name': 'DEV_TAPIS_TOKEN'
            }
        ]
    }
]