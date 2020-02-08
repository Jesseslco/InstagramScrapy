# -*- coding: utf-8 -*-
import scrapy
import requests
import random
from urllib.parse import urljoin, urlencode
from instagramScrapy.settings import PROXIES, USER_AGENTS
from pyquery import PyQuery as pq
import json
from instagramScrapy.items import InstagramscrapyItem
import re
import os
import shutil

class InstagramSpider(scrapy.Spider):

    name = 'instagram'

    def __init__(self):
        self.instagramUrl = "https://www.instagram.com"
        self.batchQuery = "https://www.instagram.com/graphql/query/?"
        self.headers = {
            "user-agent":random.choice(USER_AGENTS),
        }
        self.rollHash = None
        self.postHash = '870ea3e846839a3b6a8cd9cd7e42290c'
        self.passID = None
        self.BASE_PATH = os.path.abspath(os.path.dirname(__file__))
        self.STORAGE_PATH = os.path.join(self.BASE_PATH, 'storage')
        self.STORAGE_USER_path = None
        if os.path.exists(self.STORAGE_PATH):
            if os.path.isdir(self.STORAGE_PATH):
                # shutil.rmtree(self.STORAGE_PATH)
                self.logger.info("folder storage existed")
            else:
                os.mkdir(self.STORAGE_PATH)
        else:
            os.mkdir(self.STORAGE_PATH)

    def handle_user_input(self, userInput):
        html_elements = ["https", "www.instagram.com"]
        if any([x in userInput for x in html_elements]):
            return userInput
        else:
            return urljoin(self.instagramUrl, userInput)

    def urlValidation(self, url):

        # try:
        #     assert re.match('https://www.instagram.com/*', url) is not None
        #     if PROXIES:
        #         r = requests.get(url=url, proxies=PROXIES, headers=self.headers)
        #     else:
        #         r = requests.get(url=url, headers=self.headers)
        # except MissingSchema as e:
        #     self.logger.error("Invalid URL")
        #     return False
        # except Exception as e:
        #     return False
        # else:
        #     if r.status_code == 200:
        #         return True
        #     else:
        #         return False
        return True

    def start_requests(self):
        url = self.handle_user_input(input("URL OR USER: "))
        if self.urlValidation(url):
            yield scrapy.Request(url=url, callback=self.parse, headers=self.headers)
        else:
            self.logger.warn("Validation Failed")
            self.logger.warn("Quiting")

    def parse_nodes(self, nodes, is_index):
        # for node in nodes:
        #     if node['node']['is_video']:
        #         if node['node'].get('video_url', None):
        #             yield scrapy.Request(url=node['node']['video_url'], callback=self.parse_media, meta={'name':node['node']['id'] + '.mp4', 'delay':3})
        #         else:
        #             params = {
        #                 "query_hash": self.postHash,
        #                 "variables": json.dumps(
        #                         {
        #                             "shortcode": node['node']['shortcode'],
        #                             "child_comment_count": 3,
        #                             "fetch_comment_count": 40,
        #                             "parent_comment_count": 24,
        #                             "has_threaded_comments": True,
        #                         }),
        #             }
        #             postUrl = (self.batchQuery + urlencode(params)).replace("+", '')
        #             yield scrapy.Request(url=postUrl, callback=self.parse_video_node, meta={'delay':3})
        #     else:
        #         yield scrapy.Request(url=node['node']['display_url'], callback=self.parse_media, meta={'name':node['node']['id'] + '.jpg', 'delay':1})

        if is_index:
            #New Update
            for node in nodes:
                params = {
                    "query_hash": self.postHash,
                    "variables": json.dumps(
                            {
                                "shortcode": node['node']['shortcode'],
                                "child_comment_count": 3,
                                "fetch_comment_count": 40,
                                "parent_comment_count": 24,
                                "has_threaded_comments": True,
                            }),
                }
                postUrl = (self.batchQuery + urlencode(params)).replace("+", '')
                if node['node']['is_video']:
                    yield scrapy.Request(url=postUrl, callback=self.parse_node, meta={'name':node['node']['id'] + '.mp4', 'delay':5, 'is_video':True})
                else:
                    yield scrapy.Request(url=postUrl, callback=self.parse_node, meta={'name':node['node']['id'] + '.jpg', 'delay':2, 'is_video':False})
        else:
            for node in nodes:

                if node['node'].get('edge_sidecar_to_children', None) is not None:
                    for await_job in self.parse_son_node(node['node']['edge_sidecar_to_children']['edges']):
                        yield await_job
                if node['node']['is_video']:
                    if node['node'].get('video_url', None):
                        yield scrapy.Request(url=node['node']['video_url'], callback=self.parse_media, meta={'name':node['node']['id'] + '.mp4', 'delay':3})
                    else:
                        params = {
                            "query_hash": self.postHash,
                            "variables": json.dumps(
                                    {
                                        "shortcode": node['node']['shortcode'],
                                        "child_comment_count": 3,
                                        "fetch_comment_count": 40,
                                        "parent_comment_count": 24,
                                        "has_threaded_comments": True,
                                    }),
                        }
                        postUrl = (self.batchQuery + urlencode(params)).replace("+", '')
                        yield scrapy.Request(url=postUrl, callback=self.parse_video_node, meta={'delay':3})

                else:
                    yield scrapy.Request(url=node['node']['display_url'], callback=self.parse_media, meta={'name':node['node']['id'] + '.jpg', 'delay':1})

    def parse_son_node(self, nodes):
        for node in nodes:
            if node["node"]["is_video"]:
                yield scrapy.Request(url=node['node']['video_url'], callback=self.parse_media, meta={'name':node['node']['id'] + '.mp4', 'delay':5})
            else:
                yield scrapy.Request(url=node['node']['display_url'], callback=self.parse_media, meta={'name':node['node']['id'] + '.jpg', 'delay':2})

    def parse_node(self, response):
        data = json.loads(response.body)
        name = response.meta.get('name')
        if response.meta.get('is_video'):
            url = data["data"]["shortcode_media"]["video_url"]
        else:
            url = data["data"]["shortcode_media"]["display_url"]
        yield scrapy.Request(url=url, callback=self.parse_media, meta={'name': name})

        if data["data"]["shortcode_media"].get("edge_sidecar_to_children", None) is not None:
            for await_job in self.parse_son_node(data["data"]["shortcode_media"]["edge_sidecar_to_children"]["edges"]):
                yield await_job

    def parse(self, response):
        html = response.body.decode('utf-8')
        doc = pq(html)
        scripts = [pq(x).text() for x in doc("script")]
        links = [pq(x).attr('href') for x in doc('link')]
        def getFirstBatch(scripts):
            pattern = "window\._sharedData = ({.*?});"
            for node in scripts:
                result = re.match(pattern, node)
                if result:
                    return result.group(1)
            return False
        firstBatchOrNot = getFirstBatch(scripts)
        if firstBatchOrNot:
            firstBatchInfo = json.loads(firstBatchOrNot)
            userName = firstBatchInfo['entry_data']['ProfilePage'][0]['graphql']['user']['username']
            self.STORAGE_USER_path = os.path.join(self.STORAGE_PATH, userName)
            if os.path.exists(self.STORAGE_USER_path):
                if os.path.isdir(self.STORAGE_USER_path):
                    shutil.rmtree(self.STORAGE_USER_path)
            os.mkdir(self.STORAGE_USER_path)
            self.passID = firstBatchInfo['entry_data']['ProfilePage'][0]['graphql']['user']['id']

            # for node in firstBatchInfo["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"]:
            for await_job in self.parse_nodes(firstBatchInfo["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["edges"], True):
                yield await_job

            profileJS = None
            # consumerJS = None
            for link in links:
                if not profileJS:
                    if "ProfilePageContainer.js" in link:
                        profileJS = urljoin(self.instagramUrl, link)
                    # elif "Consumer.js" in link:
                    #     consumerJS = urljoin(self.instagramUrl, link)
                    #     yield scrapy.Request(url=consumerJS, callback=self.parseConsumerJS)

            hasNextOrNot = firstBatchInfo["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["page_info"]["has_next_page"]
            if profileJS and hasNextOrNot:
                yield scrapy.Request(url=profileJS, callback=self.parseProfileJS, meta={'endCursor':firstBatchInfo["entry_data"]["ProfilePage"][0]["graphql"]["user"]["edge_owner_to_timeline_media"]["page_info"]["end_cursor"]})
            else:
                self.logger.warn("MissingProfileJS Or Has No Next")
        else:
            self.logger.warn("Didn't get first batch")

    def parseProfileJS(self, response):
        rawJS = response.body.decode('utf-8')
        self.rollHash = re.findall("queryId:\"([0-9a-fA-F]*?)\"", rawJS)[2]
        endCursor = response.meta.get("endCursor")
        params = {
            "query_hash":self.rollHash,
            "variables":json.dumps({
                "id": self.passID,
                "first": 12,
                "after": endCursor,
            })
        }
        nextBatchUrl = (self.batchQuery + urlencode(params)).replace("+", "")
        if self.rollHash:
            yield scrapy.Request(url=nextBatchUrl, callback=self.parse_batch)

    def parse_batch(self, response):
        data = json.loads(response.body)
        nodes = data["data"]["user"]['edge_owner_to_timeline_media']['edges']

        for await_job in self.parse_nodes(nodes, False):
            yield await_job

        ## Next_Batch
        if data["data"]["user"]['edge_owner_to_timeline_media']['page_info']['has_next_page']:
            endCursor = data["data"]["user"]['edge_owner_to_timeline_media']['page_info']['end_cursor']
            params = {
                "query_hash":self.rollHash,
                "variables":json.dumps({
                    "id": self.passID,
                    "first": 12,
                    "after": endCursor,
                })
            }
            nextBatchUrl = (self.batchQuery + urlencode(params)).replace("+", "")
            yield scrapy.Request(url=nextBatchUrl, callback=self.parse_batch, meta={'delay':3})
        else:
            self.logger.info("Scrapy all imgs done")

    def parse_video_node(self, response):
        data = json.loads(response.body)
        name = data["data"]["shortcode_media"]["id"] + '.mp4'
        video_url = data["data"]["shortcode_media"]["video_url"]
        yield scrapy.Request(url=video_url, callback=self.parse_media, meta={'name': name})

    ## Parse_imgs_or_videos
    def parse_media(self, response):
        item = InstagramscrapyItem()
        item["name"] = os.path.join(self.STORAGE_USER_path, response.meta.get('name'))
        item["content"] = response.body
        yield item




