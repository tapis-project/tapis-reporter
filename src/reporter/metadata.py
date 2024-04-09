from tapipy.tapis import Tapis
from django.conf import settings
import json


def get_config_metadata_name():
    return settings.METADATA_NAME


def get_group_config_metadata_name(group):
    return f"{group}.group.{get_config_metadata_name()}"


def get_tapis_client():
    return Tapis(base_url=settings.TAPIS_API, jwt=settings.TAPIS_SERVICE_TOKEN)


def get_tapis_config_metadata():
    t = get_tapis_client()
    filter = {"name": get_config_metadata_name()}
    metadata = t.meta.listDocuments(
        db="jupyterhub_v3_metadata",
        collection=f"jupyterhub_{settings.INSTANCE}",
        filter=json.dumps(filter),
    )
    return json.loads(metadata)[0]


def list_tapis_group_config_metadata():
    t = get_tapis_client()
    filter = {"name": {"$regex": f".*group.{get_config_metadata_name()}"}}
    metadata = t.meta.listDocuments(
        db="jupyterhub_v3_metadata",
        collection=f"jupyterhub_{settings.INSTANCE}",
        filter=json.dumps(filter),
    )
    return json.loads(metadata)


def get_tapis_group_config_metadata(group):
    t = get_tapis_client()
    filter = {"name": get_group_config_metadata_name(group)}
    metadata = t.meta.listDocuments(
        db="jupyterhub_v3_metadata",
        collection=f"jupyterhub_{settings.INSTANCE}",
        filter=json.dumps(filter),
    )
    return json.loads(metadata)[0]
