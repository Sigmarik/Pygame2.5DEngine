import pygame
import time
from math import *
import os
import socket
import threading
from pygame.locals import *

PI = 3.1415926535
SCR_DIST = 100
DEBUG = False
IMAGE_STACK = {}

def get_time():
    return time.time()

class ProtocolError(Exception):
    def __init__(self):
        super().__init__('Protocol error')

def send(num, sock, big = True):
    if isinstance(num, bool): num = 'T' if num else 'F'
    if DEBUG: sock.send(b'nm')
    if big:
        final = str(num)
        prefin = str(len(final))
        prepre = str(len(prefin))
        sock.send(prepre.encode())
        sock.send(prefin.encode())
        sock.send(final.encode())
        if DEBUG: print('Sent big', final)
        return
    sock.send(str(num).encode())
    if DEBUG: print('Sent small', num)

def receve(sock, big = True):
    if DEBUG and sock.recv(2) != b'nm': raise ProtocolError()
    if DEBUG: print('Waiting for', 'big' if big else 'small', 'number')
    if big:
        len1 = int(sock.recv(1).decode())
        len2 = int(sock.recv(len1).decode())
        val = sock.recv(len2).decode()
        if DEBUG: print('Receved big', val)
        return val
    val = sock.recv(1).decode()
    if DEBUG: print('Receved small', val)
    return val

class v2d:
    def __init__(self, x = 0, y = 0):
        self.x = x
        self.y = y
    def __add__(a, b):
        return v2d(a.x + b.x, a.y + b.y)
    def __mul__(a, b):
        if isinstance(b, v2d):
            return a.x * b.x + a.y * b.y
        return v2d(a.x * b, a.y * b)
    def __sub__(a, b):
        return a + (b * -1)
    def __iadd__(self, a):
        self = self + a
        return self
    def __truediv__(a, b):
        return a * (1 / b)
    def __isub__(self, a):
        self += a * -1
        return self
    def __imul__(self, a):
        self = self * a
        return self
    def __itruediv__(self, a):
        self *= 1 / a
        return self
    def __str__(self):
        return '(' + str(self.x) + ' ' + str(self.y) + ')'
    def __lt__(a, b):
        return len(a) < len(b)
    def __gt__(a, b):
        return len(a) > len(b)
    def __le__(a, b):
        return len(a) <= len(b)
    def __ge__(a, b):
        return len(a) >= len(b)
    def __and__(a, b):
        return a.x * b.y - a.y * b.x
    def len(self):
        return sqrt(self.x * self.x + self.y * self.y)
    def __len__(self):
        return self.len()
    def __hash__(self):
        return self.x + 1000000 * self.y
    def normalise(self):
        if self.len() == 0: return self
        return self / self.len()
    def clamp(self, d = 1):
        if self.len() > d:
            return self.normalise() * d
        return self
    def turn90(self):
        return v2d(self.y, -self.x)
    def arr(self):
        return [self.x, self.y]
    def i(self):
        return [int(self.x), int(self.y)]
    def proj(self, l):
        return l & line(self, self + l.n())
    def closest(self, a, b):
        if dist(self, a) < dist(self, b):
            return a
        return b
    def rot(self):
        return atan2(self.y, self.x)
    def with_rot(self, angle):
        return v2d(cos(angle) * self.len(), sin(angle) * self.len())
    def rotated(self, angle):
        return self.with_rot(angle + self.rot())
    def send(self, sock):
        if DEBUG: sock.send(b'pt')
        if DEBUG: print('Sent vector', self)
        send(self.x, sock)
        send(self.y, sock)

def angle_to_v2d(alpha):
    return v2d(cos(alpha), sin(alpha))

def receve_v2d(sock):
    if DEBUG and sock.recv(2) != b'pt': raise ProtocolError()
    if DEBUG: print('Waiting for vector')
    x = float(receve(sock))
    y = float(receve(sock))
    if DEBUG: print('Receved vector', x, y)
    return v2d(x, y)

def sign(x):
    if x == 0:
        return x
    if x > 0:
        return 1
    return -1

