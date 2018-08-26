# -*- coding:utf-8 -*-
import os
import re
import sys
import subprocess


'''
        apkInfo.name = this.regexpOne(stdout, /application-label-zh-CN:'([^']+)'/g) ||
        this.regexpOne(stdout, /application-label-zh:'([^']+)'/g) ||
        this.regexpOne(stdout, /label='([^']+)'/g)
          
        apkInfo.package = this.regexpOne(stdout, /package: name='([^']+)'/g)
        apkInfo.versionName = this.regexpOne(stdout, /versionName='([^']+)'/g)
        apkInfo.versionCode = this.regexpOne(stdout, /versionCode='([^']+)'/g)
        let minSdk = this.regexpOne(stdout, /sdkVersion:'([^']+)'/g)
        apkInfo.minSdk = `API${minSdk} ${VersionMap[minSdk] || ''}`
'''

def getAppBaseInfo(apkpath):
    # 检查版本号等信息
    PERMISSION_DELETE_PACKAGES = "android.permission.DELETE_PACKAGES"
    PERMISSION_INSTALL_PACKAGES = "android.permission.INSTALL_PACKAGES"
    cmd = "aapt.exe d badging {}".format(apkpath)
    #output = os.popen("aapt.exe d badging %s" % apkpath).read()
    output = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE).stdout.read().decode('utf-8')
    print (output)

    lable = re.findall("application-label-zh-CN:'([^']+)'", output, re.I | re.M)[0]
    if lable is None:
        lable = re.findall("application-label:'([^']+)'", output, re.I | re.M)[0]

    apkName = lable
    packagename = re.findall("package: name='([^']+)'",output ,re.I | re.M)[0]
    versionCode = re.findall("versionCode='([^']+)'", output ,re.I | re.M)[0]
    versionName = re.findall("versionName='([^']+)'", output ,re.I | re.M)[0]
    minSdk = re.findall("sdkVersion:'([^']+)'", output ,re.I | re.M)[0]

    print('apkName:' + apkName)
    print('packagename:' + packagename)
    print('versionCode:' + versionCode)
    print('versionName:' + versionName)
    print('minSdk:' + minSdk)

    #获取icon
    iconPath = ""
    try:
        iconPath = re.findall("icon='([^']+)'", output, re.I | re.M)[0]
        ext = os.path.splitext(iconPath)[-1][1:]
        print ("ext:",ext)
        if ext == 'xml':
            print ("Not support svg file.")
            iconPath = ""
    except IndexError:
        iconPath = ""

    print("iconPath:" + iconPath)

    #获取APK icon
    if iconPath == "":
        print ("IconPath is None")
    else:
        temPath = "temp"
        #let command = `"${decompressFile(getUnzipFileOriginPath())}" "${apkPath}" "${getTmpPath()}" "${iconPath}"`
        os.popen("unzip.exe {} {} {} ".format(apkpath,temPath,iconPath))
        iconLocalPath = temPath + "/" + os.path.basename(iconPath)
        print('iconLocalPath:' + iconLocalPath)

    # 获得所有的权限
    permissons = []
    outList = output.split('\n')
    for line in outList:
        if line.startswith('uses-permission'):
            per = line.split('=')[1]
            per = per.replace("'","")
            per = per.replace("\r", "")
            permissons.append(per)

    print (permissons)
    #判断是否存在敏感权限
    if PERMISSION_INSTALL_PACKAGES in permissons:
        print ("Has exist "+ PERMISSION_INSTALL_PACKAGES)

    if PERMISSION_DELETE_PACKAGES in permissons:
        print ("Has exist "+ PERMISSION_DELETE_PACKAGES)


def checkDangerousPermission(apkpath):
    #判断是否具有危险权限
    #1、安装器 、验证器、卸载器
    #>aapt d xmltree dytt_1.3.0_dangbei.apk AndroidManifest.xml

    xmlout = os.popen("aapt.exe d xmltree %s  AndroidManifest.xml"  % apkpath).read()
    #print (xmlout)

    actis = re.split(r"(E: activity|E: receiver|E: service)",xmlout)
    #print (actis)

    ACTION_INSTALL_PACKAGE = "android.intent.action.INSTALL_PACKAGE"
    ACTION_UNINSTALL_PACKAGE = "android.intent.action.UNINSTALL_PACKAGE"
    ACTION_INTENT_FILTER_NEEDS_VERIFICATION = "android.intent.action.INTENT_FILTER_NEEDS_VERIFICATION"
    CATEGORY_DEFAULT = "android.intent.category.DEFAULT"
    PACKAGE_MIME_TYPE="application/vnd.android.package-archive"
    PACKAGE_SCHEME = "package"


    #安装器的特征
    #<action android:name="android.intent.action.INSTALL_PACKAGE" />
    #<category android:name="android.intent.category.DEFAULT" />
    #<data android:mimeType="application/vnd.android.package-archive" />

    #卸载器特征
    #<action android:name="android.intent.action.UNINSTALL_PACKAGE" />
    #<category android:name="android.intent.category.DEFAULT" />
    #<data android:scheme="package" />

    #验证器特征
    # <action android:name="android.intent.action.INTENT_FILTER_NEEDS_VERIFICATION" />
    # <data android:mimeType="application/vnd.android.package-archive" />


    for item in actis:
        #print (item)

        isInAction = re.search(ACTION_INSTALL_PACKAGE, item, re.I | re.M)
        isUnAction = re.search(ACTION_UNINSTALL_PACKAGE, item, re.I | re.M)
        isVerifyAction = re.search(ACTION_INTENT_FILTER_NEEDS_VERIFICATION, item, re.I | re.M)
        isDefault = re.search(CATEGORY_DEFAULT, item, re.I | re.M)
        isPkgMimeType = re.search(PACKAGE_MIME_TYPE, item, re.I | re.M)
        isPkgscheme = re.search(PACKAGE_SCHEME, item, re.I | re.M)

        #print("All check isInAction:{},isUnAction:{},isVerifyAction:{},isDefault:{},isPkgMimeType:{},isPkgscheme:{}"
              #.format(isInAction, isUnAction, isVerifyAction,isDefault, isPkgMimeType, isPkgscheme))

        if isInAction and isDefault and isPkgMimeType:
            print ("\n")
            print ("====================================")
            print("result:Exist InstallPackage Activty!!!")
            print("====================================\n")


        if isUnAction and isDefault and isPkgscheme:

            print ("\n")
            print ("====================================")
            print("result:Exist UninstallPackage Activty!!!")
            print("====================================\n")

        if isVerifyAction and isPkgMimeType:

            print ("\n")
            print ("====================================")
            print("result:Exist Verification Receiver!!!")
            print("====================================\n")

if __name__ == '__main__':

    print(sys.getdefaultencoding() )
    apkName = "testApp/com.google.android.packageinstaller_7.0-24.apk"
    #apkName = "Facebook_v186.0.0.48.81_apkpure.com.apk"

    getAppBaseInfo(apkName)
    #checkDangerousPermission(apkName)

