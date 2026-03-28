import osmnx as ox
import numpy as np
import trimesh
from shapely.geometry import box


def _clip_gdf(gdf, bounds):
    minx, miny, maxx, maxy = bounds
    return gdf.cx[minx:maxx, miny:maxy]


def _wgs84_to_projected(bounds_wgs84, target_crs):
    from pyproj import Transformer

    min_lon, min_lat, max_lon, max_lat = bounds_wgs84
    transformer = Transformer.from_crs("EPSG:4326", target_crs, always_xy=True)
    x1, y1 = transformer.transform(min_lon, min_lat)
    x2, y2 = transformer.transform(max_lon, max_lat)
    return (min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2))


def _remove_holes(geom):
    if geom.geom_type == "Polygon":
        return type(geom)(geom.exterior)
    if geom.geom_type == "MultiPolygon":
        return type(geom)([type(p)(p.exterior) for p in geom.geoms])
    return geom


def _clean_polygons(gdf):
    gdf = gdf[gdf.geometry.notnull()]
    gdf = gdf[gdf.geometry.type.isin(["Polygon", "MultiPolygon"])]
    gdf = gdf.explode(index_parts=False)
    gdf["geometry"] = gdf.geometry.buffer(0)
    gdf = gdf[gdf.geometry.is_valid]
    gdf["geometry"] = gdf.geometry.simplify(1.0, preserve_topology=True)
    gdf["geometry"] = gdf.geometry.apply(_remove_holes)
    gdf["area_m2"] = gdf.geometry.area
    gdf = gdf[gdf.area_m2 >= 20.0]
    return gdf.reset_index(drop=True)


def _parse_height(raw_height, raw_levels):
    if raw_height is not None and str(raw_height) != "nan":
        try:
            return float(str(raw_height).replace("m", ""))
        except Exception:
            pass
    if raw_levels is not None and str(raw_levels) != "nan":
        try:
            return float(str(raw_levels)) * 3.0
        except Exception:
            pass
    return 12.0


def _heightfield_mesh(xs, ys, zgrid):
    nx = len(xs)
    ny = len(ys)
    if nx < 2 or ny < 2:
        return None

    X, Y = np.meshgrid(xs, ys)
    top_vertices = np.column_stack([X.ravel(), Y.ravel(), zgrid.ravel()])
    bottom_vertices = np.column_stack([X.ravel(), Y.ravel(), np.zeros(nx * ny)])
    vertices = np.vstack([top_vertices, bottom_vertices])

    faces = []
    top_count = nx * ny

    def vid(i, j):
        return j * nx + i

    for j in range(ny - 1):
        for i in range(nx - 1):
            v0 = vid(i, j)
            v1 = vid(i + 1, j)
            v2 = vid(i, j + 1)
            v3 = vid(i + 1, j + 1)
            faces.append([v0, v1, v3])
            faces.append([v0, v3, v2])

            b0 = v0 + top_count
            b1 = v1 + top_count
            b2 = v2 + top_count
            b3 = v3 + top_count
            faces.append([b0, b3, b1])
            faces.append([b0, b2, b3])

    for i in range(nx - 1):
        v0 = vid(i, 0)
        v1 = vid(i + 1, 0)
        b0 = v0 + top_count
        b1 = v1 + top_count
        faces.append([v0, v1, b1])
        faces.append([v0, b1, b0])

        v0 = vid(i, ny - 1)
        v1 = vid(i + 1, ny - 1)
        b0 = v0 + top_count
        b1 = v1 + top_count
        faces.append([v0, b1, v1])
        faces.append([v0, b0, b1])

    for j in range(ny - 1):
        v0 = vid(0, j)
        v1 = vid(0, j + 1)
        b0 = v0 + top_count
        b1 = v1 + top_count
        faces.append([v0, b1, v1])
        faces.append([v0, b0, b1])

        v0 = vid(nx - 1, j)
        v1 = vid(nx - 1, j + 1)
        b0 = v0 + top_count
        b1 = v1 + top_count
        faces.append([v0, v1, b1])
        faces.append([v0, b1, b0])

    return trimesh.Trimesh(vertices=np.asarray(vertices), faces=np.asarray(faces), process=False)


def _elevation_at_xy(x, y, xs, ys, zgrid):
    if x < xs[0] or x > xs[-1] or y < ys[0] or y > ys[-1]:
        return 0.0

    i = np.searchsorted(xs, x) - 1
    j = np.searchsorted(ys, y) - 1
    i = max(0, min(i, len(xs) - 2))
    j = max(0, min(j, len(ys) - 2))

    x1 = xs[i]
    x2 = xs[i + 1]
    y1 = ys[j]
    y2 = ys[j + 1]

    tx = (x - x1) / (x2 - x1) if x2 != x1 else 0.0
    ty = (y - y1) / (y2 - y1) if y2 != y1 else 0.0

    z00 = zgrid[j, i]
    z10 = zgrid[j, i + 1]
    z01 = zgrid[j + 1, i]
    z11 = zgrid[j + 1, i + 1]

    return (1 - tx) * (1 - ty) * z00 + tx * (1 - ty) * z10 + (1 - tx) * ty * z01 + tx * ty * z11


