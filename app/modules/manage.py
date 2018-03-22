# -*- coding:utf8 -*-


import qrcode
import base
import math
import json
import Image, ImageDraw, ImageFont, ImageFilter
from StringIO import StringIO
import time
from datetime import date, datetime
import decimal
import tornado.web
from werkzeug.security import generate_password_hash, check_password_hash

_MAPPING = (u'零', u'壹', u'贰', u'叁', u'肆', u'伍', u'陆', u'柒', u'捌', u'玖',)
Z_list = [u'零', u'壹', u'贰', u'叁', u'肆', u'伍', u'陆', u'柒', u'捌', u'玖']
_P0 = (u'', u'拾', u'', u'',)
_S4, _S8, _S16 = 10 ** 4, 10 ** 8, 10 ** 16
_MIN, _MAX = 0, 9999999999999999


def _to_chinese4(num, year=False):
    '''转换[0, 10000)之间的阿拉伯数字
    '''
    assert (0 <= num and num < _S4)
    if num < 10:
        return _MAPPING[num]
    else:
        lst = []
        while num >= 10:
            lst.append(num % 10)
            num = num / 10
        lst.append(num)
        c = len(lst)  # 位数
        result = u''

        for idx, val in enumerate(lst):
            if val != 0:
                result += _P0[idx] + _MAPPING[val]
                if idx < c - 1 and lst[idx + 1] == 0:
                    result += u''
        if year == 1:
            return result[::-1].replace(u'拾', u'')
        else:
            return result[::-1].replace(u'壹拾', u'拾')


def _ZWYear(year):
    ret = ''
    ret += _to_chinese4(int(year[:2]), 0)

    for i in str(year[2:]):
        ret += Z_list[int(i)]

    return ret


class ManageBaseHandler(base.BaseHandler):
    def get_current_user(self):
        return self.get_secure_cookie("username")

    def _hash_password(self, password):
        return generate_password_hash(password)


