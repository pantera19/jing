# -*- coding:utf8 -*-:
import tornado.web
import tornado.httpserver
import tornado.ioloop
import tornado.options
import torndb
import os.path
from ConfigParser import ConfigParser

from tornado.options import define, options

from app.modules.manage import MIndex, LogoutHandler, LoginHandler, ChangePasswordHandler

from app.modules.manage import plant_list, plant_detail, plant_preview, plant_qr, plant_print, plant_state

define("port", default=8000, help="run on the given port", type=int)
define("dev", type=bool, help="dev mode switch", default=True)
define("config", default="", help="config file", type=str)


class Application(tornado.web.Application):
    def __init__(self):
        handlers = [
            (r"/manage/index", MIndex, None, 'manage_index'),

            (r"/manage/change_password", ChangePasswordHandler, None, 'manage_change_password'),
            (r"/manage/login", LoginHandler, None, 'manage_login'),
            (r"/manage/logout", LogoutHandler, None, 'manage_logout'),

            (r"/manage/plant_list", plant_list, None, 'plant_list'),
            (r"/manage/plant_detail", plant_detail, None, 'plant_detail'),
            (r"/manage/plant_preview", plant_preview, None, 'plant_preview'),
            (r"/manage/plant_print", plant_print, None, 'plant_print'),
            (r"/manage/plant_qr", plant_qr, None, 'plant_qr'),
            (r"/manage/plant_state", plant_state, None, 'plant_state'),

        ]

        self.CP = ConfigParser()
        self.CP.read(options.config)
        print
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), "templates"),
            static_path=os.path.join(os.path.dirname(__file__), "static"),
            debug=options.dev,
            cookie_secret="\xa1yn$\x1e\x12\x83\xc7\x0e\xf9u\xba\xddN\xb6k\xbf\xc1\xa0\xa2a\x99\xabJ",
            login_url="/manage/login"
        )

        self.db = torndb.Connection(host=self.CP.get('mysql', 'host') + ':' + self.CP.get('mysql', 'port'),
                                    database=self.CP.get('mysql', 'database'),
                                    user=self.CP.get('mysql', 'user'),
                                    password=self.CP.get('mysql', 'passwd'),
                                    time_zone="+8:00",
                                    )

        tornado.web.Application.__init__(self, handlers, **settings)


if __name__ == "__main__":
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application())
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.instance().start()
