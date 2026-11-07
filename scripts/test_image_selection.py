import sys,copy,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reference'))
from image_selection import consumer,prepare,verify_after,no_active_executions
from demo import example,spec,old,new
def before():return {'id':spec['resourceId'],'name':spec['name'],'identity':{'type':'UserAssigned'},'tags':{'environment':'example'},'properties':{'configuration':{'triggerType':'Manual'},'template':{'containers':[{'image':old,'env':[{'name':'enabled','value':'false'}]}]}}}
class SelectionTests(unittest.TestCase):
 def test_selection_does_not_start_work(self):self.assertEqual(example()['jobStarted'],False)
 def test_wrong_repository_and_retired_consumer_refused(self):
  for s,image in [(spec,new.replace('/carebridge/','/other/')),({**spec,'retired':True},new)]:
   with self.assertRaises(ValueError):consumer({'consumers':[s]},s['name'],image)
 def test_moved_current_image_refused(self):
  with self.assertRaises(ValueError):prepare(before(),spec,new,new)
 def test_active_or_unknown_execution_refused(self):
  for state in ['Running','Processing','Unknown']:
   with self.assertRaises(ValueError):no_active_executions([{'properties':{'status':state}}])
 def test_settings_change_is_not_an_image_only_release(self):
  b=before();body=prepare(b,spec,old,new);a=copy.deepcopy(b);a['properties']['template']=body['properties']['template'];a['properties']['configuration']['triggerType']='Schedule'
  with self.assertRaises(ValueError):verify_after(b,a,body)
 def test_identity_change_refused(self):
  b=before();body=prepare(b,spec,old,new);a=copy.deepcopy(b);a['identity']={'type':'SystemAssigned'}
  with self.assertRaises(ValueError):verify_after(b,a,body)
if __name__=='__main__':unittest.main()
