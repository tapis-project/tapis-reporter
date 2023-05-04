from agavepy import Agave
from tapipy.tapis import Tapis
from django.conf import settings
import json


def get_config_metadata_name():
    return f"config.{settings.TENANT}.{settings.INSTANCE}.jhub"

def get_group_config_metadata_name(group):
    return f"{group}.group.{get_config_metadata_name()}"

def get_tapis_client():
    return Tapis(base_url=settings.TAPIS_API, jwt=settings.TAPIS_SERVICE_TOKEN)

def get_tapis_config_metadata():
    t = get_tapis_client()
    filter = {"name": get_config_metadata_name()}
    metadata = t.meta.listDocuments(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", filter=json.dumps(filter))
    return json.loads(metadata)[0]

def list_tapis_group_config_metadata():
    t = get_tapis_client()
    filter = {'name':{'$regex':f".*group.{get_config_metadata_name()}"}}
    metadata = t.meta.listDocuments(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", filter=json.dumps(filter))
    return json.loads(metadata)

def get_tapis_group_config_metadata(group):
    t = get_tapis_client()
    filter = {'name': get_group_config_metadata_name(group)}
    metadata = t.meta.listDocuments(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", filter=json.dumps(filter))
    return json.loads(metadata)[0]

def write_tapis_group_config_metadata(group, value):
    t = get_tapis_client()
    meta = get_tapis_group_config_metadata(group)
    print("************** " * 30)
    meta['value'] = value
    print(meta)
    t.meta.modifyDocument(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", request_body=meta, docId=meta['_id']['$oid'])

def create_tapis_group_config_metadata(group):
    t = get_tapis_client()
    meta = {
        "name": get_group_config_metadata_name(group),
        "value": {
            "tenant": settings.TENANT,
            "instance": settings.INSTANCE,
            "user": [],
            "images": [],
            "config_type": "group",
            "volume_mounts": [],
            "group_name": group,
            "name": get_group_config_metadata_name(group)
        }
    }
    t.meta.createDocument(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", basic='true', request_body=meta)

def rename_tapis_group_config_metadata(original, group):
    t = get_tapis_client()
    meta = get_tapis_group_config_metadata(original)
    new_meta_name = get_group_config_metadata_name(group)
    meta['name'] = new_meta_name
    meta['value']['group_name'] = group
    meta['value']['name'] = new_meta_name
    t.meta.modifyDocument(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", request_body=meta, docId=meta['_id']['$oid'])

def delete_tapis_group_config_metadata(group):
    t = get_tapis_client()
    meta = get_tapis_group_config_metadata(group)
    t.meta.deleteDocument(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", docId=meta['_id']['$oid'])

def get_admin_tenant_metadata():
    t = get_tapis_client()
    metadata = t.meta.listDocuments(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}")
    matching = []
    for entry in metadata:
        if 'admin_users' in entry['value'] and settings.TENANT in entry['value']['admin_users']:
            matching.append(entry)
    return matching

def write_tapis_config_metadata(value):
    t = get_tapis_client()
    meta = get_tapis_config_metadata()
    meta['value'] = value
    t.meta.modifyDocument(db='jupyterhub_v3_metadata', collection=f"jupyterhub_{settings.INSTANCE}", request_body=meta, docId=meta['_id']['$oid'])


def set_config(key, value):
    current = get_tapis_config_metadata()['value']
    current[key] = value
    write_tapis_config_metadata(current)
