from pathlib import Path
import sys,json,copy
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'reference'))
from image_selection import consumer,prepare,verify_after,no_active_executions
old='exampleregistry.azurecr.io/carebridge/importer@sha256:'+'1'*64
new='exampleregistry.azurecr.io/carebridge/importer@sha256:'+'2'*64
spec={'name':'job-example-carebridge','resourceId':'/subscriptions/00000000-0000-4000-8000-000000000000/resourceGroups/rg-example/providers/Microsoft.App/jobs/job-example-carebridge','repository':'exampleregistry.azurecr.io/carebridge/importer','retired':False}
def example():
 before={'id':spec['resourceId'],'name':spec['name'],'identity':{'type':'UserAssigned'},'tags':{'environment':'example'},'properties':{'configuration':{'triggerType':'Manual','replicaRetryLimit':0},'template':{'containers':[{'name':'worker','image':old,'env':[{'name':'CAREBRIDGE_WORKER_ENABLED','value':'false'}]}]}}}
 selected=consumer({'consumers':[spec]},spec['name'],new);no_active_executions([])
 body=prepare(before,selected,old,new);after=copy.deepcopy(before);after['properties']['template']=body['properties']['template'];verify_after(before,after,body)
 return {'fictional':True,'azureRequests':0,'imageChangePrepared':True,'settingsPreserved':True,'triggerType':after['properties']['configuration']['triggerType'],'workerEnabled':False,'jobStarted':False}
if __name__=='__main__':print(json.dumps(example(),indent=2))
