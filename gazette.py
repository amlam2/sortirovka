#!/usr/bin/env python
#coding=utf-8

import os
import ftplib
import time
from glob import glob1
from re import split, compile
from shutil import copy2
from dbfpy import dbf
from cfg import *

def gazette():
    os.chdir(DIR_TEMP)

    spaceLineString = ' '*4 + '='*80
    print u'>>> 1. Введите номер накладной (без серии). Если их несколько, разделите их запятой'
    print spaceLineString
    ask = raw_input('\t--> ')
    if ask:
        ## Сформировать список номеров накладных из строки, введённой пользователем
        nomNakList = split(r'\W', ask)
        nomNakPattern = compile(NOMNAK_SEARCH_PATTERN)
        for nomNak in nomNakList[:]:
            if nomNakPattern.search(nomNak) is None:
                nomNakList.remove(nomNak)
        nomNakList = [int(i) for i in nomNakList[:]] # <<<- список номеров накладных
        ##
        
        ## Найти в архиве файлы, содержащие заданные номера накладных
        if nomNakList:
            numberDayList = list(set([str(i)[-3:] for i in nomNakList])) # <<<- список порядковых номеров дней в году
            #print 'numberDayList=', numberDayList
            print
            print u'>>> 2. Поиск исходных файлов в архиве на FTP-сервере УОСП'
            print spaceLineString
            print
            print u'\tftp://{} - соединение открыто'.format(RZN_NODE)

            print u'\tЗагрузка файлов:'

            downloadedFilesList = get_from_ftp(numberDayList)

            for downloadedFile in downloadedFilesList:
                print u'\t\t- файл {} успешно загружен'.format(downloadedFile)
            
            if not downloadedFilesList: print '\t\t-', u'Нет файлов.'

            print u'\tГотово!'
            print u'\tftp://{} - соединение закрыто'.format(RZN_NODE)
            print
            print '\t\t-', u'Всего загружено файлов - %s' % (len(downloadedFilesList),)

            if downloadedFilesList:
                #tmpDict = {}
                entriesDict = {} # <<<- словарь копируемых файлов
                for file in downloadedFilesList:
                    entriesList = [] # <<<- список вхождений номеров накладных в файл
                    table = dbf.Dbf(os.path.join(DIR_TEMP, file))
                    datad = table[0]['DATAD']
                    for record in table:
                        nomNak = record['NOMNAK']
                        if nomNak in nomNakList and not nomNak in entriesList: # <<<- комментарий
                            entriesList.append(nomNak)
                    table.close()

                    entriesDict[file] = { 
                                          'uploadDate'  : datad,
                                          'entriesList' : entriesList
                                        }
                ## Вывести в консоль таблицу вхождений
                if entriesDict:
                    headTableString = u'\tИмя файла\t|\tДата выгрузки\t|\tНакладные'
                    spaceTableString = ' ' + '-'*23 + '+' + '-'*23 + '+' + '-'*35
                    bodyTableTemplate = u'\t{}\t|\t{}\t|\t{}'
                    print
                    #print 'entriesDict=', entriesDict   ### для отладки
                    print u'>>> 3. Таблица вхождений накладных по каждому файлу'
                    print spaceLineString
                    print
                    print headTableString
                    print spaceTableString
                    for file in entriesDict.keys():
                        print bodyTableTemplate.format(
                                                        file,
                                                        entriesDict[file].get('uploadDate').strftime('%d.%m.%Y'),
                                                        ' ,'.join([str(i) for i in entriesDict[file].get('entriesList')]) or u'Не найдено'
                                                      )
                    print spaceTableString

                ## Сформировать новую таблицу
                if entriesDict:
                    workingFileList = [] # список файлов, в которых будут произведены изменения: остальные удалить
                    print
                    print u'>>> 4. Обработка файлов, содержащих введённые номера накладных'
                    print spaceLineString
                    print
                    for file in entriesDict.keys():
                        if entriesDict[file].get('entriesList'):
                            # Открыть старый и новый dbf-файлы
                            oldNakTable = dbf.Dbf(file)
                            currentTime = time.strftime('%H%M%S', time.localtime())
                            nameTempFile = "~" + currentTime + ".tmp"
                            newNakTable = dbf.Dbf(nameTempFile, new=True)

                            # Копировать структуру dbf-файла
                            for field in oldNakTable.header.fields:
                                newNakTable.addField(field)

                            # Заполнить новую таблицу на основе страрой,
                            # включая в неё только записи с номером накладной
                            # из списка
                            for record in oldNakTable:
                                new_record = newNakTable.newRecord()
                                if record['NOMNAK'] in nomNakList:
                                    new_record.fieldData = record
                                    new_record.store() # сохраняем текущую запись

                            oldNakTable.close()
                            newNakTable.close()

                            # Заменить таблицы, старую удалить
                            os.remove(file)
                            os.rename(nameTempFile, file)
                            workingFileList.append(file)
                            print u'\t- в файле {} оставлены только введённые накладные'.format(file)
                        else:
                            os.remove(file)
                            print u'\t- файл {} удалён, поскольку не содержит введённых накладных'.format(file)

                ## Изменить серию накладной
                if workingFileList:
                    print
                    print u'>>> 5. Изменение серии накладных по каждому файлу'
                    print spaceLineString
                    print
                    for file in workingFileList:
                        table = dbf.Dbf(file)
                        for item in xrange(len(table)):
                            rec = table[item]
                            rec['SERNAK'] = NEW_VALUE_OF_SERNAK_FIELD.encode('cp866')
                            rec.store()
                            del rec
                        table.close()
                        print u'\t- в файле {} произведено изменение серии накладных на "{}"'.format(file, NEW_VALUE_OF_SERNAK_FIELD)


                ## Передать файлы на ftp-сервер ПАК
                if workingFileList and UPLOAD_TO_FTP:
                    print
                    print u'>>> 6. Выгрузка обработаных файлов на FTP-сервер ПАК'
                    print spaceLineString
                    print
                    print u'\tftp://{} - соединение открыто'.format(PAK_NODE)
                    print u'\tВыгрузка файлов:'
                    
                    uploadedFilesDict = put_to_ftp(workingFileList)

                    if uploadedFilesDict:
                        for uploadedFile in uploadedFilesDict.keys():
                            if uploadedFilesDict.get(uploadedFile):
                                print u'\t\t- файл {} успешно выгружен'.format(uploadedFile)
                            else:
                                print u'\t\t- файл {} не выгружен'.format(uploadedFile)
                    else:
                        print u'\t\t- нет файлов для выгрузки'
            
                    print u'\tГотово!'
                    print u'\tftp://{} - соединение закрыто'.format(PAK_NODE)
                    print
                    print u'\t\t- Всего выгружено файлов - {}'.format(len(uploadedFilesDict.keys()))


                    # Очистка временного каталога
                    for file in workingFileList:
                        if uploadedFilesDict.get(file):
                            os.remove(file)

