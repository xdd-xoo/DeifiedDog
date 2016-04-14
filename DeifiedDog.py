#-*- coding:gbk -*-
from __future__ import division  
import urllib 
import re
import os 
import time
import xlwt
from xlwt import *
import sys
import threading
import random
from string import atoi
reload(sys)
sys.setdefaultencoding('utf-8')

global result_app_info
global local_storage 
global app_context
#global page_deepth
app_context = list()
mutex = threading.Lock()  

regex_info = re.compile(r'<span class="list_title font14_2"><.*>(.*)</a>\s*</span>$')
regex_version = re.compile(r'<span class="list_version font12">(.*)</span>$')
regex_down = re.compile(r'<a href="/appdown/(.*)" rel="nofollow">$')
filter_root = r"?sort=5&dmin=200&pi=%d"
app_root_url = r"http://apk.hiapk.com/apps/"
game_root_url = r"http://apk.hiapk.com/games/"
web_download_root = r"http://apk.hiapk.com/appdown/"

def update_app_category(app_root_url):
    content = urllib.urlopen(app_root_url).readlines()
    regex = re.compile(r'class="category_item"><a href="/.*/(.*)"> <s')
    app_category = []
    for line in content:
        res = re.findall(regex,line)
        if res:
            app_category.append(app_root_url+res[0]+filter_root)
    return app_category
    		
def update_game_category(game_root_url):
    content = urllib.urlopen(game_root_url).readlines()
    regex = re.compile(r'class="category_item"><a href="/.*/(.*)"> <s')
    game_category = []
    for line in content:
        res = re.findall(regex,line)
        if res:
            game_category.append(game_root_url+res[0]+filter_root)
    return game_category


def get_each_category_app_info(category,page_deepth):
    global app_context
    #global page_deepth
    info_label = None
    version_label = None
    down_label = None
    print category
    for i in range(1,page_deepth+1):
        category_filter = category%i
        print category_filter 
        web_line = urllib.urlopen(category_filter).readlines()
        for line in web_line:
            line = line.rstrip()
            if re.findall(regex_info,line):
                info_label = True
                res1 = re.findall(regex_info,line)
                #print res1[0]
                continue
            if re.findall(regex_version,line):
                version_label = True
                res2 = re.findall(regex_version,line)
                #print res2[0]
                continue
            if re.findall(regex_down,line.strip()):
                down_label = True
                res3 = re.findall(regex_down,line)
                #print res3[0]

            if info_label and version_label and down_label :
                if mutex.acquire():  
                    app_context.append((category.split('?')[0].split('/')[-1],res1[0],res2[0],res3[0]))
                    mutex.release()
                info_label = None
                version_label = None
                down_label = None
    #if len(app_context):     
    #    return app_context


def generate_app_context():
    global app_context
    #app_context_list = []
    threads = []
    for category in update_app_category(app_root_url):
        t = threading.Thread(target=get_each_category_app_info,args=(category,page_deepth))
        threads.append(t)
        t.start()

    for category in update_app_category(game_root_url):
        t = threading.Thread(target=get_each_category_app_info,args=(category,page_deepth))
        threads.append(t)
        t.start()

    for thread in threads:
        thread.join()
    return app_context

