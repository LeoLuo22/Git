# -*- coding:utf-8 -*-
__author__ = "Luo Hao"

import requests
import urllib
import http.cookiejar
from PIL import Image
from bs4 import BeautifulSoup
import lxml
import pytesseract
import re
import collections
import time


captcha_url = "http://wiscom.chd.edu.cn:8080/reader/captcha.php"
redr_verify = "http://wiscom.chd.edu.cn:8080/reader/redr_verify.php" #POST
redr_infp = "http://wiscom.chd.edu.cn:8080/reader/redr_info.php"#GET
book_lst = "http://wiscom.chd.edu.cn:8080/reader/book_lst.php"#GET
continue_borrow_url = "http://wiscom.chd.edu.cn:8080/reader/ajax_renew.php?" #GET
HEADERS = {'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/51.0.2704.103 Safari/537.36',
                        'Accept':'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                        'Accept-Encoding':'gzip, deflate, sdch',
                        'Accept-Language':'zh-CN,zh;q=0.8',
                        'Cache-Control':'no-cache',
                        'Connection':'keep-alive',
                        'Host':'wiscom.chd.edu.cn:8080',
                        'Pragma':'no-cache',
                        'Referer':'http://portal.chd.edu.cn/',
                        'Upgrade-Insecure-Requests':'1'}

class InputError(Exception):pass

class Chdlib:
    def __init__(self, username=None, password=None, captcha=None, name=None, borrowed_books=None, book_info_dict=None):
        self.__username = username
        self.__password = password
        self.__captcha = captcha
        self.__post_data = {'number':str(self.__username),
                                           'passwd':str(self.__password),
                                           'captcha':str(self.__captcha),
                                           'select':'cert_no'
        }
        self.__name = name
        self.__borrowed_books = borrowed_books
        self.__book_info_dict = book_info_dict#A dict saves the bar_code and check code of a book which are be used to post data in the "续借" url

    @property
    def book_info_dict(self):
        return self.__book_info_dict

    @property
    def borrowed_books(self):
        return self.__borrowed_books

    @property
    def username(self):
        return self.__username

    @username.setter
    def username(self, value):
        self.__username = value

    @property
    def password(self):
        return self.__password

    @password.setter
    def password(self, value):
        self.__password = value

    @property
    def captcha(self):
        return self.__captcha

    @captcha.setter
    def captcha(self, value):
        self.__captcha = value

    @property
    def name(self):
        return self.__name

    def get_captcha(self):
        cj = http.cookiejar.LWPCookieJar()
        opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
        urllib.request.install_opener(opener)
        req = urllib.request.Request("http://wiscom.chd.edu.cn:8080/reader/captcha.php")
        try:
            operate = opener.open(req)
            msg = operate.read()
        except (TimeoutError, urllib.error.URLError) as err:
            print(err)
        file_object = open('captcha.gif','wb')
        try:
            file_object.write(msg)
        finally:
            file_object.close()
        im = Image.open('captcha.gif')
        code = pytesseract.image_to_string(Image.open('captcha.gif'))
        return code


    def login(self):
        postdata = urllib.parse.urlencode(self.__post_data)
        postdata = postdata.encode('utf-8')
        res = urllib.request.urlopen(redr_verify,postdata)
        if(res.status == 200):
            print("登陆成功")
        return res.read()

    def book_lst(self):
        book_lst_page = urllib.request.urlopen(book_lst)
        return book_lst_page.read()

    def continue_borrow(self, seq_num=None):
        _time = int(time.time())


    def parse(self):
        """*************************获取用户名*******************************"""
        response = self.login()
        soup = BeautifulSoup(response, 'lxml')
        soup =soup.find('div',attrs={'id':'mylib_info'}).find('span', attrs={'class':'bluetext'}).find_parent()
        name = soup
        soup.span.decompose()
        self.__name = name.string
        """*************************获取当前借阅图书****************************"""
        book_page_responese  = self.book_lst()
        book_page_soup = BeautifulSoup(book_page_responese, 'lxml')
        books = book_page_soup.find_all('td',attrs={'class':'whitetext', 'width':'35%'})
        return_date = book_page_soup.find_all('td', attrs={'class':'whitetext', 'width':'13%'})
        self.__borrowed_books = collections.OrderedDict()
        tag_lst = []
        date_lst = []
        return_date_lst = []
        for tag in books:
            tag = tag.get_text()
            tag_lst.append(tag)
        for date in return_date:
            date = date.get_text()
            date_lst.append(date)
        for i in range(1,len(date_lst), 3):
            return_date_lst.append(date_lst[i])
        for i in range(0,len(tag_lst)):
            self.__borrowed_books[tag_lst[i]] = return_date_lst[i]
        """*************************获取已借阅书籍的bar_code和check**************************"""
        """*******************************并对应的存在list里***************************************"""
        bar_code = []
        check = []
        test = []
        book_info_tmp = []
        book_info = []
        bar_code_soup = book_page_soup.find_all('input',attrs={'title':'renew'})
        for item in bar_code_soup:
            test.append(item['onclick'])#re
        bar_code_re = "\\d{7}"
        r = re.compile(bar_code_re)
        for t in test:
            bar_code.append(re.search(r, t).group())
        check_re = "(\\d|A|B|C|D|E|F){8}"
        c_r = re.compile(check_re)
        for t in test:
            check.append(re.search(c_r, t).group())
        for i in range(0,len(check)):
            book_info_tmp.append(bar_code[i])
            book_info_tmp.append(check[i])
            book_info.append(book_info_tmp)
            book_info_tmp =[]
        print(book_info)
        self.__book_info_dict = collections.OrderedDict()
        for i in range(0,len(book_info)):
            self.__book_info_dict[tag_lst[i]] = book_info[i]
        print(self.__book_info_dict[0])



def get_input(msg,  _type, username=None):
    if _type == 'username':
        while  True:
            username = input(msg)
            if len(username) != 12 or  not username.isdigit():
                print("输入有误， 请重新输入")
                continue
            break
        return username

    elif _type == "password":
        password = input(msg)
        if len(password) == 0:
            password = username
            return password
        else:
            return password

def main():
    user = Chdlib()
    username = get_input("输入你的学号: ", 'username')
    password = get_input("请输入密码，默认为学号（按回车键）: ", 'password', username)
    captcha = user.get_captcha()
    user = Chdlib(username, password, captcha)
    user.login()
    user.parse()
    print("欢迎，{0}".format(user.name))
    print("你当前所借阅的图书共{0}本".format(len(user.borrowed_books)))
    for key, value in user.borrowed_books.items():
        print("{0}             归还日期: {1}".format(key, value))

main()