class line:
    def __init__(self, A, B):
        self.a, self.b = (B - A).turn90().arr()
        self.c = -(A.x * self.a + A.y * self.b)
        #print(A, B, self)
    def n(self):
        return v2d(self.a, self.b)
    def dir(self):
        return self.n().turn90()
    def __str__(self):
        return '{' + str(self.a) + ' ' + str(self.b) + ' ' + str(self.c) + '}'
    def __and__(l1, l2):
        D = l1.a * l2.b - l1.b * l2.a
        Dx = l1.c * l2.b - l1.b * l2.c
        Dy = l1.a * l2.c - l1.c * l2.a
        if D != 0:
            return v2d(-Dx / D, -Dy / D)
        return None
    def get(self, p):
        return self.a * p.x + self.b * p.y + self.c
    def check(self, seg):
        return self.get(seg.a) * self.get(seg.b) <= 0
    def mirror(self, p):
        proj = p.proj(self)
        return proj + (proj - p)
    def push(self, seg, r):
        proj = seg.b.proj(self)
        dirr = (seg.b - proj).normalise()
        point = proj + dirr * r
        #print('Started')
        while self.check(segment(seg.a, point)):
            #print('bruh')
            point = self.mirror(point)
        return segment(seg.a, point)
    def send(sock):
        if DEBUG: sock.send(b'ln')
        if DEBUG: print('Sent line', self.a, self.b, self.c)
        send(self.a, sock)
        send(self.b, sock)
        send(seld.c, sock)

def dist(a, b):
    return (b - a).len()

class segment:
    def __init__(self, p1, p2):
        self.a = p1
        self.b = p2
    def line(self):
        return line(self.a, self.b)
    def __str__(s):
        return str(s.a) + ' - ' + str(s.b)
    def __and__(s, p):
        #global scr
        if isinstance(p, v2d):
            #pygame.draw.circle(scr, [255, 0, 0], p.i(), 3)
            #print(p)
            return dist(s.a, s.b) + 0.01 > dist(s.a, p) + dist(s.b, p)
        if isinstance(p, line):
            point = p & s.line()
            if s & point:
                return point
            return None
        if s.line().check(p) and p.line().check(s):
            return s.line() & p.line()
        else:
            return None
    def dist(self, point):
        proj = point.proj(self.line())
        if self & proj:
            return dist(proj, point)
        return min(dist(self.a, point), dist(self.b, point))
    def len(self):
        return dist(self.a, self.b)
    def __len__(self):
        return self.len()
    def is_closer(self, seg, point):
        result = 0
        for targ in [self.a, self.b, seg.a, seg.b]:
            trace = segment(point, point + (targ - point) * 1000)
            hit1 = self & trace
            hit2 = seg & trace
            if hit1 != None and hit2 != None and dist(hit1, hit2) > 1:
                if dist(point, hit1) < dist(point, hit2):
                    return True
                else:
                    return False
        return True
    def send(sock):
        if DEBUG: sock.send(b'sg')
        if DEBUG: print('Sent segment', self.a, self.b)
        self.a.send(sock)
        self.b.send(sock)

def receve_segment(sock):
    if DEBUG and sock.recv(2) != b'sg': raise ProtocolError()
    if DEBUG: print('Waiting for segment')
    a = receve_v2d(sock)
    b = receve_v2d(sock)
    if DEBUG: print('Receved segment', a, b)
    return segment(a, b)

def sdist(seg1, seg2):
    if seg1 & seg2 != None:
        return 0
    return min([seg1.dist(seg2.a),
               seg1.dist(seg2.b),
               seg2.dist(seg1.a),
               seg2.dist(seg1.b)])

class game_wall(segment):
    def __init__(self, a, b, height = 100, texture = None):
        self.a = a
        self.b = b
        self.height = height
        self.texture = texture
        self.transparent = False
        if self.texture == None:
            self.texture = pygame.Surface([1, 1])
            self.texture.fill([255] * 3)
    def render(self, distance, hit, width, fog = None):
        dheight = (SCR_DIST * self.height) // distance
        duration = dist(self.a, hit) / dist(self.a, self.b)
    def __str__(s):
        return str(s.a) + ' - ' + str(s.b)

