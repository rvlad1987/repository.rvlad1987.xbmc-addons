# API


## xbmcup.app

### class Handler
Этот класс необходимо переопределить на свой.

#### Методы класса

##### handle()

Основной метод, который нужно переопределить. В нем должен находится весь код, который определяет вызов плагина.

##### item(title, url[, label, folder, media, info, property, menu, menu_replace, icon, cover, fanart, color1, color2, color3, total])

Добавляет пункт в список вывода. Параметры:

* _title_ - string. Наименование пункта, которое будет выведено на экран
* _url_ - string|method. Ссылка, которая указывает на *следующий* хандлер. Ссылки организуются с помощью методов `link`, `replace`, `resolve`, `play`, `null`. Если передается `string`, то автоматически вызовится `play(строка)`
* _label_ - string. Определяет метку `label2`
* _folder_ - bool. Если в `folder` передается `True`, то пункт будет выводится в качестве директории. Если `False` (по умолчанию), то как файл.
* _media_ - string. Тип медиа-инфо файла. Может принимать одно из трех значений: `video`, `audio`, `picture`. Если вы не передаете в метод параметр `info`, то этот параметр игнорируется
* _info_ - dict. Словарь, устанавливающий медиа-инфо. Значения `key: value` дублируются из метода [setInfo](http://mirrors.xbmc.org/docs/python-docs/xbmcgui.html#ListItem-setInfo). В значение `trailer` можно передовать один из методов определения ссылок (`link`, `replace` и т.д.)
* _property_ - dict. Словарь, передающий значения (`key: value`) в метод [setProperty](http://mirrors.xbmc.org/docs/python-docs/xbmcgui.html#ListItem-setProperty)
* _menu_ - list|tuple. Передает контекстное меню, котое состоит из списка кортежей , вида `[(title1, url1), (title2, url2), ..., (titleN, urlN)]`. Значение `url` в кортежах определяется также, как и `url` для метода `item`
* _menu_replace_ - bool. Если в параметр передается `False` (по умолчанию), то контекстное меню будет присоеденено к основному. Если `True`, то основное меню будет заменено
* _icon_ - string. Путь к файлу иконки пункта. Возможен URL
* _cover_ - string. Путь к файлу обложки пункта. Возможен URL
* _fanart_ - string. Путь к файлу фанарта пункта. Возможен URL
* _color1, color2, color3_ - цвета фанарта пункта, вида `FFBBCC00`
* _color1, color2, color3_ - общее кол-во пунктов на странице

##### render([title, content, sort, mode, fanart, color1, color2, color3, replace, cache])

Выводит на экран все пункты списка, переданные ранее. Параметры:

* _title_ - string. Наименование списка. Некоторые скрины поддерживают этот параметр
* _content_ - string. Тип выводимого списка. Возможные значения: `files`, `songs`, `artists`, `albums`, `movies`, `tvshows`, `episodes`, `musicvideos`
* _sort_ - string. Способ сортировки списка. Возможные значения: урезанные значения SORT из [xbmcplugin](http://mirrors.xbmc.org/docs/python-docs/xbmcplugin.html)
* _mode_ - вид отображаемого списка. Возможные значения: `list`, `biglist`, `info`, `icon`, `bigicon`, `view`, `view2`, `thumb`, `round`, `fanart1`, `fanart2`, `fanart3`
* _fanart_ - string. Путь к файлу фанарта списка. Возможен URL
* _color1, color2, color3_ - цвета фанарта списка, вида `FFBBCC00`
* _replace_ - bool. `True` - будет заменено предыдущее окно. `False` - список будет выведен в новое окно. Если параметр не определен, то будет применена установка из родительского окна, в зависимости от того, чем было вызвано текущее окно (`link` или `replace`)
* _cache_ - bool. Указание - будет ли кэшироваться окно или нет. По умолчанию - True.

##### reset()

##### link(route[, argv])

##### replace(route[, argv])

##### resolve(route[, argv])

##### plugin(???)

##### play(filename)

##### null()


### class Plugin

Класс, запускающий все приложение. Если нужно сделать серию обновлений, то его нужно переопределить на свой класс и добавить методы `update`

#### Методы класса

##### route(route, classname)

Добавляет в приложение хандлер

* _route_ - string. Строковое наименование хандлера. Если передан `None`, то этот класс будет использоваться в качестве *index*-хандлера
* _classname_ - class. Класс, производный от класса Handler

##### run([params])

Запуск плагина

* _params_ - глобальные параметры. Могут быть любые параметры вида `**kwargs`. В дальнейшем доступне в объекте класса `Handler` в виде словаря `self.params`


## xbmcup.cache

## xbmcup.fs

## xbmcup.gui

## xbmcup.lang

## xbmcup.nosql

## xbmcup.regex

## xbmcup.setting

## xbmcup.sql

## xbmcup.test
