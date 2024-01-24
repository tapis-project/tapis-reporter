def get_home_path(tenant):
    """
    Set home path based off of tenant

    :return: home path of tenant
    """
    home_paths = {
        'tacc': '/home/jovyan',
        'designsafe': '/home/jupyter'
    }
    return home_paths.get(tenant, "")


def get_symbolic_links(tenant):
    """
    Set symbolic link based off of tenant

    :return: symbolic link(s) of tenant
    """
    symbolic_links = {
        'tacc': {
            '/home/jovyan/shared': '/home/jovyan/team_classify/shared'
        },
        'designsafe': {
            '/home/jupyter/community': '/home/jupyter/CommunityData',
            '/home/jupyter/mydata': '/home/jupyter/MyData',
            '/home/jupyter/projects': '/home/jupyter/MyProjects'
        }
    }
    return symbolic_links.get(tenant, {})
