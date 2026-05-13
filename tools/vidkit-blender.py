#!/usr/bin/env python3
"""Blender backend helper for Vidkit-style video production.

This tool is intentionally usable without Blender for validation and script generation.
Actual rendering requires a `blender` binary on PATH or passed with --blender.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

TEMPLATES = ("glass-orbit-cathedral",)
OBJECT_TYPES = {"cube", "sphere", "ico_sphere", "uv_sphere", "plane", "torus", "cylinder", "cone", "text"}
LIGHT_TYPES = {"point", "sun", "area", "spot"}
ENGINES = {"eevee", "cycles"}


def parse_size(value: str) -> tuple[int, int]:
    try:
        w, h = value.lower().split("x", 1)
        w_i, h_i = int(w), int(h)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("size must be WIDTHxHEIGHT") from exc
    if w_i <= 0 or h_i <= 0:
        raise ValueError("size dimensions must be positive")
    return w_i, h_i


def as_vec(value: Any, *, length: int, name: str) -> list[float]:
    if not isinstance(value, list) or len(value) != length:
        raise ValueError(f"{name} must be a {length}-number list")
    try:
        return [float(v) for v in value]
    except Exception as exc:  # noqa: BLE001
        raise ValueError(f"{name} must contain numbers") from exc


def template_spec(name: str) -> dict[str, Any]:
    if name not in TEMPLATES:
        raise SystemExit(f"unknown template: {name}")
    return {
        "size": "1280x720",
        "fps": 24,
        "duration": 5.0,
        "engine": "eevee",
        "world": {"color": "#02030a", "ambient": 0.03},
        "camera": {
            "location": [0, -7.2, 3.0],
            "look_at": [0, 0, 0.4],
            "lens": 34,
            "path": {
                "type": "orbit",
                "target": [0, 0, 0.35],
                "radius": 7.2,
                "height": 3.0,
                "start_degrees": -34,
                "end_degrees": 42,
            },
        },
        "lights": [
            {"type": "area", "name": "cyan window", "location": [-3.8, -3.0, 5.0], "rotation": [60, 0, -35], "energy": 550, "size": 5.0, "color": "#00d8ff"},
            {"type": "point", "name": "magenta core", "location": [2.4, 1.2, 2.2], "energy": 280, "color": "#ff4fd8"},
            {"type": "point", "name": "emerald glint", "location": [-1.2, 2.0, 1.1], "energy": 120, "color": "#5dffb4"},
        ],
        "objects": [
            {"type": "plane", "name": "black glass floor", "location": [0, 0, -0.05], "scale": [8, 8, 1], "material": {"color": "#040713", "metallic": 0.0, "roughness": 0.18}},
            {"type": "torus", "name": "signal halo", "location": [0, 0, 1.2], "rotation": [90, 0, 0], "major_radius": 1.45, "minor_radius": 0.035, "material": {"color": "#00d8ff", "emission": "#00d8ff", "strength": 2.8}, "animate": {"rotation": [0, 0, 360]}},
            {"type": "torus", "name": "magenta halo", "location": [0, 0, 1.2], "rotation": [72, 0, 0], "major_radius": 1.05, "minor_radius": 0.025, "material": {"color": "#ff4fd8", "emission": "#ff4fd8", "strength": 2.0}, "animate": {"rotation": [0, 360, 0]}},
            {"type": "ico_sphere", "name": "glass core", "location": [0, 0, 1.2], "radius": 0.42, "subdivisions": 3, "material": {"color": "#eaffff", "emission": "#5dffb4", "strength": 1.2, "roughness": 0.05}},
            {"type": "cube", "name": "left pillar", "location": [-2.2, 0.45, 1.35], "scale": [0.14, 0.14, 2.7], "material": {"color": "#06162b", "emission": "#003f55", "strength": 0.35}},
            {"type": "cube", "name": "right pillar", "location": [2.2, 0.45, 1.35], "scale": [0.14, 0.14, 2.7], "material": {"color": "#06162b", "emission": "#30003a", "strength": 0.35}},
            {"type": "text", "name": "tiny label", "text": "VIDKIT / BLENDER BACKEND", "location": [-1.7, -1.55, 0.08], "rotation": [74, 0, 0], "size": 0.16, "align": "CENTER", "material": {"color": "#ffffff", "emission": "#00d8ff", "strength": 1.0}},
        ],
    }


def load_spec(source: str) -> dict[str, Any]:
    if source == "demo":
        return template_spec("glass-orbit-cathedral")
    if source.startswith("template:"):
        return template_spec(source.split(":", 1)[1])
    path = Path(source).expanduser()
    return json.loads(path.read_text(encoding="utf-8"))


def validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not isinstance(spec, dict):
        return ["spec must be an object"]
    try:
        parse_size(str(spec.get("size", "1280x720")))
    except ValueError as exc:
        errors.append(f"size: {exc}")
    for field, default in (("fps", 24), ("duration", 3.0)):
        try:
            value = float(spec.get(field, default))
            if value <= 0:
                errors.append(f"{field} must be positive")
        except Exception:
            errors.append(f"{field} must be numeric")
    engine = str(spec.get("engine", "eevee")).lower()
    if engine not in ENGINES:
        errors.append(f"engine unsupported: {engine}")
    camera = spec.get("camera", {})
    if camera and not isinstance(camera, dict):
        errors.append("camera must be an object")
    elif isinstance(camera, dict):
        for key in ("location", "look_at"):
            if key in camera:
                try:
                    as_vec(camera[key], length=3, name=f"camera.{key}")
                except ValueError as exc:
                    errors.append(str(exc))
        path = camera.get("path")
        if path is not None:
            if not isinstance(path, dict):
                errors.append("camera.path must be an object")
            elif path.get("type", "orbit") != "orbit":
                errors.append(f"camera.path.type unsupported: {path.get('type')}")
    lights = spec.get("lights", [])
    if not isinstance(lights, list):
        errors.append("lights must be a list")
    else:
        for idx, light in enumerate(lights):
            if not isinstance(light, dict):
                errors.append(f"lights[{idx}] must be an object")
                continue
            kind = str(light.get("type", "point")).lower()
            if kind not in LIGHT_TYPES:
                errors.append(f"lights[{idx}].type unsupported: {kind}")
            if "location" in light:
                try:
                    as_vec(light["location"], length=3, name=f"lights[{idx}].location")
                except ValueError as exc:
                    errors.append(str(exc))
    objects = spec.get("objects", [])
    if not isinstance(objects, list) or not objects:
        errors.append("objects must be a non-empty list")
    else:
        for idx, obj in enumerate(objects):
            if not isinstance(obj, dict):
                errors.append(f"objects[{idx}] must be an object")
                continue
            kind = str(obj.get("type", "cube")).lower()
            if kind not in OBJECT_TYPES:
                errors.append(f"objects[{idx}].type unsupported: {kind}")
            for key in ("location", "rotation", "scale"):
                if key in obj:
                    try:
                        as_vec(obj[key], length=3, name=f"objects[{idx}].{key}")
                    except ValueError as exc:
                        errors.append(str(exc))
            mat = obj.get("material")
            if mat is not None and not isinstance(mat, dict):
                errors.append(f"objects[{idx}].material must be an object")
    return errors


def assert_valid_spec(spec: dict[str, Any]) -> None:
    errors = validate_spec(spec)
    if errors:
        raise SystemExit("validation failed:\n" + "\n".join(f"- {e}" for e in errors))


def blender_script(spec: dict[str, Any], output: str | None) -> str:
    embedded = json.dumps(spec, indent=2)
    output_json = json.dumps(str(output) if output else "//render.mp4")
    return f'''# Auto-generated by video-blender.py. Run with: blender -b --python this_file.py
import json, math
from pathlib import Path
import bpy
from mathutils import Vector

SPEC = json.loads(r"""{embedded}""")
OUTPUT = {output_json}


def hex_to_rgba(value, alpha=1.0):
    if isinstance(value, (list, tuple)):
        vals = list(value)
        if len(vals) == 3:
            return (float(vals[0]), float(vals[1]), float(vals[2]), alpha)
        if len(vals) == 4:
            return tuple(float(v) for v in vals)
    s = str(value or '#ffffff').strip()
    if s.startswith('#'):
        s = s[1:]
    if len(s) == 3:
        s = ''.join(ch * 2 for ch in s)
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return (r, g, b, alpha)


def set_rotation(obj, degrees):
    obj.rotation_euler = tuple(math.radians(float(v)) for v in degrees)


def make_material(name, cfg):
    cfg = cfg or {{}}
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    color = hex_to_rgba(cfg.get('color', '#ffffff'))
    emission = cfg.get('emission')
    if bsdf:
        try:
            bsdf.inputs['Base Color'].default_value = color
        except Exception:
            pass
        if 'Metallic' in bsdf.inputs:
            bsdf.inputs['Metallic'].default_value = float(cfg.get('metallic', 0.0))
        if 'Roughness' in bsdf.inputs:
            bsdf.inputs['Roughness'].default_value = float(cfg.get('roughness', 0.35))
        if emission:
            # Blender 4 uses separate emission color/strength; older versions may differ.
            if 'Emission Color' in bsdf.inputs:
                bsdf.inputs['Emission Color'].default_value = hex_to_rgba(emission)
            elif 'Emission' in bsdf.inputs:
                try:
                    bsdf.inputs['Emission'].default_value = hex_to_rgba(emission)
                except Exception:
                    pass
            if 'Emission Strength' in bsdf.inputs:
                bsdf.inputs['Emission Strength'].default_value = float(cfg.get('strength', 1.0))
    return mat


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()


def add_object(cfg):
    kind = str(cfg.get('type', 'cube')).lower()
    loc = cfg.get('location', [0, 0, 0])
    rot = cfg.get('rotation', [0, 0, 0])
    scale = cfg.get('scale', [1, 1, 1])
    if kind == 'cube':
        bpy.ops.mesh.primitive_cube_add(size=float(cfg.get('size', 1.0)), location=loc)
    elif kind in {{'sphere', 'uv_sphere'}}:
        bpy.ops.mesh.primitive_uv_sphere_add(segments=int(cfg.get('segments', 48)), ring_count=int(cfg.get('rings', 24)), radius=float(cfg.get('radius', 1.0)), location=loc)
    elif kind == 'ico_sphere':
        bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=int(cfg.get('subdivisions', 2)), radius=float(cfg.get('radius', 1.0)), location=loc)
    elif kind == 'plane':
        bpy.ops.mesh.primitive_plane_add(size=float(cfg.get('size', 1.0)), location=loc)
    elif kind == 'torus':
        bpy.ops.mesh.primitive_torus_add(major_radius=float(cfg.get('major_radius', 1.0)), minor_radius=float(cfg.get('minor_radius', 0.08)), major_segments=int(cfg.get('major_segments', 128)), minor_segments=int(cfg.get('minor_segments', 16)), location=loc)
    elif kind == 'cylinder':
        bpy.ops.mesh.primitive_cylinder_add(vertices=int(cfg.get('vertices', 48)), radius=float(cfg.get('radius', 1.0)), depth=float(cfg.get('depth', 2.0)), location=loc)
    elif kind == 'cone':
        bpy.ops.mesh.primitive_cone_add(vertices=int(cfg.get('vertices', 48)), radius1=float(cfg.get('radius1', 1.0)), radius2=float(cfg.get('radius2', 0.0)), depth=float(cfg.get('depth', 2.0)), location=loc)
    elif kind == 'text':
        bpy.ops.object.text_add(location=loc)
        bpy.context.object.data.body = str(cfg.get('text', 'TEXT'))
        bpy.context.object.data.align_x = str(cfg.get('align', 'CENTER')).upper()
        bpy.context.object.data.size = float(cfg.get('size', 0.35))
    else:
        raise ValueError(f'unsupported object type: {{kind}}')
    obj = bpy.context.object
    obj.name = str(cfg.get('name', kind))
    set_rotation(obj, rot)
    obj.scale = tuple(float(v) for v in scale)
    if cfg.get('material'):
        obj.data.materials.append(make_material(obj.name + ' material', cfg.get('material')))
    anim = cfg.get('animate') or {{}}
    if anim:
        frame_start = int(SPEC.get('frame_start', 1))
        frame_end = int(round(float(SPEC.get('duration', 3.0)) * float(SPEC.get('fps', 24))))
        obj.keyframe_insert(data_path='location', frame=frame_start)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame_start)
        obj.keyframe_insert(data_path='scale', frame=frame_start)
        if 'location' in anim:
            obj.location = tuple(float(v) for v in anim['location'])
        if 'rotation' in anim:
            obj.rotation_euler.rotate_axis('X', math.radians(float(anim['rotation'][0])))
            obj.rotation_euler.rotate_axis('Y', math.radians(float(anim['rotation'][1])))
            obj.rotation_euler.rotate_axis('Z', math.radians(float(anim['rotation'][2])))
        if 'scale' in anim:
            obj.scale = tuple(float(v) for v in anim['scale'])
        obj.keyframe_insert(data_path='location', frame=frame_end)
        obj.keyframe_insert(data_path='rotation_euler', frame=frame_end)
        obj.keyframe_insert(data_path='scale', frame=frame_end)
        for fc in (obj.animation_data.action.fcurves if obj.animation_data and obj.animation_data.action else []):
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
    return obj


def add_light(cfg):
    kind = str(cfg.get('type', 'point')).upper()
    if kind == 'SUN':
        kind = 'SUN'
    elif kind == 'SPOT':
        kind = 'SPOT'
    elif kind == 'AREA':
        kind = 'AREA'
    else:
        kind = 'POINT'
    data = bpy.data.lights.new(str(cfg.get('name', kind.lower())), kind)
    data.energy = float(cfg.get('energy', 250))
    if hasattr(data, 'color'):
        rgba = hex_to_rgba(cfg.get('color', '#ffffff'))
        data.color = rgba[:3]
    if kind == 'AREA':
        data.size = float(cfg.get('size', 4.0))
    obj = bpy.data.objects.new(str(cfg.get('name', data.name)), data)
    bpy.context.collection.objects.link(obj)
    obj.location = tuple(float(v) for v in cfg.get('location', [0, -3, 4]))
    set_rotation(obj, cfg.get('rotation', [0, 0, 0]))
    return obj


# Clear scene
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete()

w, h = [int(v) for v in str(SPEC.get('size', '1280x720')).lower().split('x')]
fps = int(SPEC.get('fps', 24))
duration = float(SPEC.get('duration', 3.0))
frames = max(1, int(round(duration * fps)))
scene = bpy.context.scene
scene.render.resolution_x = w
scene.render.resolution_y = h
scene.render.fps = fps
scene.frame_start = 1
scene.frame_end = frames
engine = str(SPEC.get('engine', 'eevee')).lower()
scene.render.engine = 'CYCLES' if engine == 'cycles' else 'BLENDER_EEVEE_NEXT' if 'BLENDER_EEVEE_NEXT' in [item.identifier for item in bpy.types.RenderSettings.bl_rna.properties['engine'].enum_items] else 'BLENDER_EEVEE'
samples = int(SPEC.get('samples', 64))
if engine == 'cycles':
    try:
        scene.cycles.samples = samples
        scene.cycles.preview_samples = min(samples, 32)
        scene.cycles.use_denoising = bool(SPEC.get('denoise', True))
        scene.cycles.device = 'CPU'
    except Exception:
        pass
else:
    try:
        scene.eevee.taa_render_samples = samples
    except Exception:
        pass
scene.render.image_settings.file_format = 'FFMPEG'
scene.render.ffmpeg.format = 'MPEG4'
scene.render.ffmpeg.codec = 'H264'
scene.render.ffmpeg.audio_codec = 'AAC'
scene.render.filepath = OUTPUT

world = SPEC.get('world') or {{}}
bpy.context.scene.world = bpy.data.worlds.new('world') if bpy.context.scene.world is None else bpy.context.scene.world
bpy.context.scene.world.color = hex_to_rgba(world.get('color', '#02030a'))[:3]

for light in SPEC.get('lights', []):
    add_light(light)
for obj_cfg in SPEC.get('objects', []):
    add_object(obj_cfg)

cam_cfg = SPEC.get('camera') or {{}}
cam_data = bpy.data.cameras.new('Camera')
cam = bpy.data.objects.new('Camera', cam_data)
bpy.context.collection.objects.link(cam)
cam.location = tuple(float(v) for v in cam_cfg.get('location', [0, -6, 3]))
cam_data.lens = float(cam_cfg.get('lens', 35))
target = tuple(float(v) for v in cam_cfg.get('look_at', [0, 0, 0]))
look_at(cam, target)
path = cam_cfg.get('path') or {{}}
if path:
    target = tuple(float(v) for v in path.get('target', target))
    radius = float(path.get('radius', 6.0))
    height = float(path.get('height', cam.location.z))
    start = math.radians(float(path.get('start_degrees', -25)))
    end = math.radians(float(path.get('end_degrees', 25)))
    cam.location = (target[0] + math.sin(start) * radius, target[1] - math.cos(start) * radius, height)
    look_at(cam, target)
    cam.keyframe_insert(data_path='location', frame=1)
    cam.keyframe_insert(data_path='rotation_euler', frame=1)
    cam.location = (target[0] + math.sin(end) * radius, target[1] - math.cos(end) * radius, height)
    look_at(cam, target)
    cam.keyframe_insert(data_path='location', frame=frames)
    cam.keyframe_insert(data_path='rotation_euler', frame=frames)
    if cam.animation_data and cam.animation_data.action:
        for fc in cam.animation_data.action.fcurves:
            for kp in fc.keyframe_points:
                kp.interpolation = 'BEZIER'
scene.camera = cam

bpy.ops.wm.save_as_mainfile(filepath=str(Path(OUTPUT).with_suffix('.blend')))
bpy.ops.render.render(animation=True)
'''


def write_script(spec: dict[str, Any], script_path: Path, output: Path | None) -> None:
    assert_valid_spec(spec)
    script_path.parent.mkdir(parents=True, exist_ok=True)
    script_path.write_text(blender_script(spec, str(output) if output else None), encoding="utf-8")


def render(spec: dict[str, Any], out: Path, *, blender: str | None, keep_script: Path | None = None) -> None:
    assert_valid_spec(spec)
    blender_bin = blender or shutil.which("blender")
    if not blender_bin:
        raise SystemExit("Blender binary not found. Install Blender or pass --blender /path/to/blender. Use `script` to generate a Blender Python file without rendering.")
    out.parent.mkdir(parents=True, exist_ok=True)
    if keep_script:
        script_path = keep_script
        write_script(spec, script_path, out)
        subprocess.run([blender_bin, "-b", "--python", str(script_path)], check=True)
        return
    with tempfile.TemporaryDirectory(prefix="video-blender-") as tmp:
        script_path = Path(tmp) / "render.py"
        write_script(spec, script_path, out)
        subprocess.run([blender_bin, "-b", "--python", str(script_path)], check=True)


def print_json(data: Any) -> None:
    print(json.dumps(data, indent=2))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or render Blender-backed video scenes from JSON specs.")
    parser.add_argument("command", help="templates/init/show/validate/script/render, a JSON spec, demo, or template:<name>")
    parser.add_argument("arg1", nargs="?")
    parser.add_argument("arg2", nargs="?")
    parser.add_argument("--blender", help="Path to blender binary for render command")
    parser.add_argument("--keep-script", type=Path, help="Keep generated Blender Python script at this path when rendering")
    args = parser.parse_args(argv)

    if args.command in {"templates", "list-templates"}:
        if args.arg1 or args.arg2:
            raise SystemExit("usage: video-blender templates")
        print("\n".join(TEMPLATES))
        return 0

    if args.command == "init":
        if not args.arg1 or not args.arg2:
            raise SystemExit("usage: video-blender init <template-name|demo> <out.json>")
        spec = load_spec("demo" if args.arg1 == "demo" else f"template:{args.arg1}")
        assert_valid_spec(spec)
        out = Path(args.arg2)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(spec, indent=2) + "\n", encoding="utf-8")
        print(f"wrote {out}")
        return 0

    if args.command == "show":
        if not args.arg1 or args.arg2:
            raise SystemExit("usage: video-blender show <spec|demo|template:name>")
        spec = load_spec(args.arg1)
        assert_valid_spec(spec)
        print_json(spec)
        return 0

    if args.command == "validate":
        if not args.arg1 or args.arg2:
            raise SystemExit("usage: video-blender validate <spec|demo|template:name>")
        spec = load_spec(args.arg1)
        assert_valid_spec(spec)
        print("valid")
        return 0

    if args.command == "script":
        if not args.arg1 or not args.arg2:
            raise SystemExit("usage: video-blender script <spec|demo|template:name> <out.py>")
        spec = load_spec(args.arg1)
        write_script(spec, Path(args.arg2), None)
        print(f"wrote {args.arg2}")
        return 0

    if args.command == "render":
        if not args.arg1 or not args.arg2:
            raise SystemExit("usage: video-blender render <spec|demo|template:name> <out.mp4> [--blender path]")
        spec = load_spec(args.arg1)
        render(spec, Path(args.arg2), blender=args.blender, keep_script=args.keep_script)
        return 0

    # Convenience: `video-blender spec.json out.mp4` renders.
    if args.arg1 and not args.arg2:
        spec = load_spec(args.command)
        render(spec, Path(args.arg1), blender=args.blender, keep_script=args.keep_script)
        return 0

    raise SystemExit("usage: video-blender templates|init|show|validate|script|render ...")


if __name__ == "__main__":
    raise SystemExit(main())
