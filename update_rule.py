#coding:utf-8
#!/usr/bin/python

 
from xml.etree.ElementTree import ElementTree,Element
import urllib2
import sys
import json
from copy import deepcopy
import os
import time

def read_xml(in_path):
    '''读取并解析xml文件
         in_path: xml路径
         return: ElementTree'''
    tree = ElementTree()
    tree.parse(in_path)
    return tree
 
def write_xml(tree, out_path):
    '''将xml文件写出
         tree: xml树
         out_path: 写出路径'''
    tree.write(out_path, encoding="utf-8",xml_declaration=True)
 
#---------------search -----
def find_nodes(tree, path):
    '''查找某个路径匹配的所有节点
         tree: xml树
         path: 节点路径'''
    return tree.findall(path)
 
 
def create_node(tag, property_map, content):
    '''新造一个节点
         tag:节点标签
         property_map:属性及属性值map
         content: 节点闭合标签里的文本内容
         return 新节点'''
    element = Element(tag, property_map)
    element.text = content
    return element


def read_local_version(version):
    file = open(version, 'r')
    version = file.read()
    file.close()
    return version.strip(' \n\r\n\t') 

def get_server_version(url):
    #url = 'http://get_version'
    resp = urllib2.urlopen(url)
    if resp.code == 200:
        return resp.read().strip(' \n\r\n\t')
    return False

def get_json_data(url):
    #url = 'http:get_rules'
    resp = urllib2.urlopen(url)
    #print resp.code
    if resp.code != 200:
        return False
    try:
        datas =  json.load(resp)
        roles = transfer_role(datas['roles'])
        return datas['version'],datas['rules'],roles
    except Exception, e:
        print e
        #sys.exit()
    #roles = transfer_role(datas['roles'])
    #return datas['version'], datas['rules'], roles

def transfer_role(roles):
    tran_roles = {}
    for role in roles:
        for role_name, users in role.items():
            tran_roles[deepcopy(role_name)] = deepcopy(users)
    return tran_roles
    
def build_rule(datas, roles):
    rules = []
    for data in datas:
        for user in roles[data['role']]:
            if data['insert'] in ('1',1):
                rule = 'insert.*' + data['table'] + '.*' + 'web-user=' + user
                rules.append(deepcopy(rule))
            if data['update'] in ('1',1):
                rule = 'update.*' + data['table'] + '.*' + 'web-user=' + user
                rules.append(deepcopy(rule))
            if data['delete'] in ('1',1):
                rule = 'delete.*' + data['table'] + '.*' + 'web-user=' + user
                rules.append(deepcopy(rule))
            if data['select'] in ('1',1):
                rule = 'select.*' + data['table'] + '.*' + 'web-user=' + user
                rules.append(deepcopy(rule))
    return rules

def update_config_xml(config_file, rules): 
    #1. 读取xml文件
    tree = read_xml(config_file)
     #A. 找到父节点
    filters = find_nodes(tree, "instance/filters")
    filters = filters[0]
    #清空子节点
    filters.clear()
    
    for rule in rules:
        #新建节点
        new_rule = create_node("filter", {"module":"regex","pattern":rule}, '')
        #插入到父节点之下
        filters.append(deepcopy(new_rule))
    write_xml(tree, config_file)
    
def update_version(version, new_version):
    file = open(version, 'w')
    file.write(new_version)
    file.close()
        
def restart_server():
    command = '/usr/local/sqlrelay/bin/sqlr-stop -id test'
    print command 
    print 'stop命令输出为：', os.popen(command)
    command = '/usr/local/sqlrelay/bin/sqlr-start -id test'
    print command
    print 'start命令输出为： ', os.popen(command)

def main():        
    #判断版本是否有更新
    local_version = read_local_version('version')
    #server_version = get_server_version('http://localhost:81/version.txt')
    #if local_version == server_version:
    #    sys.exit()
    application="财务系统"
    #获取规则
    print '获取json'
    new_version, datas, roles = get_json_data('http://10.206.9.177:8080/z2sas/getSqlrRules?version=' + local_version+'&application='+application)
    print '生成规则'
    rules = build_rule(datas,roles)
    try:
        if new_version > local_version:
            #update_config_xml
            print 'new version:'+new_version
            print 'local version:'+local_version
            print '更新xml'
            update_config_xml('./etc/sqlrelay.conf', rules)
            print '更新本地版本'
            update_version('version', new_version)  
            print '重启sqlrelay'
            restart_server()
        else:
            print '规则已是最新版本'
    except Exception,e:
        print e


if __name__ == "__main__":
    while True:
        main()
        time.sleep(10)

    
    


         
