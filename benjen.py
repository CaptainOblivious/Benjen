from glob import glob
import os, re, sys, yaml
from markdown import markdown as pmarkdown
from functools import *

from mako.template import Template
from mako.lookup import TemplateLookup

def load_all(dir):
	return {fn[len(dir)+1:] : file(fn, 'r').read() for fn in glob(dir + '/*')}

class Benjen(object):
	def __init__(self):
		self.lookup = TemplateLookup(directories=['templates'])
		
		self.config = yaml.load(file('config.yaml'))

		self.out = self.config['path']
		if self.out[-1] != '/':
			self.out += '/'
		try:
			os.makedirs(self.out)
		except:
			pass

		self.load_entries()

		self.generate_indexes()
		map(self.generate_post, self.entries)

	def render(self, name, **kwargs):
		return self.lookup.get_template('/' + name + '.html').render(**kwargs)

	def markdown(self, text):
		return pmarkdown(text)

	def link(self, fn):
		return fn

	title_sub = partial(re.compile(r'[^a-zA-Z0-9_\-"\']').sub, '_')
	def load_entries(self):
		raw = load_all('entries')

		self.entries = []
		for entry in raw.values():
			title = None
			date = None
			while True:
				if not entry or entry[0] != '#':
					break
				line, entry = entry.split('\n', 1)
				type, rest = line[1:].split(' ', 1)
				if type == 'title':
					title = rest
				elif type == 'date':
					date = rest
				else:
					assert False

			fn = date + '_' + self.title_sub(title) + '.html'
			self.entries.append(dict(
				title=title, 
				date=date, 
				raw=entry, 
				html=self.markdown(entry), 
				file=fn, 
				link=self.link(fn)
			))

		self.entries.sort(lambda a, b: cmp(b['date'], a['date']))

	def generate_indexes(self):
		per = self.config['per_page']
		genFn = lambda i: 'index.html' if i == 0 else 'index_%i.html' % (i / per)
		for i in xrange(0, len(self.entries), per):
			with file(self.out + genFn(i), 'w') as fp:
				fp.write(self.render('index', 
					page=(i / per) + 1, 
					prev=None if i == 0 else self.link(genFn(i - per)), 
					next=None if i + per >= len(self.entries) else self.link(genFn(i + per)), 
					posts=self.entries[i:i+per]
				))

	def generate_post(self, post):
		with file(self.out + post['file'], 'w') as fp:
			fp.write(self.render('post', post=post))

if __name__=='__main__':
	Benjen(*sys.argv[1:])
