#!/usr/bin/env python
# coding: utf-8

"""
        from http://majid.info/blog/just-enough-weave/

    Based on tools/scripts/weave_server.py from
    http://hg.mozilla.org/labs/weave/
 
    do the Simplest Thing That Can Work: just enough to get by with Weave 0.6
    - SSL, authentication and loggin are done by nginx or other reverse proxy
    - no persistence, in case of process failure do a full resync
    - only one user. If you need more, create multiple instances on different
        ports and use rewrite rules to route traffic to the right one
"""

import sys, time, logging, socket, urlparse, httplib, pprint
try:
    import simplejson as json
except ImportError:
    import json
import wsgiref.simple_server

#BIND_IP = '127.0.0.1'
BIND_IP = '192.168.7.20'
URL_BASE = 'http://%s' % BIND_IP
#BIND_IP = ''
DEFAULT_PORT = 8000


class HttpResponse:
    def __init__(self, code, content='', content_type='text/plain'):
        self.status = '%s %s' % (code, httplib.responses.get(code, ''))
        self.headers = [('Content-type', content_type),
                                        ('X-Weave-Timestamp', str(timestamp()))]
        self.content = content or self.status

    def debug(self):
        print "status: %r" % self.status
        print "headers: %r" % self.headers
        print "content: %r" % self.content


def JsonResponse(value):
    return HttpResponse(httplib.OK, value, content_type='application/json')


class HttpRequest:
    def __init__(self, environ):
        self.environ = environ
        content_length = environ.get('CONTENT_LENGTH')
        if content_length:
            stream = environ['wsgi.input']
            self.contents = stream.read(int(content_length))
            print "request contents: %r" % self.contents
        else:
            self.contents = ''


def timestamp():
    # Weave rounds to 2 digits and so must we, otherwise rounding errors will
    # influence the "newer" and "older" modifiers
    return round(time.time(), 2)

class WeaveApp():
    """WSGI app for the Weave server"""
    def __init__(self):
        self.collections = {}

    def url_base(self):
        """XXX should derive this automagically from self.request.environ"""
        return URL_BASE

    def ts_col(self, col):
        self.collections.setdefault('timestamps', {})[col] = str(timestamp())

    def parse_url(self, path):
        print "parse_url: %r" % path
        if not path.startswith('/0.5/') and not path.startswith('/1.0/'):
            return
        command, args = path.split('/', 4)[3:]
        return command, args

    def opts_test(self, opts):
        if 'older' in opts:
            return float(opts['older'][0]).__ge__
        elif 'newer' in opts:
            return float(opts['newer'][0]).__le__
        else:
            return lambda x: True

    # HTTP method handlers

    def _handle_PUT(self, path, environ):
        command, args = self.parse_url(path)
        col, key = args.split('/', 1)
        assert command == 'storage'
        val = self.request.contents
        if val[0] == '{':
            val = json.loads(val)
            val['modified'] = timestamp()
            val = json.dumps(val, sort_keys=True)
        self.collections.setdefault(col, {})[key] = val
        self.ts_col(col)
        return HttpResponse(httplib.OK)

    def _handle_POST(self, path, environ):
        try:
            status = httplib.NOT_FOUND
            if path.startswith('/0.5/') or path.startswith('/1.0/'):
                command, args = self.parse_url(path)
                col = args.split('/')[0]
                vals = json.loads(self.request.contents)
                for val in vals:
                    val['modified'] = timestamp()
                    self.collections.setdefault(col, {})[val['id']] = json.dumps(val)
                self.ts_col(col)
                status = httplib.OK
        finally:
            return HttpResponse(status)

    def _handle_DELETE(self, path, environ):
        assert path.startswith('/0.5/') or path.startswith('/1.0/')
        response = HttpResponse(httplib.OK)
        if path.endswith('/storage/0'):
            self.collections.clear()
        elif path.startswith('/0.5/') or path.startswith('/1.0/'):
            command, args = self.parse_url(path)
            col, key = args.split('/', 1)
            if not key:
                opts = urlparse.parse_qs(environ['QUERY_STRING'])
                test = self.opts_test(opts)
                col = self.collections.setdefault(col, {})
                for key in col.keys():
                    if test(json.loads(col[key]).get('modified', 0)):
                        logging.info('DELETE %s key %s' % (path, key))
                        del col[key]
            else:
                try:
                    del self.collections[col][key]
                except KeyError:
                    return HttpResponse(httplib.NOT_FOUND)
        return response

    def _handle_GET(self, path, environ):
        if path.startswith('/0.5/') or path.startswith('/1.0/'):
            command, args = self.parse_url(path)
            return self.handle_storage(command, args, path, environ)
        elif path.startswith('/1/'):
            return HttpResponse(httplib.OK, self.url_base())
        elif path.startswith('/state'):
            return HttpResponse(httplib.OK, pprint.pformat(self.collections))
        else:
            return HttpResponse(httplib.NOT_FOUND)

    def handle_storage(self, command, args, path, environ):
        if command == 'info':
            if args == 'collections':
                return JsonResponse(json.dumps(self.collections.get('timestamps', {})))
        if command == 'storage':
            if '/' in args:
                col, key = args.split('/')
            else:
                col, key = args, None
            try:
                if not key: # list output requested
                    opts = urlparse.parse_qs(environ['QUERY_STRING'])
                    test = self.opts_test(opts)
                    result = []
                    for val in self.collections.setdefault(col, {}).itervalues():
                        val = json.loads(val)
                        if test(val.get('modified', 0)):
                            result.append(val)
                    result = sorted(result,
                                                    key=lambda val: (val.get('sortindex'),
                                                                                     val.get('modified')),
                                                    reverse=True)
                    if 'limit' in opts:
                        result = result[:int(opts['limit'][0])]
                    logging.info('result set len = %d' % len(result))
                    if 'application/newlines' in environ.get('HTTP_ACCEPT', ''):
                        value = '\n'.join(json.dumps(val) for val in result)
                        return HttpResponse(httplib.OK, value,
                                                                content_type='application/text')
                    else:
                        return JsonResponse(json.dumps(result))
                else:
                    return JsonResponse(self.collections.setdefault(col, {})[key])
            except KeyError:
                if not key: raise
                return HttpResponse(httplib.NOT_FOUND, '"record not found"',
                                                        content_type='application/json')

    def __process_handler(self, handler):
        path = self.request.environ['PATH_INFO']
        response = handler(path, self.request.environ)
        return response

    def __call__(self, environ, start_response):
        """Main WSGI application method"""

        self.request = HttpRequest(environ)
        method = '_handle_%s' % environ['REQUEST_METHOD']
        print environ['REQUEST_METHOD']

        # See if we have a method called 'handle_METHOD', where
        # METHOD is the name of the HTTP method to call.    If we do,
        # then call it.
        if hasattr(self, method):
            handler = getattr(self, method)
            response = self.__process_handler(handler)
        else:
            response = HttpResponse(httplib.METHOD_NOT_ALLOWED,
                                                            'Method %s is not yet implemented.' % method)

        response.debug()
        print "*** collections:"
        pprint.pprint(self.collections)
        print " -" * 40
        start_response(response.status, response.headers)
        return [response.content]