def UpdateDataToExcel():
    time_stamp = time.strftime("%Y-%m-%d-%H%M%S", time.localtime())
    date_for_report = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    ReportFile = 'report\SpiderReport_'+time_stamp+'.xls'

    # Define Fond & Style for excel subject slot for Spider report
    font_subject_jira = Font()
    font_subject_jira.name = 'Arial'
    font_subject_jira.bold = True
    font_subject_jira.colour_index = 1
    font_subject_jira.outline = True
    pattern_subject_jira = xlwt.Pattern()
    pattern_subject_jira.pattern = xlwt.Pattern.SOLID_PATTERN
    pattern_subject_jira.pattern_fore_colour = 18
    alignment_subject_jira = xlwt.Alignment()
    alignment_subject_jira.horz = xlwt.Alignment.HORZ_CENTER
    alignment_subject_jira.vert = xlwt.Alignment.VERT_CENTER
    borders_subject_jira = Borders()
    borders_subject_jira.left = 1
    borders_subject_jira.right = 1
    borders_subject_jira.top = 1
    borders_subject_jira.bottom = 1
    style_subject = XFStyle()
    style_subject.font = font_subject_jira
    style_subject.pattern = pattern_subject_jira
    style_subject.alignment = alignment_subject_jira
    style_subject.borders = borders_subject_jira
    # Define Fond & Style for excel data slot
    font_data = Font()
    font_data.name = 'Arial'
    borders_data = Borders()
    borders_data.left = 1
    borders_data.right = 1
    borders_data.top = 1
    borders_data.bottom = 1
    style_data = XFStyle()
    style_data.font = font_data
    style_data.borders = borders_data
    file_handle = xlwt.Workbook(encoding = 'utf-8')
    # Generate sheet JIRA for JIRA issue list with CR mapping
    sheet_handle_report = file_handle.add_sheet('report')
    # Update subject
    sheet_handle_report.write(0, 0, 'Category', style_subject)
    sheet_handle_report.col(0).width = 5000
    sheet_handle_report.write(0, 1, 'APP', style_subject)
    sheet_handle_report.col(1).width = 5000
    sheet_handle_report.write(0, 2, 'Version', style_subject)
    sheet_handle_report.col(2).width = 5000
    sheet_handle_report.write(0, 3, 'Date', style_subject)
    sheet_handle_report.col(3).width = 5000
    sheet_handle_report.write(0, 4, 'Path', style_subject)
    sheet_handle_report.col(4).width = 5000

    row = 1
    for app_info in result_app_info:
        app_category = app_info[0] or "N/A"
        app_name = app_info[1] or "N/A"
        app_version = app_info[2][1:-1] or "N/A"
        date = date_for_report
        path = os.path.join(local_storage,app_info[3]+".apk")
        sheet_handle_report.write(row, 0, app_category, style_data)
        sheet_handle_report.write(row, 1, app_name, style_data)
        sheet_handle_report.write(row, 2, app_version, style_data)
        sheet_handle_report.write(row, 3, date, style_data)
        sheet_handle_report.write(row, 4, path, style_data)
        row = row + 1        
    file_handle.save(ReportFile)

def cbk(a, b, c):
    per = 100.0 * a * b / c
    if per < 100:
        print ('\r%.2f%%' % per),
    else:
        print "\rcompleted!"

def main():
    global result_app_info
    global app_context
    global local_storage
    global apk_number
    global result_app_info
    global page_deepth
    result_app_info = list()
    if len(sys.argv[1:])>1:
        local_storage = sys.argv[1]
        apk_number = atoi(sys.argv[2])
    else:
        local_storage = "C:\Dropbox\APKs"
        apk_number = 3000

    if not os.path.exists(local_storage):
        os.mkdir(local_storage)
    page_deepth = apk_number/290
    if page_deepth <= 1:
        page_deepth = 1
    if page_deepth > 1:
        page_deepth = int(page_deepth)+1

    result_app_info = generate_app_context()
    #while len(result_app_info)<apk_number:
    #    random_choice = random.choice(result_info)
    #    if random_choice not in result_app_info:
    #        result_app_info.append(random_choice)

    UpdateDataToExcel()
    
    item = 1
    for app in result_app_info:
        if len(app) == 4 and app[3]:
            app_url = web_download_root+app[3]
            local_url  = local_storage+"\\"+app[3]+".apk"
            try :
                print "Start to download the %d : %s ,save the app at %s"%(item,app[3],local_url)
                urllib.urlretrieve(app_url,local_url,cbk)
            except :
                print "download the app %s failed , remove the imcompletely file "%app[3]
                os.system("del %s"%local_url)
            item +=1
    
if __name__ == "__main__":
    main()
