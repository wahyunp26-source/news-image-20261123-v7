"""Build-time tool: rasterize Natural Earth 110m land polygons into a compact
dot-grid bitmask (worldmap.txt) for the entry's world map. Build-time only;
the entry itself is stdlib-only and only decodes worldmap.txt."""
import json, base64
from PIL import Image, ImageDraw

GW, GH = 136, 69
LAT_TOP, LAT_BOT = 83.0, -60.0


def proj(lon, lat):
    x = (lon + 180.0) / 360.0 * GW
    y = (LAT_TOP - lat) / (LAT_TOP - LAT_BOT) * GH
    return (x, y)


def main():
    data = json.load(open('/tmp/ne_110m_land.geojson'))
    img = Image.new('L', (GW, GH), 0)
    d = ImageDraw.Draw(img)
    for feat in data['features']:
        geom = feat['geometry']
        polys = []
        if geom['type'] == 'Polygon':
            polys = [geom['coordinates']]
        elif geom['type'] == 'MultiPolygon':
            polys = geom['coordinates']
        for poly in polys:
            for ring in poly:
                pts = [proj(lon, lat) for lon, lat in ring]
                # split rings that jump across the antimeridian
                runs, cur = [], [pts[0]]
                for a, b in zip(pts, pts[1:]):
                    if abs(b[0] - a[0]) > GW / 2:
                        runs.append(cur)
                        cur = [b]
                    else:
                        cur.append(b)
                runs.append(cur)
                for run in runs:
                    if len(run) >= 3:
                        d.polygon(run, fill=255)
    px = img.load()
    out = bytearray()
    cur = 0
    bit = 0
    land = 0
    for y in range(GH):
        for x in range(GW):
            if px[x, y] > 0:
                cur |= (1 << (7 - bit))
                land += 1
            bit += 1
            if bit == 8:
                out.append(cur)
                cur = 0
                bit = 0
    if bit:
        out.append(cur)
    open('worldmap.txt', 'w').write(base64.b64encode(bytes(out)).decode())
    print('land cells:', land, 'of', GW * GH, '| worldmap.txt bytes:',
          len(base64.b64encode(bytes(out))))
    prev = Image.new('RGB', (GW * 4, GH * 4), (250, 244, 230))
    pd = ImageDraw.Draw(prev)
    for y in range(GH):
        for x in range(GW):
            if px[x, y] > 0:
                pd.ellipse([x * 4, y * 4, x * 4 + 3, y * 4 + 3],
                           fill=(70, 90, 120))
    prev.save('/tmp/map-preview.png')
    print('preview saved /tmp/map-preview.png')


if __name__ == '__main__':
    main()
