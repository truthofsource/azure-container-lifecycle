"""Actual pure selection guards; Azure adapter and CLI intentionally omitted."""
import copy
import image_contract as trust

def consumer(policy, name, image):
    values = [x for x in policy['consumers'] if x['name'] == name]
    if len(values) != 1 or values[0]['retired']:
        raise ValueError('consumer_unregistered_or_retired')
    value = values[0]
    if not trust.IMAGE.fullmatch(image) or image.split('@')[0] != value['repository']:
        raise ValueError('consumer_repository_mismatch')
    return value

def prepare(before, spec, current, selected):
    if before.get('id','').lower() != spec['resourceId'].lower() or before.get('name') != spec['name']:
        raise ValueError('consumer_live_identity_mismatch')
    template = copy.deepcopy(before['properties']['template'])
    containers = template.get('containers', [])
    if len(containers) != 1 or containers[0].get('image') != current or not trust.IMAGE.fullmatch(current):
        raise ValueError('current_image_or_container_mismatch')
    containers[0]['image'] = selected
    return {'properties': {'template': template}}

def verify_after(before, after, body):
    if before.get('id','').lower() != after.get('id','').lower() or before.get('identity') != after.get('identity') or before.get('tags') != after.get('tags'):
        raise ValueError('consumer_identity_or_tags_changed')
    expected = copy.deepcopy(before['properties']);expected['template'] = body['properties']['template']
    actual = copy.deepcopy(after['properties'])
    for value in (expected, actual): value.pop('provisioningState',None)
    if expected != actual:
        raise ValueError('unrelated_consumer_configuration_changed')
    return True

def no_active_executions(items):
    if not isinstance(items, list): raise ValueError('execution_inventory_incomplete')
    # Unknown statuses cannot prove the job is idle.
    if any(x.get('properties',{}).get('status') not in ('Succeeded','Failed','Stopped') for x in items):
        raise ValueError('consumer_execution_not_quiescent')
