import random, string
import json
import boto3
import base64
from elasticsearch import Elasticsearch

lexBot = boto3.client("lex-runtime")
s3Resource = boto3.resource('s3')
s3Client = boto3.client('s3')
bucket = s3Resource.Bucket('storagebucket17')

def lambda_handler(event, context):
    query = event["q"]
    
    newUser = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
    emptyArray = []
    
    es = Elasticsearch(
        hosts = "https://search-photos-rcgm42jp6ggwagmaclqlhvx77a.us-east-1.es.amazonaws.com",
        http_auth = ("randygenere", "zokbim-niBbik-danso0")
    )
        
    try:
        response = lexBot.post_text(
            botName='SearchPhotos',
            botAlias='$LATEST',
            userId=newUser,
            inputText=query,
        )
    except Exception as e:
        print(e)
        return {
            'statusCode': 200,
            'body': json.dumps(emptyArray)
        }
    
    keyword1 = response["slots"]["keywordOne"]
    keyword2 = response["slots"]["keywordTwo"]
    
    if keyword1 == None and keyword2 == None:
        return {
            'statusCode': 200,
            'body': json.dumps(emptyArray)
        }
    elif keyword1 != None and keyword2 == None:
        esResponse = es.search(index = "photos", body = {
            "query": {
                "match": {
                    "labels": {
                        "query": keyword1
                    }
                }
            }
        })
    elif keyword1 == None and keyword2 != None:
        esResponse = es.search(index = "photos", body = {
            "query": {
                "match": {
                    "labels": {
                        "query": keyword2
                    }
                }
            }
        })
    else:
        esResponse = es.search(index = "photos", body = {
            "query": {
                "match": {
                    "labels": {
                        "query": "{} {}".format(keyword1, keyword2)
                    }
                }
            }
        })
      
    if (len(esResponse) == 0):
        return {
            'statusCode': 200,
            'body': json.dumps(emptyArray)
        }
    else:
        photos = []
        for photo in esResponse["hits"]["hits"]:
            url = s3Client.generate_presigned_url('get_object', Params={'Bucket': "storagebucket17",'Key': photo["_source"]["objectKey"]}, ExpiresIn=3600)
            photos.append(url)
    
    return {
        'statusCode': 200,
        'body': json.dumps(photos)
    }