class NoLogging(wsgiref.simple_server.WSGIRequestHandler):
    def log_request(self, *args):
        pass

if __name__ == '__main__':
    socket.setdefaulttimeout(300)
    if '-v' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
        handler_class = wsgiref.simple_server.WSGIRequestHandler
    else:
        logging.basicConfig(level=logging.ERROR)
        handler_class = NoLogging
    logging.info('Serving on port %d.' % DEFAULT_PORT)
    app = WeaveApp()
    httpd = wsgiref.simple_server.make_server(BIND_IP, DEFAULT_PORT, app,
                                                                                        handler_class=handler_class)
    httpd.serve_forever()
"""
    Based on tools/scripts/weave_server.py from
    http://hg.mozilla.org/labs/weave/
 
    do the Simplest Thing That Can Work: just enough to get by with Weave 0.6
    - SSL, authentication and loggin are done by nginx or other reverse proxy
    - no persistence, in case of process failure do a full resync
    - only one user. If you need more, create multiple instances on different
        ports and use rewrite rules to route traffic to the right one
"""

import sys, time, logging, socket, urlparse, httplib, pprint
try:
    import simplejson as json
except ImportError:
    import json
import wsgiref.simple_server

URL_BASE = 'https://your.server.name/'
#BIND_IP = ''
BIND_IP = '127.0.0.1'
DEFAULT_PORT = 8000

class HttpResponse:
    def __init__(self, code, content='', content_type='text/plain'):
        self.status = '%s %s' % (code, httplib.responses.get(code, ''))
        self.headers = [('Content-type', content_type),
                                        ('X-Weave-Timestamp', str(timestamp()))]
        self.content = content or self.status

def JsonResponse(value):
    return HttpResponse(httplib.OK, value, content_type='application/json')

