# -*- coding: utf-8 -*-

__author__ = 'hal9000'

import sys

import xbmc
import xbmcgui
import xbmcplugin

import log

#from core import Log
#from gui import Progress, Text
from gui import Progress

class Log(object):
    def __call__(self, *args):
        for msg in args:
            xbmc.log('TEST: ' + str(msg))


class Test(object):
    def __init__(self, suite):
        self.suite = suite

    def test(self):
        pass

    def check(self, check, *args):
        if not check:
            if args:
                Log()(*args)
            raise Exception()

    def log(self, *args):
        log.log(*args)

    def text(self, text):
        Progress().close()
        Text(self.__class__.__name__ + '  -  ' + self.suite, text)
        Progress().render()

    def human(self):
        Progress().close()
        if not xbmcgui.Dialog().yesno(self.__class__.__name__ + '  -  ' + self.suite, 'Was the test passed?'):
            raise
        Progress().render()


class TestRun(object):
    Test = Test

    def __init__(self):
        self.tests = []

    def add(self, *args):
        if isinstance(args[0], bool):
            if not args[0]:
                return
            args = args[1:]

        test = {'id': str(len(self.tests))}

        if isinstance(args[0], basestring):
            test['name'] = args[0]
            args = args[1:]
        else:
            test['name'] = 'Suite ' + str(len(self.tests) + 1)

        test['class'] = args
        self.tests.append(test)

    def run(self):
        result, id = [], sys.argv[2][1:] if sys.argv[2] else None

        if id is not None:
            fail, result = self._test(id)
            if result:
                if id == 'all':
                    result.insert(0, {'id': 'all', 'name': '[COLOR=' + ('red' if fail else 'green') + ']All tests[/COLOR]'})
                else:
                    result.insert(0, {'id': 'all', 'name': 'All tests'})

                xbmc.executebuiltin('XBMC.Notification("%s", "%s", %s)' % ('Result', '[COLOR=red]Tests failed.[/COLOR]' if fail else '[COLOR=green]Tests passed.[/COLOR]', 5000))

        if not result:
            result = [{'id': 'all', 'name': 'All tests'}]
            result.extend([{'id': x['id'], 'name': '[COLOR=orange]' + x['name'] + '[/COLOR]   -   ' + ', '.join([y.__name__ for y in x['class']])} for x in self.tests])

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), [(sys.argv[0] + '?' + x['id'], xbmcgui.ListItem(x['name']), True) for x in result])
        xbmcplugin.endOfDirectory(int(sys.argv[1]), True, bool(id), False)


    def _test(self, id):
        count_suite, count_test, fail, result = 0, 0, False, []

        if id == 'all':
            total_suite = len(self.tests)
            total_test = 0
            for suite in self.tests:
                total_test += len(suite)
        else:
            suite = [x for x in self.tests if x['id'] == id]
            total_suite = 1
            total_test = len(suite[0]) if suite else 0

        if not total_test:
            return True, []

        progress = Progress()
        progress('Testing', 'Suite:', 'Test:', 'Result:', total_test)

        for suite in self.tests:
            if id == 'all' or id == suite['id']:

                count_suite += 1
                if not progress.render(line1='Suite:     ' + str(count_suite) + '/' + str(total_suite) + '  - ' + suite['name'], line3='Result:   ?'):
                    return True, []

                res, res_icon, fail_suite = [], [], False

                for i, test in enumerate(suite['class']):
                    if id == 'all' or not fail:
                        if not progress.render(line2='Test:      ' + str(i + 1) + '/' + str(len(suite['class'])) + '  - ' + test.__name__):
                            return True, []
                        try:
                            cls = test(suite['name'])
                            cls.test()
                        except:
                            import traceback
                            traceback.print_exc()

                            fail, fail_suite = True, True
                            res.append('[COLOR=red]' + test.__name__ + '[/COLOR]')
                            res_icon.append('[COLOR=red]F[/COLOR]')
                        else:
                            res.append(test.__name__)
                            res_icon.append('*')
                    else:
                        res.append(test.__name__)

                    count_test += 1
                    if not progress.render(count_test, line3='Result:   ' + '  '.join(res_icon) + '  ?'):
                        return True, []

                suite['name'] = '[COLOR=' + ('red' if fail_suite else 'orange') + ']' + suite['name'] + '[/COLOR]'
                result.append({'id': suite['id'], 'name': suite['name'] + '   -   ' + ', '.join(res)})

            else:
                result.append({'id': suite['id'], 'name': '[COLOR=orange]' + suite['name'] + '[/COLOR]   -   ' + ', '.join([x.__name__ for x in suite['class']])})

        progress.close()

        return fail, result

