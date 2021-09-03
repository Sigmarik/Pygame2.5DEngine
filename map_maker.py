import pygame
from math import *
pygame.init()

font = pygame.font.SysFont('arial', 13)

class v2d:
    def __init__(self, x = 0, y = 0):
        try:
            self.x, self.y = x
            return
        except TypeError:
            pass
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
    def round(self):
        return [round(self.x), round(self.y)]
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
        return sign(self.get(seg.a)) * sign(self.get(seg.b)) <= 0
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
    def dist(self, point):
        proj = point.proj(self.line())
        if self & proj:
            return dist(proj, point)
        return min(dist(self.a, point), dist(self.b, point))
    def len(self):
        return dist(self.a, self.b)
    def __len__(self):
        return self.len()

def sdist(seg1, seg2):
    if seg1 & seg2 != None:
        return 0
    return min([seg1.dist(seg2.a),
               seg1.dist(seg2.b),
               seg2.dist(seg1.a),
               seg2.dist(seg1.b)])

SCRX = 600
SCRY = 600
cam_pos = v2d()
scr = pygame.display.set_mode([SCRX, SCRY])
arr = []
materials = []
selected_material = 'concrete'
side = 600
grid = 100
grids = [5, 10, 25, 50, 100, 250, 500, 1000]
player_radius = 20
kg = True
pygame.mouse.set_visible(False)
adding_point = None
rounding = True

while kg:
    mpos = pygame.mouse.get_pos()
    mouse_point = v2d(mpos) * (side / SCRX)
    rounded_point = v2d((mouse_point / grid).round()) * grid
    minn = 0
    for i in range(len(arr)):
        if arr[minn].dist(mouse_point) > arr[i].dist(mouse_point):
            minn = i
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            kg = False
        if event.type == pygame.KEYDOWN:
            #print(event.key)
            if event.key == 61:
                #print('Pressed')
                side += 100
            if event.key == pygame.K_MINUS:
                if side > 100:
                    side -= 100
            if event.key == pygame.K_KP_PLUS:
                grid = grids[(grids.index(grid) + 1) % len(grids)]
            if event.key == pygame.K_KP_MINUS:
                grid = grids[(grids.index(grid) - 1) % len(grids)]
            if event.key == pygame.K_r:
                rounding = not rounding
            if event.key == pygame.K_e:
                file = open('maps/' + input('Map name -> ') + '.txt', 'w')
                for i in range(len(arr)):
                    print(*arr[i].a.i(), *arr[i].b.i(), materials[i], file=file)
                file.close()
            if event.key == pygame.K_l:
                lines = open('maps/' + input('Map name -> ') + '.txt', 'r').read().split('\n')
                for ln in lines:
                    if '/' in ln:
                        ln = ln[:ln.find('/')]
                    if ln == '': continue
                    pts = ln.split()
                    print(pts[4])
                    arr.append(segment(v2d(float(pts[0]), float(pts[1])), v2d(float(pts[2]), float(pts[3]))))
                    materials.append(pts[4])
            if event.key == pygame.K_m:
                mat = input('Material name -> ')
                mat_exe = 'assets/' + mat + ('' if '.' in mat else '.png')
                try:
                    mt = pygame.image.load(mat_exe)
                    selected_material = mat
                except FileNotFoundError:
                    print('Error loading material')
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                adding_point = rounded_point if rounding else mouse_point
            if event.button == 3:
                if len(arr) == 0: continue
                arr.pop(minn)
                materials.pop(minn)
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                p_a = rounded_point if rounding else mouse_point
                p_b = adding_point
                for i in list(range(len(arr)))[::-1]:
                    if ((dist(arr[i].a, p_a) < 1 and dist(arr[i].b, p_b) < 1) or
                        (dist(arr[i].a, p_b) < 1 and dist(arr[i].b, p_a) < 1)):
                        arr.pop(i)
                arr.append(segment(p_a, p_b))
                materials.append(selected_material)
                adding_point = None
                    
    scr.fill([0] * 3)
    scaling_multiplyer = SCRX / side
    for i in range(0, side, grid):
        col = [50] * 3
        pygame.draw.line(scr, col, [int(i * scaling_multiplyer), 0], [int(i * scaling_multiplyer), SCRY])
        pygame.draw.line(scr, col, [0, int(i * scaling_multiplyer)], [SCRX, int(i * scaling_multiplyer)])
    for i, seg in enumerate(arr):
        pygame.draw.line(scr, [255] * 3, (seg.a * scaling_multiplyer).i(), (seg.b * scaling_multiplyer).i(),
                         4 if (seg.a.x == seg.b.x == 0 or seg.a.y == seg.b.y == 0) else 2)
        if i == minn:scr.blit(font.render(materials[i], True, [200] * 3), ((seg.a + seg.b) * scaling_multiplyer / 2).i())
    if adding_point != None:
        pygame.draw.line(scr, [255] * 3, (adding_point * scaling_multiplyer).i(),
                         ((rounded_point if rounding else mouse_point) * scaling_multiplyer).i())
    if rounding:pygame.draw.circle(scr, [255, 0, 0], (rounded_point * scaling_multiplyer).i(), 2)
    pygame.draw.circle(scr, [10, 170, 10], mpos, int(player_radius * scaling_multiplyer), 1)
    pygame.draw.circle(scr, [10, 170, 10], mpos, 2)
    pygame.display.update()
pygame.quit()
