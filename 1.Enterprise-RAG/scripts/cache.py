from abc import ABC, abstractmethod
from typing import Optional
import time
import hashlib
import redis
import logging
from enum import Enum
import json
from typing import Any

logger = logging.getLogger(__name__)

########## Class definition BEGIN ##########

class CacheType(Enum):
    DISABLED = "0"
    REDIS = "1"
    LOCAL = "2"
    

#cache abstract class
#makes it easier to move to redis later
class Cache(ABC):

    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

    @abstractmethod
    def set(self, key: str, value: Any, ex: int | None = None):
        pass

    ## helper functions ##

    ## normalize the input query ##
    def normalize_query(self, query: str) -> str:
        #remove extra spaces and convert to lowercase     
        return " ".join(query.lower().strip().split())
    ## end ## 

    ## generate key ##
    def generate_cache_key(self, query: str, kb_version: str):
        normalized = self.normalize_query(query)

        return hashlib.sha256(
            f"{normalized}:{kb_version}".encode()
        ).hexdigest()
    ## end ##

    ## query cache ##
    def query_cache(self, query: str):

        ## generate the query key ##
        key = self.generate_cache_key(query=query, kb_version="v1")

        logger.info("calling redis")
        cached_response = self.get(key)
        logger.info("redis call done")

        if cached_response is not None:
            data = json.loads(cached_response)
            logger.info("CACHE HIT")
        else:
            data = cached_response
            logger.info("CACHE MISS")

        return data
    ## end ##

    ## update cache ##
    def update_cache(
            self, 
            query: str,
            response: dict
        ):

        ## generate the query key ##
        key = self.generate_cache_key(query=query, kb_version="v1")
    
        logger.info("Cache missed, loading response in cache...")
        self.set(
            key=key,
            value=response,
            ex=86400  # 1 day
        )
## end ##        

## redis cache
class RedisCache(Cache):

    def __init__(self, host, port = 6379):
        self.client = redis.Redis(
            host=host,
            port=port,
            ssl=True,
            decode_responses=True
    )

    ## get the item from cache ##
    def get(self, key: str):
        logger.info("trying to get key from redis")
        return self.client.get(key)
    ## end ##

    ## put item into cache ##
    def set(self, key: str, value: Any, ex: int | None = 86400):
        self.client.set(key, json.dumps(value), ex=ex)
    ## end ##

## end ##        


## local cache to test before moving to redis
class LocalCache(Cache):

    def __init__(self):
        self._store = {}

    ## get the item from cache ##
    def get(self, key: str):
        item = self._store.get(key)

        if item is None:
            return None

        #item is a tuple, with two items, value = item[0], expiry = item[1]
        # below line unpacks both fields of tuple in one line
        # upack items 
        value, expiry = item

        #check if key is expired
        if expiry and expiry < time.time():
            #if expired then delete expired item
            del self._store[key]
            return None

        return value
    ## end ##

    ## put item into cache ##
    def set(self, key: str, value: str, ex: int | None = 86400):
        
        #set expiry time
        expiry = time.time() + ex if ex else None

        #store the item
        self._store[key] = (value, expiry)
    ## end ##

## end ##
        
########## Class definition END ##########        