class HttpRequest:
    def __init__(self, environ):
        self.environ = environ
        content_length = environ.get('CONTENT_LENGTH')
        if content_length:
            stream = environ['wsgi.input']
            self.contents = stream.read(int(content_length))
        else:
            self.contents = ''

def timestamp():
    # Weave rounds to 2 digits and so must we, otherwise rounding errors will
    # influence the "newer" and "older" modifiers
    return round(time.time(), 2)

class WeaveApp():
    """WSGI app for the Weave server"""
    def __init__(self):
        self.collections = {}

    def url_base(self):
        """XXX should derive this automagically from self.request.environ"""
        return URL_BASE

    def ts_col(self, col):
        self.collections.setdefault('timestamps', {})[col] = str(timestamp())

    def parse_url(self, path):
        if not path.startswith('/0.5/') and not path.startswith('/1.0/'):
            return
        command, args = path.split('/', 4)[3:]
        return command, args

    def opts_test(self, opts):
        if 'older' in opts:
            return float(opts['older'][0]).__ge__
        elif 'newer' in opts:
            return float(opts['newer'][0]).__le__
        else:
            return lambda x: True

    # HTTP method handlers

    def _handle_PUT(self, path, environ):
        command, args = self.parse_url(path)
        col, key = args.split('/', 1)
        assert command == 'storage'
        val = self.request.contents
        if val[0] == '{':
            val = json.loads(val)
            val['modified'] = timestamp()
            val = json.dumps(val, sort_keys=True)
        self.collections.setdefault(col, {})[key] = val
        self.ts_col(col)
        return HttpResponse(httplib.OK)

    def _handle_POST(self, path, environ):
        try:
            status = httplib.NOT_FOUND
            if path.startswith('/0.5/') or path.startswith('/1.0/'):
                command, args = self.parse_url(path)
                col = args.split('/')[0]
                vals = json.loads(self.request.contents)
                for val in vals:
                    val['modified'] = timestamp()
                    self.collections.setdefault(col, {})[val['id']] = json.dumps(val)
                self.ts_col(col)
                status = httplib.OK
        finally:
            return HttpResponse(status)

    def _handle_DELETE(self, path, environ):
        assert path.startswith('/0.5/') or path.startswith('/1.0/')
        response = HttpResponse(httplib.OK)
        if path.endswith('/storage/0'):
            self.collections.clear()
        elif path.startswith('/0.5/') or path.startswith('/1.0/'):
            command, args = self.parse_url(path)
            col, key = args.split('/', 1)
            if not key:
                opts = urlparse.parse_qs(environ['QUERY_STRING'])
                test = self.opts_test(opts)
                col = self.collections.setdefault(col, {})
                for key in col.keys():
                    if test(json.loads(col[key]).get('modified', 0)):
                        logging.info('DELETE %s key %s' % (path, key))
                        del col[key]
            else:
                try:
                    del self.collections[col][key]
                except KeyError:
                    return HttpResponse(httplib.NOT_FOUND)
        return response

    def _handle_GET(self, path, environ):
        if path.startswith('/0.5/') or path.startswith('/1.0/'):
            command, args = self.parse_url(path)
            return self.handle_storage(command, args, path, environ)
        elif path.startswith('/1/'):
            return HttpResponse(httplib.OK, self.url_base())
        elif path.startswith('/state'):
            return HttpResponse(httplib.OK, pprint.pformat(self.collections))
        else:
            return HttpResponse(httplib.NOT_FOUND)

    def handle_storage(self, command, args, path, environ):
        if command == 'info':
            if args == 'collections':
                return JsonResponse(json.dumps(self.collections.get('timestamps', {})))
        if command == 'storage':
            if '/' in args:
                col, key = args.split('/')
            else:
                col, key = args, None
            try:
                if not key: # list output requested
                    opts = urlparse.parse_qs(environ['QUERY_STRING'])
                    test = self.opts_test(opts)
                    result = []
                    for val in self.collections.setdefault(col, {}).itervalues():
                        val = json.loads(val)
                        if test(val.get('modified', 0)):
                            result.append(val)
                    result = sorted(result,
                                                    key=lambda val: (val.get('sortindex'),
                                                                                     val.get('modified')),
                                                    reverse=True)
                    if 'limit' in opts:
                        result = result[:int(opts['limit'][0])]
                    logging.info('result set len = %d' % len(result))
                    if 'application/newlines' in environ.get('HTTP_ACCEPT', ''):
                        value = '\n'.join(json.dumps(val) for val in result)
                        return HttpResponse(httplib.OK, value,
                                                                content_type='application/text')
                    else:
                        return JsonResponse(json.dumps(result))
                else:
                    return JsonResponse(self.collections.setdefault(col, {})[key])
            except KeyError:
                if not key: raise
                return HttpResponse(httplib.NOT_FOUND, '"record not found"',
                                                        content_type='application/json')

    def __process_handler(self, handler):
        path = self.request.environ['PATH_INFO']
        response = handler(path, self.request.environ)
        return response

    def __call__(self, environ, start_response):
        """Main WSGI application method"""

        self.request = HttpRequest(environ)
        method = '_handle_%s' % environ['REQUEST_METHOD']

        # See if we have a method called 'handle_METHOD', where
        # METHOD is the name of the HTTP method to call.    If we do,
        # then call it.
        if hasattr(self, method):
            handler = getattr(self, method)
            response = self.__process_handler(handler)
        else:
            response = HttpResponse(httplib.METHOD_NOT_ALLOWED,
                                                            'Method %s is not yet implemented.' % method)

        start_response(response.status, response.headers)
        return [response.content]

