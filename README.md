# InstagramScrapy

# What For
scrapy post images and videos from a user

# Installation
1. Clone the project or Download zip
2. python3 required, python3-pip required
3. pip3 install -r requirements.txt

# How to use
1. Enter the folder with setting.py in 
2. Run `scrapy crawl instagram` in terminal
3. Input the instagram username or the url of user
> Example: 
> ### url
> https://www.instagram.com/heyimbee/ 
> ### username
> heyimbee
4. If goes well, images and videos will be sent to spider/storage/{username}


# Proxy
You can set proxy within setting.py
example:
```python
PROXIES = {
    "https":"127.0.0.1:8123",
    "http":"127.0.0.1:8123"
}
```
# FeedBack
* if you have any problem while using this script, please feel free to ask and raise a issue, I will check as soon as I can, thanks
