# -*- coding: utf-8 -*-
#  [Program]
#
#  Common Folder Tidy
#
#
#  [Author]
#
#  ZWY
#  zwycn [at] icloud [dot] com
#
#
#  [License]
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#  See 'docs/LICENSE' for more information.

import sys
import os
import re
import time
import ConfigParser
import shutil
import glob
import codecs

reload(sys)
sys.setdefaultencoding('gbk')

class CommonFolderTidy:

    def __init__(self):
        

        self.version = '1.0'

        self.isWin = False
        if sys.platform.startswith('win'):
            self.isWin = True

        # reading configuration file...
        config = ConfigParser.ConfigParser()
        if not self.isWin:
            config.read("cft.cfg")
        else:
            config.readfp(codecs.open("cft.cfg", "r", "utf-8-sig"))

        self.sections = config.sections()
        self.sections.sort()

        self.dictNode = {}
        self.nodeList = []
        # get per node and values then setting in a Dictionary
        for section in self.sections:

            items = config.items(section)[0][1].split(',')
            self.dictNode.setdefault(section, items)

            # only get effective values, See cft.cfg
            specialSections = ['Ignore', 'Folders', 'Unrecognized']
            if section not in specialSections:
                [self.nodeList.append(x) for x in items]
        

    def menuOfProgram(self, param):

        param = param.lower()
        if param == '-h':
            print 'Please provider a absolute folder path you want to tidy.'
            print 'e.g:'
            print 'On Windows:  D:\\Downloads'
            print 'On *nix or Mac:  ~/Downloads'
            print 'For more help take a look in docs/README.'
            print 'Configuration files in cft.cfg.\n'
            print "-v to watch the current version of CFT."
            print "-f [path] [fileName] to find absolute path of a file\n"
            sys.exit()
        elif param == '-v':
            print 'Common Folder Tidy version: %s\n' % (self.version)
            sys.exit()
        elif param == '-f':
            if len(sys.argv) > 3:
                if not self.isWin:
                    if sys.platform == 'darwin' or sys.platform.startswith('linux'):
                        objPos = os.popen('find ' + sys.argv[2]  + ' -name '+sys.argv[3])
                        for x in objPos: print x,
                        sys.exit()
                    else:
                        print 'Sry, What Operating System are you use?'
                        print 'Please give a mail-feedback to help cft going to better, Thanks!'
                        sys.exit()
                else:
                    command = 'dir ' + sys.argv[2] + ' /s /b | find "' + sys.argv[3] + '"'
                    objPos = os.popen(command)
                    for x in objPos: print x,
                    sys.exit()
            print 'Find: -f [path] [file]\nFor Example: python cft.py -f . png\n'
            sys.exit()
        else:
            print "Unknow arguments, use '-h' for menu help."
            sys.exit()


    def validateConfig(self):

        self.nodeList.sort()
        flag = False 

        for i,item in enumerate(self.nodeList):
            count = self.nodeList.count(item)
            if count > 1:
                flag = True
                print 'Warning: Found duplicate suffix - ',item
                self.nodeList.remove(item) 

        if flag:
            print '\nYou can go back \'cft.cfg\' and make modifications,',
            answer = raw_input('Are you wanna continue anyway? (y/n) ')
            if answer != 'y':
                sys.exit()


    def validateParam(self, param):

        param = param.strip()

        # menu help
        if param.startswith('-'):
            self.menuOfProgram(param)

        if self.isWin:
            if param.lower().startswith('c'):
                # volume C may not be the windows system disk...
                answer = raw_input("Warning: Volume C is very IMPORTANT for Windows! Please make sure it is NOT you system disk, Do you really wanna continue? (n/Yes) ")
                if answer != 'Yes': 
                    print '\nYou just make a good choice:) \nThank you for using!'
                    sys.exit()
            if param.endswith('\\'):
                param = param.rstrip('\\')

        else:
            param = param.rstrip('/')
            if len(param) == 0 or param == '/' or param == '~' or \
               param.lower() == os.path.join('/users', os.getlogin()):
                    print 'You should not to tidy your root directory, it\'s very IMPORTANT for your computer!'
                    sys.exit()

        # ensure the path exists and it's a directory
        if not os.path.exists(param) or not os.path.isdir(param):
            print 'Please check the path you provider is exists'
            print "Or make sure it\'s a Folder Path."
            print "However, the system root path '/' or 'c:\' should not be input."
            sys.exit()
        print 'Start tidy > ',param
        self.startClearUp(param)


    def prepareEnvironment(self, path):

        if self.isWin:
            up_level_name = path.split('\\')[len(path.split('\\'))-1].replace(':','')
            root_name = path + os.sep + up_level_name.upper() + ' Tidy From ' + time.ctime().replace(':','_')
        else:
            up_level_name = path.split('/')[len(path.split('/'))-1]
            root_name = path + os.sep + up_level_name.upper() + ' Tidy From ' + time.ctime()

        try:
            # create root Directory
            if not os.path.exists(root_name):
                os.makedirs(root_name)

            # create subfolders
            for sub in self.dictNode.keys():
                if sub != 'Ignore':
                    sub_name = root_name + os.sep + sub
                    if not os.path.exists(sub_name):
                        os.makedirs(sub_name)
        except Exception, ex:
            print 'Create tidy folders failed...\n', ex

        return root_name


    def ignoreUserDefineList(self, path):

        ignoreList = []

        for user_define_ignore in self.dictNode['Ignore']:
            for x in glob.iglob(os.path.join(path, user_define_ignore)):

                if self.isWin:
                    x =x[x.rindex('\\')+1:]
                else:
                    x = x[x.rindex('/')+1:]

                # append each object to ignore list
                ignoreList.append(x)

        # fuzzy match may got the same file
        return self.uniqueParams(ignoreList)


    def startClearUp(self, absolutePath):

        # Check the config file
        self.validateConfig()

        if self.isWin:
            targets = [item.decode('gbk') for item in os.listdir(absolutePath)]
        else: 
            targets = os.listdir(absolutePath)
        newPos = self.prepareEnvironment(absolutePath)

        if len(targets) > 0:
            # ignore hidden files with silence
            targets = [x for x in targets if not x.startswith('.')]
            # user-defined ignore list - See cft.cfg, user-defined config
            ignoreList = self.ignoreUserDefineList(absolutePath)

            try:
                for f in targets:
                    if f in ignoreList:
                        print 'Ignore object...',f
                        continue

                    if os.path.isdir(os.path.join(absolutePath,f)):
                        self.handingDirs(f, absolutePath, newPos)
                    else:
                        self.handingFiles(f, absolutePath, newPos)
            except Exception, e:
                print 'Failed clear up at %s\n %s' % (f,e)

        print '\nDone!'


    def handingDirs(self, dirName, path, newPos):
        self.coperating(dirName, path, os.path.join(newPos,'Folders'))


    def handingFiles(self, fileName, path, newPos):

        # get each file suffix
        if fileName.rfind('.') != -1:
            fileType = fileName[fileName.rindex('.')+1:len(fileName)]
        else:
            # no suffix files, all of unrecognizable files will move to [Unrecognized]
            fileType = 'Unknow'

        if fileType.lower() in self.dictNode.get('Applications'):
            self.coperating(fileName, path, os.path.join(newPos,'Applications'))
        elif fileType.lower() in self.dictNode.get('Archives'):
            self.coperating(fileName, path, os.path.join(newPos,'Archives'))
        elif fileType.lower() in self.dictNode.get('Documents'):
            self.coperating(fileName, path, os.path.join(newPos,'Documents'))
        elif fileType.lower() in self.dictNode.get('Movies'):
            self.coperating(fileName, path, os.path.join(newPos,'Movies'))
        elif fileType.lower() in self.dictNode.get('PDFs'):
            self.coperating(fileName, path, os.path.join(newPos,'PDFs'))
        elif fileType.lower() in self.dictNode.get('Pictures'):
            self.coperating(fileName, path, os.path.join(newPos,'Pictures'))
        elif fileType.lower() in self.dictNode.get('Resources'):
            self.coperating(fileName, path, os.path.join(newPos,'Resources'))
        elif fileType.lower() in self.dictNode.get('Source Code'):
            self.coperating(fileName, path, os.path.join(newPos,'Source Code'))
        elif fileType.lower() in self.dictNode.get('Text'):
            self.coperating(fileName, path, os.path.join(newPos,'Text'))
        else:
            self.coperating(fileName, path, os.path.join(newPos,'Unrecognized'))


    def coperating(self, obj, srcPath, dst):

        try:
            src = os.path.join(srcPath, obj)
            if os.path.exists(dst) and os.path.isdir(dst):
                shutil.move(src, dst)
        except Exception, ex:
            ex_namesake = 'already exists'
            if ex_namesake in str(ex).lower():

                for i in xrange(10000):
                    expect_dst = os.path.join(dst, obj) + ' ' + str(i)
                    if os.path.exists(expect_dst):
                        continue
                    else:
                        try:
                            if os.path.exists(dst) and os.path.isdir(dst):
                                shutil.move(src, expect_dst)
                        except Exception, iex:
                            print 'Oops, something was wrong at \'%s\' Raise by %s' % (obj, str(iex))
                        finally:
                            break
        else:
            pass


    def uniqueParams(self, s):
        try:
            return list(set(s))
        except:
            pass
        try:
            t =  s[:]
            t.sort()
        except:
            print 'Processing error when uniqueParams at', s
            raise
        else:
            return [x for i,x in enumerate(t) if not i or x != t[i-1]]




if __name__ == "__main__":
    if len(sys.argv) < 2:
        print 'no arguments.'
        sys.exit()
    path = sys.argv[1]
    print 'Your enter is: %s' % (path)
    cft = CommonFolderTidy()
    cft.validateParam(path)