class NoLogging(wsgiref.simple_server.WSGIRequestHandler):
    def log_request(self, *args):
        pass

if __name__ == '__main__':
    socket.setdefaulttimeout(300)
    if '-v' in sys.argv:
        logging.basicConfig(level=logging.DEBUG)
        handler_class = wsgiref.simple_server.WSGIRequestHandler
    else:
        logging.basicConfig(level=logging.ERROR)
        handler_class = NoLogging
    logging.info('Serving on port %d.' % DEFAULT_PORT)
    app = WeaveApp()
    httpd = wsgiref.simple_server.make_server(BIND_IP, DEFAULT_PORT, app,
                                                                                        handler_class=handler_class)
    httpd.serve_forever()
"""
    Based on tools/scripts/weave_server.py from
    http://hg.mozilla.org/labs/weave/
 
    do the Simplest Thing That Can Work: just enough to get by with Weave 0.6
    - SSL, authentication and loggin are done by nginx or other reverse proxy
    - no persistence, in case of process failure do a full resync
    - only one user. If you need more, create multiple instances on different
        ports and use rewrite rules to route traffic to the right one
"""

import sys, time, logging, socket, urlparse, httplib, pprint
try:
    import simplejson as json
except ImportError:
    import json
import wsgiref.simple_server

URL_BASE = 'https://your.server.name/'
#BIND_IP = ''
BIND_IP = '127.0.0.1'
DEFAULT_PORT = 8000

class HttpResponse:
    def __init__(self, code, content='', content_type='text/plain'):
        self.status = '%s %s' % (code, httplib.responses.get(code, ''))
        self.headers = [('Content-type', content_type),
                                        ('X-Weave-Timestamp', str(timestamp()))]
        self.content = content or self.status

def JsonResponse(value):
    return HttpResponse(httplib.OK, value, content_type='application/json')

class HttpRequest:
    def __init__(self, environ):
        self.environ = environ
        content_length = environ.get('CONTENT_LENGTH')
        if content_length:
            stream = environ['wsgi.input']
            self.contents = stream.read(int(content_length))
        else:
            self.contents = ''

def timestamp():
    # Weave rounds to 2 digits and so must we, otherwise rounding errors will
    # influence the "newer" and "older" modifiers
    return round(time.time(), 2)

