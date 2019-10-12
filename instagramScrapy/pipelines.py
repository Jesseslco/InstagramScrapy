# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://docs.scrapy.org/en/latest/topics/item-pipeline.html

import os

class InstagramscrapyPipeline(object):
    def process_item(self, item, spider):
        with open(item['name'], "wb") as f:
            f.write(item['content'])
        return f"Saved-{item['name']}"
