#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Planche des couleurs de filament disponibles - FORGEON, 15/08/2026."""
import random, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

B = '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'
N = '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'
f_titre = ImageFont.truetype(B, 58); f_stitre = ImageFont.truetype(N, 25)
f_fam = ImageFont.truetype(B, 34);   f_fam2 = ImageFont.truetype(N, 21)
f_nom = ImageFont.truetype(N, 18);   f_pt = ImageFont.truetype(N, 17)
FOND, ENCRE, GRIS = '#f4f0e6', '#26241e', '#8a8477'

NOTRE = [('bois clair','#d8c49a'),('brun chocolat','#4a3826'),('noir mat','#24242a'),('blanc crème','#f2ede2')]
BASIC = [('Noir','#000000'),('Blanc jade','#ffffff'),('Rouge','#C12E1F'),('Écarlate','#DE4343'),
 ('Orange','#FF6A13'),('Jaune tournesol','#FEC600'),('Vert vif','#BECF00'),('Vert','#00AE42'),
 ('Turquoise','#00B1B7'),('Cyan','#0086D6'),('Bleu','#0A2989'),('Violet','#5E43B7'),
 ('Magenta','#EC008C'),('Rose vif','#F5547C'),('Or','#E4BD68'),('Argent','#A6A9AA'),
 ('Gris','#8E9089'),('Marron','#9D432C')]
MAT = [('Blanc os','#CBC6B8'),('Sable','#E8DBB7'),('Brun latte','#D3B7A7'),('Caramel','#AE835B'),
 ('Brun foncé','#7D6556'),('Terracotta','#B15533'),('Rouge sombre','#BB3D43'),('Prune','#950051'),
 ('Rose sakura','#E8AFCF'),('Lilas','#AE96D4'),('Bleu glacier','#A3D8E1'),('Bleu ciel','#56B7E6'),
 ('Bleu marine','#0078BF'),('Vert prairie','#61C680'),('Vert foncé','#68724D'),
 ('Jaune citron','#F7D959'),('Gris cendre','#9B9EA0'),('Charbon','#2b2b2b')]
SILK = [('Or','#D4AF37'),('Argent','#C0C0C0'),('Or rose','#B76E79'),('Champagne','#E6D3A3'),
 ('Rouge','#C1272D'),('Bleu','#1F6FB2'),('Bleu bébé','#7BC5D6'),('Vert','#2E8B57'),
 ('Violet','#7D5BA6'),('Gris titane','#5A5A5A')]
EFFETS = [('Paillettes onyx','#1a1a1a','s'),('Paillettes ardoise','#6b6f72','s'),
 ('Paillettes vert alpin','#2f5d43','s'),('Paillettes or','#b08d3f','s'),
 ('Paillettes pourpre','#8c2733','s'),('Galaxy nébuleuse','#4b3a6b','s'),
 ('Bois chêne blanc','#c9b18a','w'),('Bois noyer noir','#5b4436','w'),
 ('Bois palissandre','#8d5a3b','w'),('Marbre blanc','#e9e6df','m'),
 ('Granit rouge','#9c6b5e','m'),('Phosphorescent','#b9f6c0','g')]

CW, CH, GAP, COLS = 172, 132, 14, 8

def pastille(coul, effet=None):
    w, h = CW, CH - 34
    im = Image.new('RGB', (w, h), coul); d = ImageDraw.Draw(im, 'RGBA')
    if effet == 'k':
        for x in range(w):
            a = int(46 * max(0.0, 1 - abs(x - w*0.30)/(w*0.42)))
            d.line([(x,0),(x,h)], fill=(255,255,255,a))
    elif effet == 'silk':
        for x in range(w):
            t = x/w
            d.line([(x,0),(x,h)], fill=(255,255,255,int(120*max(0,1-abs(t-0.22)/0.26))))
            d.line([(x,0),(x,h)], fill=(0,0,0,int(110*max(0,1-abs(t-0.72)/0.30))))
            d.line([(x,0),(x,h)], fill=(255,255,255,int(90*max(0,1-abs(t-0.95)/0.12))))
    elif effet == 's':
        rnd = random.Random(abs(hash(coul)) & 0xffff)
        for _ in range(190):
            x, y = rnd.randrange(w), rnd.randrange(h); r = rnd.choice([1,1,1,2])
            c = rnd.choice([(255,255,255,215),(255,244,200,200),(200,225,255,190)])
            d.ellipse([x-r,y-r,x+r,y+r], fill=c)
    elif effet == 'w':
        rnd = random.Random(abs(hash(coul)) & 0xffff); y = 0
        while y < h:
            d.line([(0,y),(w,y+rnd.randrange(-3,4))], fill=(60,40,25,rnd.randrange(28,74)),
                   width=rnd.choice([1,1,2]))
            y += rnd.randrange(5,11)
    elif effet == 'm':
        rnd = random.Random(abs(hash(coul)) & 0xffff)
        for _ in range(9):
            pts, x, y = [], -6, rnd.randrange(h)
            while x < w+6:
                pts.append((x,y)); x += 13; y += rnd.randrange(-9,10)
            d.line(pts, fill=(90,80,75,rnd.randrange(45,105)), width=rnd.choice([1,2]))
        im = im.filter(ImageFilter.SMOOTH)
    elif effet == 'g':
        lu = Image.new('RGB',(w,h),coul); d2 = ImageDraw.Draw(lu,'RGBA')
        d2.ellipse([w*0.12,h*0.10,w*0.88,h*0.92], fill=(210,255,215,130))
        im = Image.blend(im, lu.filter(ImageFilter.GaussianBlur(14)), 0.75)
    ImageDraw.Draw(im).rectangle([0,0,w-1,h-1], outline='#00000026')
    return im

