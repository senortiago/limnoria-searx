###
# Copyright (c) 2016, lod
# All rights reserved.
#
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.utils.minisix as minisix

import json

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Searx')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class Searx(callbacks.Plugin):
    """does a search on https://searx.me/"""

    threaded = True
    filterlist = ['files', 'images', 'it', 'map', 'music', 'news', 'science', 'social', 'videos']
    
    def __init__(self, irc):
        self.__parent = super(Searx, self)
        self.__parent.__init__(irc)

    def search(self, query, channel, filters={}):
        """search("search phrase")"""
        
        opts = {'q': query, 'format': 'json'}
        for key, value in filters.items():
            opts[key] = value

        defaultLanguage = self.registryValue('defaultLanguage', channel)
        #if opts['language']:
        #    defaultLanguage = opts['language']

        ref = 'http://%s/%s' % (dynamic.irc.server, dynamic.irc.nick)
        headers = dict(utils.web.defaultHeaders)
        headers['Referer'] = ref
        headers['cookie'] = "%s=%s" % ('language', defaultLanguage)

        url = self.registryValue('url', channel)

        text = utils.web.getUrlFd('%s?%s' % (url, 
                                           utils.web.urlencode(opts)),
                                headers=headers)
        return text

    def getData(self, data):
        """creates Python Object with results from Json string"""
        data = json.loads(data.read().decode('utf-8'))
        data = data['results']
        return data

    def formatData(self, data, bold=True, max=0, onetoone=False):
        """formats Data for output"""
        data = self.getData(data)
        results = []
        if max:
            data = data[:max]

        for result in data:
            title = result['title']
            url = result['url']
            if minisix.PY2:
                url = url.encode('utf-8')
            if title:
                if bold:
                    title = ircutils.bold(title)
                results.append(format('%s: %u', title, url))
            else:
                results.append(url)
        if minisix.PY2:
            repl = lambda x:x if isinstance(x, unicode) else unicode(x, 'utf8')
            results = list(map(repl, results))
        if not results:
            return [_('No matches found.')]
        elif onetoone:
            return results
        else:
            return [minisix.u('; ').join(results)]

    def lucky(self, irc, msg, args, opts, text):
        """[--snippet] <search>
        Does a Searx search, but only returns the first result.
        If option --snippet is given, returns also the page text snippet.
        """

        opts = dict(opts)
        data = self.search(text, msg.args[0])
        data = self.getData(data)

        if data:
            url = data[0]['url']
            if 'snippet' in opts:
                snippet = data[0]['content']
                snippet = " | " + utils.web.htmlToText(snippet, tagReplace='')
            else:
                snippet = ""
            result = url + snippet
            irc.reply(result)
        else:
            irc.reply(_('searx found nothing.'))

    lucky = wrap(lucky, [getopts({'snippet':'',}), 'text'])

    def searx(self, irc, msg, args, opts, text):
        """[--filter <value>] <search>

	Searches Searx for the given string; --filter accepts (files, images, it, map, music, news, science, social, videos)
        """

        filter = {}
        if opts:
            opts = dict(opts)
            opts = opts['filter']
            if opts not in self.filterlist:
                irc.error('%s is not a valid filter option.' % opts)
            else:
                if opts == 'social':
                    filter = {'category_%s media' % opts:'on'}
                else:
                    filter = {'category_%s' % opts:'on'}

        try:
            data = self.search(text, msg.args[0], dict(filter))
            bold = self.registryValue('bold', msg.args[0])
            max = self.registryValue('maximumResults', msg.args[0])
            onetoone = self.registryValue('oneToOne', msg.args[0])
            for result in self.formatData(data,
                                  bold=bold, max=max, onetoone=onetoone):
                irc.reply(result)
        except:
            irc.reply(_('searx found nothing.'))

    searx = wrap(searx, [getopts({'language':'something','filter':'something'}),'text'])

Class = Searx


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