def imload(name, pos = [0, 0], target_h = -1):
    img = pygame.image.load(name)
    col = img.get_at(pos)
    img.set_colorkey(col)
    if target_h == -1: return img
    surf = pygame.Surface([img.get_width(), target_h])
    surf.fill(col)
    surf.blit(img, [0, target_h - img.get_height()])
    surf.set_colorkey(col)
    return surf

class frame_machine:
    def __init__(self, name):
        self.states = {}
        for fl in os.listdir(os.getcwd() + '/assets/' + name):
            parts = fl.split('#')
            if len(parts) == 1:
                self.states[fl[:-4]] = imload(os.getcwd() + '/assets/' + name + '/' + fl, target_h = 100)
            else:
                if parts[0] not in self.states.keys():
                    self.states[parts[0]] = {}
                self.states[parts[0]][parts[1][:-4]] = imload(os.getcwd() + '/assets/' + name + '/' + fl, target_h = 100)
        #print(self.states)

def delta_r(a):
    v = degrees(a)
    x = v % 360
    #print(x)
    if x > 180:
        return x - 360
    return x

class creature:
    def __init__(self, pos, frame_m):
        self.anim = frame_m
        self.df = delta_fram
        self.pos = pos
        self.dir = 0
    def get_wall(self, target, image):
        arrow = (target.pos - self.pos).normalise()
        n = arrow.turn90()
        a = self.pos + n * (image.get_width() // 2)
        b = self.pos - n * (image.get_width() // 2)
        cnt = 0
        while (a - target.pos) * (b - target.pos) < 0 and cnt < 2:
            a, b = b, a
            cnt += 1
        gwall = game_wall(a, b, 100, image)
        gwall.transparent = True
        return gwall
    def send(self, sock):
        if DEBUG: sock.send(b'cr')
        if DEBUG: print('Sent creature', self.pos, self.dir)
        self.pos.send(sock)
        send(self.dir, sock)

def receve_creature(sock, frm):
    if DEBUG and sock.recv(2) != b'cr': raise ProtocolError()
    if DEBUG: print('Waiting for creature')
    pos = receve_v2d(sock)
    dirr = float(receve(sock))
    cret = creture(pos, frm)
    cret.dir = dirr
    if DEBUG: print('Receved creature', pos, dirr)
    return cret

class render_circle:
    def add_mark(self, mark):
        if not -PI <= mark <= PI: raise Exception
        L, R = 0, len(self.marks)
        while R - L > 1:
            M = (R + L) // 2
            if self.marks[M] == mark:
                return
            elif self.marks[M] > mark:
                R = M
            else:
                L = M
        self.marks.insert(R, mark)
        self.walls.insert(R, self.walls[L])
    def __init__(self, walls, pos):
        self.marks = [-PI, PI]
        self.walls = [None]
        for wall in walls.values():
            self.add_mark(atan2(*(wall.a - pos).arr()[::-1]))
            self.add_mark(atan2(*(wall.b - pos).arr()[::-1]))
            for wl in walls.values():
                if wl != wall and wl & wall != None:
                    self.add_mark(atan2(*((wl & wall) - pos).arr()[::-1]))
        for i in range(len(self.marks) - 1):
            insecs = []
            trace = segment(pos, pos + angle_to_v2d((self.marks[i] + self.marks[i + 1]) / 2) * 10000)
            for ind in walls:
                #print(walls[ind])
                insec = walls[ind] & trace
                if insec != None:
                    insecs.append([dist(insec, pos), ind])
            self.walls[i] = walls[min(insecs)[1]]
        ind = 1
        while i < len(self.walls):
            if self.walls[ind] == self.walls[ind - 1]:
                self.walls.pop(ind)
                self.marks.pop(ind)
            else:
                ind += 1
        #print(self.walls)
    def get_at(self, angle):
        if not -PI <= angle <= PI: raise Exception
        L, R = 0, len(self.marks)
        while R - L > 1:
            M = (R + L) // 2
            if self.marks[M] > angle:
                R = M
            else:
                L = M
        return self.walls[L]

class player(creature):
    def __init__(self, pos, frm_m, r = 20):
        if isinstance(pos, list):
            self.pos = v2d(*pos)
        else:
            self.pos = pos
        self.framework = frm_m
        self.r = r
        self.dir = 0
        self.velocity = v2d()
        self.max_vel = 300
        self.hp = 3
        self.damage_time = -2
        self.shoot_time = -2
        self.update_time = -2
        self.knife_time = -2
        self.did_shot = False
        self.punched = False
        self.damaged = False
    def forward(self):
        return v2d(cos(self.dir), sin(self.dir))
    def right(self):
        return v2d(cos(self.dir + PI * 0.5), sin(self.dir + PI * 0.5))
    def tick(self, dt, walls, vector = None, recursion = 0):
        if self.hp <= 0: return
        if vector != None:
            trace = segment(self.pos, self.pos + vector)
        else:
            trace = segment(self.pos, self.pos + self.velocity.clamp(1).rotated(self.dir + PI / 2) * self.max_vel * dt)
        if trace.len() == 0: return
        broken = None
        hit_wall = []
        for wall in walls:
            #print(wall, trace, dt)
            if sdist(wall, trace) > self.r: continue
            L, R = 0, 1
            while R - L > 0.0001:
                M = (R + L) / 2
                trc = segment(self.pos, self.pos + self.velocity.clamp(1) * self.max_vel * dt * M)
                if M == 0 or sdist(wall, trace) < self.r + 0.001:
                    R = M
                else:
                    L = M
            if len(hit_wall) == 0 or hit_wall[0] < L:
                hit_wall = [L, wall]
            broken = wall
        if broken != None and recursion < 100:
            broken = hit_wall[1]
            prj = trace.b.proj(broken.line())
            if (not broken & trace.b.proj(broken.line())):
                #print('hard')
                corner = trace.b.closest(broken.a, broken.b)
                dirr = (trace.b - corner).normalise() * (self.r + 1)
                self.tick(dt, walls, corner + dirr - self.pos, recursion + 1)
                #self.pos = corner + dirr
                return
            trace = broken.line().push(trace, self.r + 1)
            self.tick(dt, walls, trace.b - trace.a, recursion + 1)
        else:
            self.pos = trace.b
            #print(self.pos)
    def get_model(self, other):
        state = 'idle'
        monot = get_time()
        if monot - self.shoot_time < 0.1 and self.hp > 0:
            state = 'fire'
        elif self.hp <= 0 or monot - self.damage_time < 0.3:
            if self.hp > 0:
                state = 'damage'
            else:
                state = 'death' + str(min(int((monot - self.damage_time) / 0.2), 6))
        elif self.velocity.len() != 0:
            state = 'walk' + str((int(monot / 0.13) % 4))
        img = None
        if 'death' in state:
            img = self.framework.states[state]
        else:
            deg = delta_r(self.dir - (other.pos - self.pos).rot())
            #print(deg)
            closest = 0
            for p in [45, 90, 135, 180]:
                if abs(abs(deg) - closest) > abs(abs(deg) - p):
                    closest = p
            img = self.framework.states['rot' + str(closest)][state]
            if deg > 0 and (closest not in [0, 180]):
                img = pygame.transform.flip(img, 1, 0)
        wall =  self.get_wall(other, img)
        wall.transparent = True
        return wall
    def render(self, scr, walls, players):
        circle = render_circle(walls, self.pos)
        step = 2
        player_models = []
        delta = max(0, (0.05 - abs(0.05 - get_time() + self.shoot_time)) * 20)
        #print(delta)
        for pl in players.values():
            if pl == self: continue
            player_models.append(pl.get_model(self))
        #print(player_models)
        math_time = 0
        pygame_time = 0
        call_counter = 0
        for d in range(-300, 300, step):
            dirr = v2d(300, d)
            sdist = dirr.len()
            dirr = dirr.rotated(self.dir)
            trace = segment(self.pos, self.pos + dirr * 10000)
            render_pipe = []
            #print(len(list(walls.values()) + player_models))
            for wall in [circle.get_at(atan2(*dirr.arr()[::-1]))] + player_models:
                m_tm = time.monotonic()
                hit = wall & trace
                call_counter += 1
                math_time += time.monotonic() - m_tm
                if hit != None:
                    render_pipe.append([dist(hit, self.pos), wall])
            if len(render_pipe) == 0: continue
            srt = sorted(render_pipe)
            arr = []
            for r in srt:
                arr.append(r)
                if not r[1].transparent:
                    break
            for render in arr[::-1]:
                p_tm = time.monotonic()
                wall = render[1]
                hit = wall & trace
                wall_texture = IMAGE_STACK[wall.texture] if isinstance(wall.texture, str) else wall.texture
                k = (wall_texture.get_width() * wall.height / wall_texture.get_height()) / wall.len()
                left = int((wall_texture.get_width() / k) * dist(wall.a, hit) / dist(wall.a, wall.b)) % wall_texture.get_width()
                H = int(wall.height * sdist / render[0])
                col = min(255, max(0, int(255 - 255 * render[0] / sdist)))
                #pygame.draw.line(scr, [0] * 3, [d + scr.get_width() // 2, scr.get_height() // 2 - H // 2],
                #                 [d + scr.get_width() // 2, scr.get_height() // 2 + H // 2])
                HH = scr.get_height() * render[0] / sdist
                top = max(0, int(0.5 * wall_texture.get_height() * (wall.height - HH) / wall.height))
                #pygame.transform.scale(wall.texture, [wall.texture.get_width(), H])
                prerend = pygame.transform.scale(wall_texture.subsurface(left, top, 1, wall_texture.get_height() - 2 * top), [step, min(H, scr.get_height())])
                fade = pygame.Surface([prerend.get_width(), prerend.get_height()])
                fade.set_alpha(255 - col)
                #prerend.set_alpha(col)
                render_pos = [d + scr.get_width() // 2, max(0, scr.get_height() // 2 - H // 2) + int(delta * 10), step, min(H, scr.get_height())]
                scr.blit(prerend, render_pos)
                pygame_time += time.monotonic() - p_tm
                #scr.blit(fade, render_pos)
        #print(call_counter, math_time, pygame_time)
        w_space = pygame.Surface([scr.get_width(), scr.get_height()])
        w_space.fill([255, 255, 200])
        w_space.set_alpha(int(255 * delta * 0.07))
        scr.blit(w_space, [0, 0])
    def shoot(self, gm_now, update_time = True):
        print('shoot called')
        if self.hp <= 0: return
        if update_time:
            self.shoot_time = get_time()
            self.did_shot = True
        trace = segment(self.pos, self.pos + self.forward() * 10000)
        for wall in gm_now.walls.values():
            hit = trace & wall
            if hit == None: continue
            trace = segment(self.pos, hit)
        for key in gm_now.players.keys():
            if gm_now.players[key] == self: continue
            if trace.dist(gm_now.players[key].pos) < gm_now.players[key].r and gm_now.players[key].hp > 0:
                gm_now.players[key].hp -= 1
                gm_now.players[key].damage_time = get_time()
                gm_now.players[key].damaged = True
                print('Bullet left', gm_now.players[key].hp)
    def punch(self, gm_now):
        if self.hp <= 0: return
        for key in gm_now.players.keys():
            if gm_now.players[key] == self: continue
            if dist(gm_now.players[key].pos, self.pos) <= 40 and gm_now.players[key].hp > 0:
                gm_now.players[key].hp -= 4
                gm_now.players[key].damage_time = get_time()
                gm_now.players[key].damaged = True
        self.knife_time = get_time()
        self.punched = True
    def send(self, sock, minus = {'damage' : False, 'shoot' : False, 'knife' : False}):
        if DEBUG: sock.send(b'pl')
        if DEBUG: print('Sent player', self.pos, self.dir, self.hp, self.damage_time, self.shoot_time)
        self.pos.send(sock)
        self.velocity.send(sock)
        send(self.dir, sock)
        send(self.hp, sock, big=False)
        #print(minus['shoot'])
        send(-1 if minus['damage'] else self.damage_time, sock)
        send(-1 if minus['shoot'] else self.shoot_time, sock)
        send(-1 if minus['knife'] else self.knife_time, sock)
        send(self.did_shot, sock, big=False)
        send(self.punched, sock, big=False)
        send(self.damaged, sock, big=False)
        self.did_shot = False
        self.punched = False
        self.damaged = False

def my_bool(s):
    if s == 'T':
        return True
    elif s == 'F':
        return False
    return None

def receve_player(sock, frm):
    if DEBUG and sock.recv(2) != b'pl': raise ProtocolError()
    if DEBUG: print('Waiting for player')
    pos = receve_v2d(sock)
    vel = receve_v2d(sock)
    dirr = float(receve(sock))
    hp = int(receve(sock, big=False))
    dmg_t = float(receve(sock))
    sht_t = float(receve(sock))
    knf_t = float(receve(sock))
    #print(dmg_t, sht_t, knf_t)
    if -1.5 <= dmg_t <= 0: dmg_t = get_time()
    if -1.5 <= sht_t <= 0: sht_t = get_time()
    if -1.5 <= knf_t <= 0: knf_t = get_time()
    did_shot = my_bool(receve(sock, big=False))
    punch = my_bool(receve(sock, big=False))
    damaged = my_bool(receve(sock, big=False))
    plr = player(pos, frm)
    plr.velocity = vel
    plr.dir = dirr
    plr.hp = hp
    plr.damage_time = dmg_t
    plr.shoot_time = sht_t
    plr.knife_time = knf_t
    if DEBUG: print('Receved player', pos, dirr, hp, dmg_t, sht_t)
    return plr, did_shot, punch, damaged

class game:
    def __init__(self, mode = 'single'):
        conf = open('config.txt', 'r')
        ip = conf.readline().replace('\n', '')
        port = int(conf.readline().replace('\n', ''))
        self.walls = {}
        self.players = {}
        self.mpi = 0
        self.mwi = 0
        self.mode = mode
        self.update_times = {}
        self.action_states = {}
        if mode != 'single':
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock = sock
            if mode == 'client':
                sock.connect((ip, port))
                thr = threading.Thread(target = self.as_client, args = [sock])
                thr.start()
            if mode == 'server':
                sock.bind((ip, port))
                thr = threading.Thread(target = self.as_server, args = [sock])
                thr.start()
    def load_map(self, name):
        lines = open(name, 'r').read().split('\n')
        for ln in lines:
            if '/' in ln:
                ln = ln[:ln.find('/')]
            if ln == '': continue
            pts = ln.split()
            #print(pts[4])
            key = pts[4] + ('.png' if ('.' not in pts[4]) else '')
            IMAGE_STACK[key] = pygame.image.load('assets/' + key).convert()
            self.add_wall(game_wall(v2d(float(pts[0]), float(pts[1])), v2d(float(pts[2]), float(pts[3])),
                                    100, key))
    def as_client(self, sock):
        global NET_DELTA_TIME
        self.ticked = False
        self.client_id = receve(sock)
        client_id = self.client_id
        send(get_time(), sock)
        dt = float(receve(sock)) - get_time()
        #NET_DELTA_TIME = dt
        #print(NET_DELTA_TIME)
        self.receve(sock)
        self.ticked = True
        while True:
            if DEBUG: print('Trying to send player', self.players[client_id])
            self.players[client_id].send(sock)
            self.receve(sock)
    def as_server(self, sock):
        global frm
        sock.listen(1)
        print('Server started')
        while True:
            conn, addr = sock.accept()
            print('Connected player at', addr)
            print(player(v2d(600, 600), frm))
            cl_id = self.add_player(player(v2d(600, 600), frm))
            client_thread = threading.Thread(target = self.client_work, args = [conn, cl_id])
            client_thread.start()
    def client_work(self, sock, cl_id):
        global frm
        send(cl_id, sock)
        cl_start_time = float(receve(sock))
        send(0, sock)
        start_time = get_time()
        self.send(sock)
        self.ticked = True
        upd_time = 1
        try:
            while True:
                plr, did_shot, punch, damaged = receve_player(sock, frm)
                #for k in self.action_states.keys():
                #    self.action_states[k][cl_id]['shoot'] = self.action_states[k][cl_id]['shoot'] or did_shot
                #    self.action_states[k][cl_id]['damaged'] = self.action_states[k][cl_id]['damaged'] or damaged
                #print(cl_id, did_shot, punch, damaged)
                plr.hp = self.players[cl_id].hp
                self.players[cl_id] = plr
                if did_shot:
                    self.shoot(cl_id, ignore_time=True)
                    print(cl_id, upd_time, self.players[cl_id].shoot_time)
                if punch:
                    self.knife(cl_id)
                # - start_time + cl_start_time
                #print(cl_id, get_time() - start_time + cl_start_time, plr.shoot_time)
                #print(plr.shoot_timupd_time)
                self.send(sock, upd_time)
                upd_time = get_time()
        except:
            print("Player", cl_id, 'disconnected')
            self.remove_player(cl_id)
    def add_player(self, pl):
        self.players[str(self.mpi)] = pl
        self.update_times[str(self.mpi)] = -1
        self.action_states[str(self.mpi)] = dict(zip(self.players.keys(), [{'shoot' : False, 'damage' : False} for _ in range(len(self.players))]))
        self.mpi += 1
        return str(self.mpi - 1)
    def remove_player(self, index):
        del self.players[index]
        del self.update_times[index]
        del self.action_states[index]
        #for k in self.action_states[index].keys():
        #    del self.action_states[index][k]
    def add_wall(self, seg):
        self.walls[str(self.mwi)] = seg
        self.mwi += 1
    def draw_2d(self, scr, k = 1):
        for key in self.players.keys():
            pl = self.players[key]
            pygame.draw.circle(scr, [255] * 3, (pl.pos * k).i(), int(pl.r * k))
            pygame.draw.circle(scr, [0] * 3, (pl.pos * k).i(), max(0, pl.r * k - 1))
            pygame.draw.line(scr, [255] * 3, (pl.pos * k).i(), (pl.pos * k + pl.forward() * pl.r * k).i())
        for key in self.walls.keys():
            wall = self.walls[key]
            pygame.draw.line(scr, [255] * 3, (wall.a * k).i(), (wall.b * k).i())
    def draw_3d(self, scr, player_id):
        self.players[player_id].render(scr, self.walls, self.players)
    def shoot(self, player_id, update_time = True, ignore_time = False):
        if get_time() - self.players[player_id].shoot_time < 0.2 and not ignore_time: return
        self.players[player_id].shoot(self, update_time)
        self.players[player_id].shoot_time = get_time()
    def knife(self, player_id):
        self.players[player_id].punch(self)
    def tick(self, dt):
        for pl in self.players.keys():
            self.players[pl].tick(dt, self.walls.values())
    def send(self, sock, last_update = 10 ** 18):
        if DEBUG: sock.send(b'gm')
        if DEBUG: print('Sent game')
        send(len(self.players), sock)
        for plr in list(self.players.keys()):
            send(plr, sock)
            cur_plr = self.players[plr]
            actions = {'damage' : False, 'shoot' : False, 'knife' : False}
            if cur_plr.shoot_time >= last_update:
                actions['shoot'] = True
                #print('Fired')
            if cur_plr.damage_time >= last_update:
                actions['damage'] = True
            if cur_plr.knife_time >= last_update:
                actions['knife'] = True
            cur_plr.send(sock, actions)
    def receve(self, sock):
        global frm
        if DEBUG and sock.recv(2) != b'gm': raise ProtocolError()
        if DEBUG: print('Waiting for game')
        new_plrs = {}
        n = int(receve(sock))
        shooting_players = []
        for i in range(n):
            key = receve(sock)
            plr, did_shot, punch, damaged = receve_player(sock, frm)
            if self.mode == 'client' and self.client_id == key and (key in self.players.keys()):
                new_plrs[key] = self.players[key]
                new_plrs[key].hp = plr.hp
                continue
            new_plrs[key] = plr
            if damaged:
                new_plrs[key].damage_time = get_time()
            if did_shot:
                new_plrs[key].shoot_time = get_time()
                #shooting_players.append(key)
        self.players = new_plrs.copy()
        for shooter in shooting_players:
            self.shoot(shooter, False)
        if DEBUG: print('Receved game')

# Debug part

frm = frame_machine('marine')

# ############

game_mode = input('Game mode (single, client or server)?\n-> ')
scr = pygame.display.set_mode([600, 600], DOUBLEBUF)
kg = True
gm = game(mode = game_mode)
#gm.add_wall(game_wall(v2d(100, 200), v2d(300, 300), 100, texture = pygame.image.load('assets/bricks.png')))
#gm.add_wall(game_wall(v2d(200, 100), v2d(300, 300), 100, texture = pygame.image.load('assets/bricks.png')))
gm.load_map('maps/storage.txt')
if game_mode == 'single':
    gm.add_player(player([300, 400], frm))
    gm.add_player(player([300, 320], frm))
    controlled_player = '0'
    view_player = '0'
tm = get_time()
angular_speed = 0
#gm.players[1].velocity = v2d(0.8, 0)
if game_mode != 'server':
    pygame.mouse.set_visible(False)
if game_mode == 'client':
    while not gm.ticked: pass
    controlled_player = gm.client_id
    view_player = gm.client_id
    print('Client index ->', controlled_player)
while kg:
    TM = get_time()
    delta_time = TM - tm
    tm = TM

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            kg = False
        if event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_w] and game_mode != 'server':
                #print('W pressed')
                gm.players[controlled_player].velocity += v2d(0, -1)
            if event.key in [pygame.K_s] and game_mode != 'server':
                gm.players[controlled_player].velocity += v2d(0, 1)
            if event.key in [pygame.K_a] and game_mode != 'server':
                gm.players[controlled_player].velocity += v2d(-1, 0)
            if event.key in [pygame.K_d] and game_mode != 'server':
                gm.players[controlled_player].velocity += v2d(1, 0)
            if event.key in [pygame.K_LEFT] and game_mode != 'server':
                angular_speed -= 1
            if event.key in [pygame.K_RIGHT] and game_mode != 'server':
                angular_speed -= -1
            if event.key in [pygame.K_SPACE] and game_mode != 'server':
                gm.shoot(controlled_player)
            if event.key in [pygame.K_ESCAPE]:
                kg = False
            if event.key == pygame.K_q:
                gm.knife(controlled_player)
        if event.type == pygame.KEYUP and game_mode != 'server':
            if event.key in [pygame.K_w]:
                gm.players[controlled_player].velocity -= v2d(0, -1)
            if event.key in [pygame.K_s]:
                gm.players[controlled_player].velocity -= v2d(0, 1)
            if event.key in [pygame.K_a]:
                gm.players[controlled_player].velocity -= v2d(-1, 0)
            if event.key in [pygame.K_d]:
                gm.players[controlled_player].velocity -= v2d(1, 0)
            if event.key in [pygame.K_LEFT]:
                angular_speed += 1
            if event.key in [pygame.K_RIGHT]:
                angular_speed += -1
        if event.type == pygame.MOUSEBUTTONDOWN and game_mode != 'server':
            gm.shoot(controlled_player)
    if game_mode != 'server':
        #print(gm.players[controlled_player].velocity)
        pass
    scr.fill([0] * 3)
    if game_mode != 'server':
        gm.players[controlled_player].dir += angular_speed * 3 * delta_time
        gm.players[controlled_player].dir += (pygame.mouse.get_pos()[0] - 300) / 150
        pygame.mouse.set_pos([300, 300])
        #gm.players[controlled_player].tick(delta_time, gm.walls.values())
    #gm.players[1].shoot_time = get_time()
    gm.tick(delta_time)
    if game_mode != 'server':
        gm.draw_3d(scr, view_player)
    #else:
    #    gm.draw_2d(scr, 1 if game_mode == 'server' else 0.3)
    gm.draw_2d(scr, 1 if game_mode == 'server' else 0.3)
    if game_mode != 'server':
        pygame.draw.line(scr, [255, 0, 0], [300, 295], [300, 305])
        pygame.draw.line(scr, [255, 0, 0], [295, 300], [305, 300])
    pygame.display.update()
pygame.quit()
if game_mode != 'single': gm.sock.close()
exit()