def bloc(pl, dr, x0, y0, titre, sous, items, defaut=None):
    dr.text((x0,y0), titre, font=f_fam, fill=ENCRE)
    dr.text((x0,y0+40), sous, font=f_fam2, fill=GRIS)
    y = y0 + 76
    for i, it in enumerate(items):
        nom, coul = it[0], it[1]
        eff = it[2] if len(it) > 2 else defaut
        cx = x0 + (i % COLS)*(CW+GAP); cy = y + (i//COLS)*(CH+GAP+12)
        pl.paste(pastille(coul, eff), (cx, cy))
        dr.text((cx+3, cy+CH-30), nom, font=f_nom, fill=ENCRE)
    return y + ((len(items)+COLS-1)//COLS)*(CH+GAP+12) + 26

M = 40
W = M*2 + COLS*CW + (COLS-1)*GAP
pl = Image.new('RGB', (W, 2600), FOND); dr = ImageDraw.Draw(pl)
dr.text((M,34), 'Les couleurs possibles', font=f_titre, fill=ENCRE)
dr.text((M,104), "FORGEON · nuancier PLA · la machine tient 4 bobines à la fois, "
                 "mais on change entre deux impressions", font=f_stitre, fill=GRIS)
y = 168
y = bloc(pl, dr, M, y, 'Nos 4 couleurs actuelles',
         "notre choix « bois et naturel » — rien ne t'oblige à le garder", NOTRE, 'k')
dr.line([(M,y-12),(W-M,y-12)], fill='#00000022', width=2)
y = bloc(pl, dr, M, y, 'PLA Basic', 'brillant léger · le moins cher · plus de 30 teintes', BASIC, 'k')
y = bloc(pl, dr, M, y, 'PLA Mat',
         "aucun reflet, toucher velours · C'EST CELUI QUI PHOTOGRAPHIE LE MIEUX", MAT, None)
y = bloc(pl, dr, M, y, 'PLA Silk',
         'effet métal poli · superbe sur un petit objet, mais accentue les lignes', SILK, 'silk')
y = bloc(pl, dr, M, y, 'Effets spéciaux',
         '⚠ abrasifs : demandent une buse en acier trempé (20-30 €)', EFFETS)
dr.line([(M,y-10),(W-M,y-10)], fill='#00000022', width=2)
pied = [
 "Pour tes objets :  plaques → MAT (effet fait main)   ·   lampe photo et boule → BLANC MAT obligatoire",
 "médaillon et porte-clés → SILK or ou argent (ça imite le bijou)   ·   urne et cadre → MARBRE ou BOIS",
 "",
 "Prix : bobines Bambu 20 à 25 € le kilo · autres marques 15 à 20 € · la machine accepte toutes les bobines.",
 "Les teintes ci-dessus sont indicatives : un écran ne rend jamais la vraie couleur d'une bobine.",
]
for i, t in enumerate(pied):
    dr.text((M, y+8+i*30), t, font=f_pt, fill=ENCRE if i < 2 else GRIS)
pl = pl.crop((0,0,W, y+8+len(pied)*30+26))
out = '/sessions/stoic-trusting-rubin/mnt/outputs/FORGEON_planche_couleurs.jpg'
pl.save(out, 'JPEG', quality=90)
print('OK', pl.size, os.path.getsize(out)//1024, 'Ko')
