# coding=utf-8
"""
etymology.py - Sopel Etymology Module
Copyright 2007-9, Sean B. Palmer, inamidst.com
Licensed under the Eiffel Forum License 2.
http://sopel.chat
"""
from __future__ import unicode_literals, absolute_import, print_function, division

import re
import glados
import urllib.request
import urllib.parse


class Etymology(glados.Module):

    etyuri = 'http://etymonline.com/?'

    r_definition = re.compile(r'(?ims)<dd[^>]*>.*?</dd>')
    r_tag = re.compile(r'<(?!!)[^>]+>')
    r_whitespace = re.compile(r'[\t\r\n ]+')

    abbrs = [
        'cf', 'lit', 'etc', 'Ger', 'Du', 'Skt', 'Rus', 'Eng', 'Amer.Eng', 'Sp',
        'Fr', 'N', 'E', 'S', 'W', 'L', 'Gen', 'J.C', 'dial', 'Gk',
        '19c', '18c', '17c', '16c', 'St', 'Capt', 'obs', 'Jan', 'Feb', 'Mar',
        'Apr', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec', 'c', 'tr', 'e', 'g'
    ]
    t_sentence = r'^.*?(?<!%s)(?:\.(?= [A-Z0-9]|\Z)|\Z)'
    r_sentence = re.compile(t_sentence % ')(?<!'.join(abbrs))

    def text(self, html):
        html = self.r_tag.sub('', html)
        html = self.r_whitespace.sub(' ', html)
        return urllib.parse.unquote(html)

    def etymology(self, word):
        # @@ <nsh> sbp, would it be possible to have a flag for .ety to get 2nd/etc
        # entries? - http://swhack.com/logs/2006-07-19#T15-05-29

        if len(word) > 25:
            raise ValueError("Word too long: %s[...]" % word[:10])
        word = {'axe': 'ax/axe'}.get(word, word)

        uri = self.etyuri + urllib.parse.urlencode(dict(term=word))
        bytes = urllib.request.urlopen(uri).read().decode('utf-8')
        definitions = self.r_definition.findall(bytes)

        if not definitions:
            return None

        defn = self.text(definitions[0])
        m = self.r_sentence.match(defn)
        if not m:
            return None
        sentence = m.group(0)

        maxlength = 275
        if len(sentence) > maxlength:
            sentence = sentence[:maxlength]
            words = sentence[:-5].split(' ')
            words.pop()
            sentence = ' '.join(words) + ' [...]'

        sentence = '"' + sentence.replace('"', "'") + '"'
        return sentence + ' - ' + uri

    @glados.Module.command('ety', '<word>', 'Looks up the etymology of a word.')
    async def f_etymology(self, message, word):
        """Look up the etymology of a word"""

        try:
            result = self.etymology(word)
        except IOError:
            msg = "Can't connect to etymonline.com (%s)" % (self.etyuri % word)
            await self.client.send_message(message.channel, msg)
            return

        if result is not None:
            await self.client.send_message(message.channel, result)
        else:
            uri = self.etyuri + urllib.parse.urlencode(dict(search=word))
            msg = 'Can\'t find the etymology for "%s". Try %s' % (word, uri)
            await self.client.send_message(message.channel, msg)
            return