class WeaveApp():
    """WSGI app for the Weave server"""
    def __init__(self):
        self.collections = {}

    def url_base(self):
        """XXX should derive this automagically from self.request.environ"""
        return URL_BASE

    def ts_col(self, col):
        self.collections.setdefault('timestamps', {})[col] = str(timestamp())

    def parse_url(self, path):
        if not path.startswith('/0.5/') and not path.startswith('/1.0/'):
            return
        command, args = path.split('/', 4)[3:]
        return command, args

    def opts_test(self, opts):
        if 'older' in opts:
            return float(opts['older'][0]).__ge__
        elif 'newer' in opts:
            return float(opts['newer'][0]).__le__
        else:
            return lambda x: True

    # HTTP method handlers

    def _handle_PUT(self, path, environ):
        command, args = self.parse_url(path)
        col, key = args.split('/', 1)
        assert command == 'storage'
        val = self.request.contents
        if val[0] == '{':
            val = json.loads(val)
            val['modified'] = timestamp()
            val = json.dumps(val, sort_keys=True)
        self.collections.setdefault(col, {})[key] = val
        self.ts_col(col)
        return HttpResponse(httplib.OK)

    def _handle_POST(self, path, environ):
        try:
            status = httplib.NOT_FOUND
            if path.startswith('/0.5/') or path.startswith('/1.0/'):
                command, args = self.parse_url(path)
                col = args.split('/')[0]
                vals = json.loads(self.request.contents)
                for val in vals:
                    val['modified'] = timestamp()
                    self.collections.setdefault(col, {})[val['id']] = json.dumps(val)
                self.ts_col(col)
                status = httplib.OK
        finally:
            return HttpResponse(status)

    def _handle_DELETE(self, path, environ):
        assert path.startswith('/0.5/') or path.startswith('/1.0/')
        response = HttpResponse(httplib.OK)
        if path.endswith('/storage/0'):
            self.collections.clear()
        elif path.startswith('/0.5/') or path.startswith('/1.0/'):
            command, args = self.parse_url(path)
            col, key = args.split('/', 1)
            if not key:
                opts = urlparse.parse_qs(environ['QUERY_STRING'])
                test = self.opts_test(opts)
                col = self.collections.setdefault(col, {})
                for key in col.keys():
                    if test(json.loads(col[key]).get('modified', 0)):
                        logging.info('DELETE %s key %s' % (path, key))
                        del col[key]
            else:
                try:
                    del self.collections[col][key]
                except KeyError:
                    return HttpResponse(httplib.NOT_FOUND)
        return response

    def _handle_GET(self, path, environ):
        if path.startswith('/0.5/') or path.startswith('/1.0/'):
            command, args = self.parse_url(path)
            return self.handle_storage(command, args, path, environ)
        elif path.startswith('/1/'):
            return HttpResponse(httplib.OK, self.url_base())
        elif path.startswith('/state'):
            return HttpResponse(httplib.OK, pprint.pformat(self.collections))
        else:
            return HttpResponse(httplib.NOT_FOUND)

    def handle_storage(self, command, args, path, environ):
        if command == 'info':
            if args == 'collections':
                return JsonResponse(json.dumps(self.collections.get('timestamps', {})))
        if command == 'storage':
            if '/' in args:
                col, key = args.split('/')
            else:
                col, key = args, None
            try:
                if not key: # list output requested
                    opts = urlparse.parse_qs(environ['QUERY_STRING'])
                    test = self.opts_test(opts)
                    result = []
                    for val in self.collections.setdefault(col, {}).itervalues():
                        val = json.loads(val)
                        if test(val.get('modified', 0)):
                            result.append(val)
                    result = sorted(result,
                                                    key=lambda val: (val.get('sortindex'),
                                                                                     val.get('modified')),
                                                    reverse=True)
                    if 'limit' in opts:
                        result = result[:int(opts['limit'][0])]
                    logging.info('result set len = %d' % len(result))
                    if 'application/newlines' in environ.get('HTTP_ACCEPT', ''):
                        value = '\n'.join(json.dumps(val) for val in result)
                        return HttpResponse(httplib.OK, value,
                                                                content_type='application/text')
                    else:
                        return JsonResponse(json.dumps(result))
                else:
                    return JsonResponse(self.collections.setdefault(col, {})[key])
            except KeyError:
                if not key: raise
                return HttpResponse(httplib.NOT_FOUND, '"record not found"',
                                                        content_type='application/json')

    def __process_handler(self, handler):
        path = self.request.environ['PATH_INFO']
        response = handler(path, self.request.environ)
        return response

    def __call__(self, environ, start_response):
        """Main WSGI application method"""

        self.request = HttpRequest(environ)
        method = '_handle_%s' % environ['REQUEST_METHOD']

        # See if we have a method called 'handle_METHOD', where
        # METHOD is the name of the HTTP method to call.    If we do,
        # then call it.
        if hasattr(self, method):
            handler = getattr(self, method)
            response = self.__process_handler(handler)
        else:
            response = HttpResponse(httplib.METHOD_NOT_ALLOWED,
                                                            'Method %s is not yet implemented.' % method)

        start_response(response.status, response.headers)
        return [response.content]

class NoLogging(wsgiref.simple_server.WSGIRequestHandler):
    def log_request(self, *args):
        pass

if __name__ == '__main__':
    socket.setdefaulttimeout(300)
#    if '-v' in sys.argv:
    logging.basicConfig(level=logging.DEBUG)
    handler_class = wsgiref.simple_server.WSGIRequestHandler
#    else:
#        logging.basicConfig(level=logging.ERROR)
#        handler_class = NoLogging
    logging.info('Serving on %s:%d.' % (URL_BASE, DEFAULT_PORT))
    app = WeaveApp()
    httpd = wsgiref.simple_server.make_server(BIND_IP, DEFAULT_PORT, app, handler_class=handler_class)
    httpd.serve_forever()
