import argparse
import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent
DEFAULT_SCAD_DIR = ROOT / "3D"
DEFAULT_STEP_DIR = ROOT.parent.parent / "3d_models" / "passive" / "capacitor" / "th" / "bipolar" / "nichicon" / "ues"


def parse_args():
    parser = argparse.ArgumentParser(
        description="Convert generated Nichicon UES OpenSCAD models to STEP using FreeCAD."
    )
    parser.add_argument(
        "--scad-dir",
        default=str(DEFAULT_SCAD_DIR),
        help="Directory containing .scad files.",
    )
    parser.add_argument(
        "--step-dir",
        default=str(DEFAULT_STEP_DIR),
        help="Directory where .step files will be written.",
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Optional list of .scad files to convert. Defaults to all files in --scad-dir.",
    )
    return parser.parse_args()


def ensure_openscad_configured():
    import FreeCAD

    openscad = shutil.which("openscad")
    if not openscad:
        raise RuntimeError("openscad executable not found in PATH")

    params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/OpenSCAD")
    if params.GetString("openscadexecutable") != openscad:
        params.SetString("openscadexecutable", openscad)


def import_scad(scad_path):
    import FreeCAD
    import importCSG

    ensure_openscad_configured()

    try:
        doc = importCSG.open(str(scad_path))
        if doc is not None:
            return doc
    except Exception:
        pass

    doc = FreeCAD.newDocument(scad_path.stem)
    importCSG.insert(str(scad_path), doc.Name)
    return doc


def export_step(doc, step_path):
    import FreeCAD
    import Import

    doc.recompute()
    export_objects = []
    for obj in doc.Objects:
        shape = getattr(obj, "Shape", None)
        if shape is not None and not shape.isNull():
            export_objects.append(obj)

    if not export_objects:
        raise RuntimeError(f"No exportable objects found in document {doc.Name}")

    step_path.parent.mkdir(parents=True, exist_ok=True)
    Import.export(export_objects, str(step_path))
    FreeCAD.closeDocument(doc.Name)


def resolve_inputs(args):
    scad_dir = Path(args.scad_dir).resolve()
    if args.files:
        files = [Path(path).resolve() for path in args.files]
    else:
        files = sorted(scad_dir.glob("*.scad"))
    return files, Path(args.step_dir).resolve()


def main():
    args = parse_args()
    scad_files, step_dir = resolve_inputs(args)

    if not scad_files:
        print("No .scad files found.")
        return 1

    failures = []
    for scad_path in scad_files:
        step_path = step_dir / f"{scad_path.stem}.step"
        try:
            doc = import_scad(scad_path)
            export_step(doc, step_path)
            print(f"OK   {scad_path.name} -> {step_path}")
        except Exception as exc:
            failures.append((scad_path, exc))
            print(f"FAIL {scad_path.name}: {exc}", file=sys.stderr)

    if failures:
        print(f"{len(failures)} conversion(s) failed.", file=sys.stderr)
        return 1

    print(f"Converted {len(scad_files)} model(s) to {step_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