class MIndex(ManageBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('admin/index.html', user=self.current_user)


class LoginHandler(ManageBaseHandler):
    def get(self):
        self.render('admin/login.html')

    def post(self):
        username = self.get_argument("username")
        password = self.get_argument("password")

        user = self.application.db.get('select * from users where username=%s', username)
        if user and check_password_hash(user['password_hash'], password):
            self.set_secure_cookie("username", self.get_argument("username"))
            self.redirect("/manage/index")
        else:
            self.redirect("/manage/login")


class LogoutHandler(ManageBaseHandler):
    def get(self):
        self.clear_cookie("username")
        self.redirect("/manage/login")


class ChangePasswordHandler(ManageBaseHandler):
    @tornado.web.authenticated
    def get(self):
        self.render('admin/change_password.html', user=self.current_user)

    def post(self):
        old_password = self.get_argument("old_password")
        password = self.get_argument("password")

        user = self.application.db.get('select * from users where username=%s', self.current_user)
        if user and check_password_hash(user['password_hash'], old_password):
            ret = self.application.db.execute('update users set password_hash=%s where id=%s',
                                              generate_password_hash(password), user['id'])
            self.redirect("/manage/login")
        else:
            self.redirect("/manage/change_password")


class plant_list(ManageBaseHandler):
    @tornado.web.authenticated
    def get(self):
        pagesize = int(self.get_argument('ps', 50))
        p = int(self.get_argument('p', 1))
        start = (p - 1) * pagesize

        c = self.application.db.query('select count(0) as c from certificate where state=1')
        cts = self.application.db.query('select * from certificate where state=1 order by id desc limit %s,%s', start,
                                        pagesize)

        pagecount = int(math.ceil(c[0]['c'] / float(pagesize)))
        self.render('admin/plant_list.html', cts=cts, count=c[0]['c'], current=p, pagesize=pagesize,
                    pagecount=pagecount)


class plant_detail(ManageBaseHandler):
    @tornado.web.authenticated
    def get(self):
        id = int(self.get_argument("id", 0))
        ct = self.application.db.get('select * from certificate where state=1 and id=%s', id)
        if not ct:
            keys = ['no', 'address1', 'name1', 'id_number', 'phone_number', 'address2', 'source', 'tool',
                    'transport_address1',
                    'transport_address2', 'transport_address3', 'start_time', 'end_time', 'variety', 'opinion',
                    'sign_time', 'start_year', 'start_month', 'start_day', 'end_year', 'end_month', 'end_day',
                    'sign_year', 'sign_month', 'sign_day']
            ct = {'id': 0}
            for key in keys:
                ct[key] = ''
        else:
            start_time = str(ct['start_time'])[:10].split('-')
            end_time = str(ct['end_time'])[:10].split('-')
            sign_time = str(ct['sign_time'])[:10].split('-')

            ct['start_year'] = int(start_time[0])
            ct['start_month'] = int(start_time[1])
            ct['start_day'] = int(start_time[2])

            ct['end_year'] = int(end_time[0])
            ct['end_month'] = int(end_time[1])
            ct['end_day'] = int(end_time[2])

            ct['sign_year'] = int(sign_time[0])
            ct['sign_month'] = int(sign_time[1])
            ct['sign_day'] = int(sign_time[2])

        self.render('admin/plant_detail.html', ct=ct)

    @tornado.web.authenticated
    def post(self):

        id = int(self.get_argument('id', 0))
        no = self.get_argument('no', '')
        address1 = self.get_argument('address1', '')
        name1 = self.get_argument('name1', '')
        id_number = self.get_argument('id_number', '')
        phone_number = self.get_argument('phone_number', '')

        address2 = self.get_argument('address2', '')
        source = self.get_argument('source', '')
        tool = self.get_argument('tool', '')

        transport_address1 = self.get_argument('transport_address1', '')
        transport_address2 = self.get_argument('transport_address2', '')
        transport_address3 = self.get_argument('transport_address3', '')

        st_year = self.get_argument('st_year')
        st_month = self.get_argument('st_month')
        st_day = self.get_argument('st_day')

        et_year = self.get_argument('et_year')
        et_month = self.get_argument('et_month')
        et_day = self.get_argument('et_day')

        opinion = self.get_argument('opinion')

        sign_year = self.get_argument('sign_year')
        sign_month = self.get_argument('sign_month')
        sign_day = self.get_argument('sign_day')

        start_time = '-'.join([st_year, st_month, st_day])
        end_time = '-'.join([et_year, et_month, et_day])
        sign_time = '-'.join([sign_year, sign_month, sign_day])

        variety = self.get_argument('variety')

        ct = self.application.db.get('select * from certificate where id=%s', id)

        params = [no, address1, name1, id_number, phone_number, address2, source, tool, transport_address1,
                  transport_address2, transport_address3, start_time, end_time, variety, opinion, sign_time]
        if ct:
            sql = '''update certificate set `no`=%s,address1=%s,name1=%s,id_number=%s,phone_number=%s,address2=%s,source=%s,
                      tool=%s,transport_address1=%s,transport_address2=%s,transport_address3=%s,start_time=%s,end_time=%s,
                      variety=%s,opinion=%s,sign_time=%s where id=%s'''
            params.append(id)
        else:
            sql = '''insert into certificate(`no`, address1, name1, id_number, phone_number, address2, source, tool, transport_address1,
                  transport_address2, transport_address3, start_time, end_time, variety, opinion, sign_time) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)'''

        ret = self.application.db.execute(sql, *params)
        self.redirect('/manage/plant_list')


def logo_watermark(img, water_img):
    '''''
    添加一个图片水印,原理就是合并图层，用png比较好
    '''
    baseim = img
    bw, bh = baseim.size
    lw, lh = water_img.size
    water_img = water_img.resize((80, 80))
    baseim.paste(water_img, (570, 20))
    return baseim


class plant_preview(ManageBaseHandler):
    def get(self):
        id = int(self.get_argument("id", 0))
        ct = self.application.db.get('select * from certificate where state=1 and id=%s', id)

        start_time = str(ct['start_time'])[:10].split('-')
        end_time = str(ct['end_time'])[:10].split('-')
        sign_time = str(ct['sign_time'])[:10].split('-')

        data = u'暂无数据'
        if ct:
            image = Image.open('static/jy.jpg')

            font = ImageFont.truetype('static/simsun.ttf', 12)
            color = '#0000CD'
            draw = ImageDraw.Draw(image)
            draw.text((440, 158), u'冀', font=font, fill=color)
            draw.text((500, 158), 'No.'+ct['no'], font=font, fill=color)

            draw.text((180, 185), ct['address1'], font=font, fill=color)
            draw.text((180, 213), ct['name1'], font=font, fill=color)
            draw.text((348, 213), ct['id_number'][:6]+ len(ct['id_number'][6:-4])*'*'+ct['id_number'][-4:], font=font, fill=color)
            draw.text((535, 213), ct['phone_number'], font=font, fill=color)

            draw.text((180, 240), ct['address2'], font=font, fill=color)
            draw.text((180, 265), ct['source'], font=font, fill=color)
            draw.text((535, 265), ct['tool'], font=font, fill=color)

            draw.text((145, 293), ct['transport_address1'], font=font, fill=color)
            draw.text((335, 293), ct['transport_address2'], font=font, fill=color)
            draw.text((445, 293), ct['transport_address3'], font=font, fill=color)

            draw.text((145, 320), _ZWYear(str(int(start_time[0]))), font=font, fill=color)
            draw.text((245, 320), _to_chinese4(int(start_time[1])), font=font, fill=color)
            draw.text((310, 320), _to_chinese4(int(start_time[2])), font=font, fill=color)
            draw.text((390, 320), _ZWYear(str(int(end_time[0]))), font=font, fill=color)
            draw.text((490, 320), _to_chinese4(int(end_time[1])), font=font, fill=color)
            draw.text((550, 320), _to_chinese4(int(end_time[2])), font=font, fill=color)

            if ct['variety']:
                for i, v in enumerate(json.loads(ct['variety'])):
                    draw.text((60, 375 + i * 27), v['key1'], font=font, fill=color)
                    draw.text((200, 375 + i * 27), v['key2'], font=font, fill=color)
                    draw.text((350, 375 + i * 27), v['key3'], font=font, fill=color)
                    draw.text((410, 375 + i * 27), v['key4'], font=font, fill=color)
                    draw.text((480, 375 + i * 27), v['key5'], font=font, fill=color)
                    draw.text((550, 375 + i * 27), v['key6'], font=font, fill=color)

            draw.text((420, 655), ct['opinion'], font=font, fill=color)

            draw.text((450, 847), str(int(sign_time[0])), font=font, fill=color)
            draw.text((510, 847), str(int(sign_time[1])), font=font, fill=color)
            draw.text((550, 847), str(int(sign_time[2])), font=font, fill=color)

            qr = qrcode.make("http://www.liagou.top:8009/manage/plant_preview?id=" + str(id))
            img = logo_watermark(image, qr)
            stream = StringIO()
            img.save(stream, 'JPEG')
            data = stream.getvalue()
            self.set_header("Content-Type", "image/JPEG")
            self.set_header("Content-Length", len(data))
        self.write(data)


class plant_print(ManageBaseHandler):
    def get(self):
        id = int(self.get_argument("id", 0))
        ct = self.application.db.get('select * from certificate where state=1 and id=%s', id)

        start_time = str(ct['start_time'])[:10].split('-')
        end_time = str(ct['end_time'])[:10].split('-')
        sign_time = str(ct['sign_time'])[:10].split('-')

        data = u'暂无数据'
        if ct:
            image = Image.new('RGB', (676, 1012), (255, 255, 255, 0))

            font = ImageFont.truetype('static/simsun.ttf', 14)
            color = '#0000CD'
            draw = ImageDraw.Draw(image)
            draw.text((450, 158), u'冀', font=font, fill=color)
            #draw.text((500, 158), 'No.'+ct['no'], font=font, fill=color)

            draw.text((180, 185), ct['address1'], font=font, fill=color)
            draw.text((180, 213), ct['name1'], font=font, fill=color)
            draw.text((348, 213), ct['id_number'][:6]+ len(ct['id_number'][6:-4])*'*'+ct['id_number'][-4:], font=font, fill=color)
            draw.text((540, 213), ct['phone_number'], font=font, fill=color)

            draw.text((180, 240), ct['address2'], font=font, fill=color)
            draw.text((180, 265), ct['source'], font=font, fill=color)
            draw.text((540, 265), ct['tool'], font=font, fill=color)

            draw.text((145, 293), ct['transport_address1'], font=font, fill=color)
            draw.text((335, 293), ct['transport_address2'], font=font, fill=color)
            draw.text((445, 293), ct['transport_address3'], font=font, fill=color)

            draw.text((145, 320), _ZWYear(str(int(start_time[0]))), font=font, fill=color)
            draw.text((245, 320), _to_chinese4(int(start_time[1])), font=font, fill=color)
            draw.text((310, 320), _to_chinese4(int(start_time[2])), font=font, fill=color)
            draw.text((390, 320), _ZWYear(str(int(end_time[0]))), font=font, fill=color)
            draw.text((490, 320), _to_chinese4(int(end_time[1])), font=font, fill=color)
            draw.text((550, 320), _to_chinese4(int(end_time[2])), font=font, fill=color)

            if ct['variety']:
                for i, v in enumerate(json.loads(ct['variety'])):
                    draw.text((60, 375 + i * 27), v['key1'], font=font, fill=color)
                    draw.text((200, 375 + i * 27), v['key2'], font=font, fill=color)
                    draw.text((350, 375 + i * 27), v['key3'], font=font, fill=color)
                    draw.text((410, 375 + i * 27), v['key4'], font=font, fill=color)
                    draw.text((480, 375 + i * 27), v['key5'], font=font, fill=color)
                    draw.text((550, 375 + i * 27), v['key6'], font=font, fill=color)

            draw.text((420, 655), ct['opinion'], font=font, fill=color)

            draw.text((450, 847), str(int(sign_time[0])), font=font, fill=color)
            draw.text((520, 847), str(int(sign_time[1])), font=font, fill=color)
            draw.text((565, 847), str(int(sign_time[2])), font=font, fill=color)

            qr = qrcode.make("http://www.liagou.top:8009/manage/plant_preview?id=" + str(id))
            img = logo_watermark(image, qr)
            stream = StringIO()
            img.save(stream, 'JPEG')
            data = stream.getvalue()
            self.set_header("Content-Type", "image/JPEG")
            self.set_header("Content-Length", len(data))
        self.write(data)


class plant_qr(ManageBaseHandler):
    def get(self):
        id = self.get_argument('id')
        image = qrcode.make("http://www.liagou.top:8009/manage/plant_preview?id=" + id)
        stream = StringIO()
        image.save(stream, 'PNG')
        data = stream.getvalue()
        self.set_header("Content-Type", "image/PNG")
        self.set_header("Content-Length", len(data))
        self.write(data)


class plant_state(ManageBaseHandler):
    @tornado.web.authenticated
    def get(self):
        id = self.get_argument('id')
        state = self.get_argument('state')
        ret = self.application.db.execute('update certificate set state=%s where id=%s', state, id)
        self.redirect('/manage/plant_list')


class CJsonEncoder:
    @classmethod
    def default(ss, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            raise TypeError('%r is not JSON serializable' % obj)

    @classmethod
    def timestamp(ss, obj):
        if isinstance(obj, datetime):
            return time.mktime(obj.timetuple())
        elif isinstance(obj, date):
            return obj.strftime('%Y-%m-%d')
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            raise TypeError('%r is not JSON serializable' % obj)
