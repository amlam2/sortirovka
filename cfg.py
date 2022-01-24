# coding=utf-8

from platform import system, architecture

## Директории Windows
if system() == 'Windows':
    DIR_TEMP = 'C:\\Temp'
    if architecture()[0] == '64bit':
        DIR_ARCH = 'D:\\gazette\\Sortirovka_smi\\arch'
    elif architecture()[0] == '32bit':
        DIR_ARCH = 'D:\\gazette\\Sortirovka_smi\\arch'
## Директории Linux
elif system() == 'Linux':
    DIR_TEMP = '/home/user/Temp'
    DIR_ARCH = '/home/user/gazette/Sortirovka_smi/arch'

# Данные для соединения с ftp-сервером ПАК
PAK_NODE   = '192.168.1.12'
PAK_USER   = 'pack'
PAK_PASSWD = 'u78sdw45'
PAK_ROOT   = '.'

# Данные для соединения с ftp-сервером УОСП (сортировка розницы)
RZN_NODE   = '192.168.1.18'
RZN_USER   = 'sort-arch'
RZN_PASSWD = '42tn5Yags7'
RZN_ROOT   = '.'

# 0 - не загружать файлы на FTP ПАК
# 1 - загружать файлы на FTP ПАК
UPLOAD_TO_FTP = 1

NEW_VALUE_OF_SERNAK_FIELD = u"ЯЭ"

# шаблон поиска исходных файлов в архиве
FILE_SEARCH_PATTERN = r'^[0-9]{3}%s[0-9]{5}.DBF$'

# шаблон поиска номеров накладных
NOMNAK_SEARCH_PATTERN = r'^5|4[0-9]{6}$'