## Функция загружает исходне файлы с ftp-сервера УОСП (сортировка розницы)
def get_from_ftp(numberDayList):
    copiedFilesList = []
    try:
        ftp = ftplib.FTP(RZN_NODE)
        ftp.login(RZN_USER, RZN_PASSWD)
        ftp.cwd(RZN_ROOT)

        for numberDay in numberDayList:
            pattern = compile(FILE_SEARCH_PATTERN % numberDay)
            for fileName in ftp.nlst():
                if pattern.search(fileName) is not None:
                    hostFile = os.path.join(DIR_TEMP, fileName)
                    try:
                        with open(hostFile, 'wb') as localFile:
                            ftp.retrbinary('RETR ' + fileName, localFile.write)
                        copiedFilesList.append(fileName)
                    except ftplib.error_perm:
                        copiedFilesList

        ftp.quit()
        return copiedFilesList
    except:
        return copiedFilesList

## Функция передаёт файлы на ftp-сервер ПАК
def put_to_ftp(workingFileList):
    statusWorkingFileDict = {}
    try:
        ftp = ftplib.FTP(PAK_NODE)
        ftp.login(PAK_USER, PAK_PASSWD)
        ftp.cwd(PAK_ROOT)

        for fileName in workingFileList:
            # Отправка файла по ftp
            localFile = os.path.join(DIR_TEMP, fileName)
            try:
                with open(localFile, 'rb') as hostFile:
                    ftp.storbinary("STOR " + fileName, hostFile)
                statusWorkingFileDict[fileName] = True
            except ftplib.error_perm:
                statusWorkingFileDict[fileName] = False

        ftp.quit()
        return statusWorkingFileDict
    except:
        return statusWorkingFileDict

if __name__ == "__main__":
    print
    print
    gazette()
    print
    print u"Для выхода нажмите клавишу <Enter>..."
    raw_input()
