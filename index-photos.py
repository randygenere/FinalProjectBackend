import json
import urllib.parse
import boto3
import requests
import inflect

# Test Code Pipeline
s3 = boto3.client('s3')
rekognition = boto3.client('rekognition')
p = inflect.engine()

endpoint = "https://search-photos-rcgm42jp6ggwagmaclqlhvx77a.us-east-1.es.amazonaws.com"
headers = { "Content-Type": "application/json" }

def lambda_handler(event, context):
    bucket = event['Records'][0]['s3']['bucket']['name']
    key = urllib.parse.unquote_plus(event['Records'][0]['s3']['object']['key'], encoding='utf-8')
    timestamp = event['Records'][0]['eventTime']
    
    esObject = {}
    esObject["objectKey"] = key
    esObject["bucket"] = bucket
    esObject["createdTimestamp"] = timestamp
    esObject["labels"] = []
    
    try:
        response = s3.head_object(Bucket=bucket, Key=key)
        print(response)
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
        
    rekognitionResponse = rekognition.detect_labels(Image={'S3Object':{'Bucket': bucket, 'Name': key}})    
    
    try:
        tempLabels = response["Metadata"]["customlabels"].replace(" ", "").lower()
        labels = tempLabels.split(",")
        
        pluralLabels = []
        for label in labels:
            esObject["labels"].append(label)
            esObject["labels"].append(p.plural(label))
            pluralLabels.append(p.plural(label))
        
        for lable in rekognitionResponse["Labels"]:
            if (lable.lower() not in labels):
                esObject["labels"].append(lable["Name"].replace(" ", "").lower())
            if (p.plural(lable.lower()) not in pluralLabels):
                esObject["labels"].append(p.plural(lable["Name"].replace(" ", "").lower()))
    except Exception as e:
        for lable in rekognitionResponse["Labels"]:
            esObject["labels"].append(lable["Name"].replace(" ", "").lower())
            esObject["labels"].append(p.plural(lable["Name"].replace(" ", "").lower()))
            
    print(esObject["labels"])
    
    url = endpoint + "/{}".format("photos") + "/_doc"
    data = json.dumps(esObject)
    result = json.loads(requests.post(url, auth = ('randygenere', 'zokbim-niBbik-danso0'),headers = headers, data = data).text)