def _build_terrain(bounds, target_crs):
    import rasterio
    from pyproj import Transformer

    with rasterio.open("/home/chispitas/Documents/ESN/3d-model/data/santander.tif") as dem:
        if dem.crs is None:
            raise RuntimeError("DEM has no CRS.")

        transformer = Transformer.from_crs(target_crs, dem.crs, always_xy=True)
        minx, miny, maxx, maxy = bounds

        xs = np.arange(minx, maxx + 10.0, 10.0)
        ys = np.arange(miny, maxy + 10.0, 10.0)
        if len(xs) < 2 or len(ys) < 2:
            raise RuntimeError("Grid resolution too coarse for bounds.")

        X, Y = np.meshgrid(xs, ys)
        x_flat = X.ravel()
        y_flat = Y.ravel()
        rx, ry = transformer.transform(x_flat, y_flat)

        samples = np.array([s[0] for s in dem.sample(zip(rx, ry))], dtype=float)
        if dem.nodata is not None:
            samples[samples == dem.nodata] = np.nan

        z = samples.reshape(Y.shape)
        if np.isnan(z).all():
            raise RuntimeError("DEM returned all nodata.")

        fill = np.nanmedian(z)
        z = np.where(np.isnan(z), fill, z)

        z_min = float(np.min(z))
        z = (z - z_min) * 1.5

        return _heightfield_mesh(xs, ys, z), (xs, ys, z)


print("Downloading buildings...")
buildings = ox.features_from_place("Santander", {"building": True})

buildings = ox.projection.project_gdf(buildings)
clip_bounds = _wgs84_to_projected((-3.817667, 43.47899, -3.765713, 43.46063), buildings.crs)
clip_bounds = (
    clip_bounds[0] - 200.0,
    clip_bounds[1] - 200.0,
    clip_bounds[2] + 200.0,
    clip_bounds[3] + 200.0,
)
clip_poly = box(*clip_bounds)
buildings = _clip_gdf(buildings, clip_bounds)
buildings["geometry"] = buildings.geometry.intersection(clip_poly)

buildings = _clean_polygons(buildings)
if buildings is None or buildings.empty:
    raise RuntimeError("No buildings found inside the clip bounds.")

raw_heights = buildings.get("height", [None] * len(buildings))
raw_levels = buildings.get("building:levels", [None] * len(buildings))
heights = []
for h, lvl in zip(raw_heights, raw_levels):
    height = _parse_height(h, lvl)
    height = min(height, 60.0)
    heights.append(height)
buildings["height"] = heights

terrain_mesh, terrain_data = _build_terrain(clip_bounds, buildings.crs)
xs, ys, zgrid = terrain_data


def terrain_z(x, y):
    return _elevation_at_xy(x, y, xs, ys, zgrid)


print("Creating 3D meshes...")
meshes = []
scene = trimesh.Scene()

if terrain_mesh is not None:
    scene.add_geometry(terrain_mesh, geom_name="terrain")
    meshes.append(terrain_mesh)

mesh_buildings = []
for geom, h in zip(buildings.geometry, buildings.height):
    try:
        mesh = trimesh.creation.extrude_polygon(geom, h)
        pt = geom.representative_point()
        mesh.apply_translation((0, 0, terrain_z(pt.x, pt.y)))
        mesh_buildings.append(mesh)
    except Exception:
        continue

if mesh_buildings:
    buildings_mesh = trimesh.util.concatenate(mesh_buildings)
    scene.add_geometry(buildings_mesh, geom_name="buildings")
    meshes.append(buildings_mesh)

if not meshes:
    raise RuntimeError("No meshes could be created.")

width = clip_bounds[2] - clip_bounds[0]
depth = clip_bounds[3] - clip_bounds[1]
base_thickness = width * 0.015
base = trimesh.creation.box(extents=(width, depth, base_thickness))
base.apply_translation((clip_bounds[0] + width / 2.0, clip_bounds[1] + depth / 2.0, -base_thickness / 2.0))
scene.add_geometry(base, geom_name="base")
meshes.append(base)

offset = (-clip_bounds[0], -clip_bounds[1], 0)
for mesh in meshes:
    mesh.apply_translation(offset)

scene.export("santander_colored.glb")
trimesh.util.concatenate(meshes).export("santander_city_model.stl")
print("Exported GLB and STL")
