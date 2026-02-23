import os
import numpy as np
from scipy.interpolate import interp1d

# ====== CONFIG ======
INPUT_ROOTS = [
    "numpy_results",
    "numpy_results_2",
    # "numpy_results_3",
]

OUTPUT_ROOT   = "numpy_normalised"
TARGET_FRAMES = 30

stats = {"processed": 0, "skipped": 0, "too_short": 0, "errors": 0}


def resample_sequence(sequence, target_frames):
    num_frames = sequence.shape[0]
    if num_frames == target_frames:
        return sequence
    original_times = np.linspace(0, 1, num_frames)
    target_times   = np.linspace(0, 1, target_frames)
    interpolator   = interp1d(original_times, sequence, axis=0, kind="linear")
    return interpolator(target_times)


def load_npy(npy_path):
    """
    Load a .npy file regardless of how it was saved.

    Handles two formats:
      1. Clean float array  — saved by the NEW holistic_extractor.py
         shape: (frames, features)  dtype: float32 / float64

      2. Object array of lists-of-dicts — saved by the OLD extractor
         Each frame is a list of dicts: {"x":..., "y":..., "z":..., "visibility":...}
         We flatten those into a float array automatically.
    """
    data = np.load(npy_path, allow_pickle=True)

    if data.dtype != object:
        # Already a clean numeric array — return as-is
        return data.astype(np.float32)

    # Object array → convert frame-by-frame
    converted = []
    for frame in data:
        flat = []
        for lm in frame:
            flat.append(float(lm["x"]))
            flat.append(float(lm["y"]))
            flat.append(float(lm["z"]))
            if "visibility" in lm:
                flat.append(float(lm["visibility"]))
        converted.append(flat)

    return np.array(converted, dtype=np.float32)


def collect_all_npy_files(input_roots):
    found = []
    for input_root in input_roots:
        if not os.path.exists(input_root):
            print(f"[WARN] Folder not found, skipping: {input_root}")
            continue
        source_root_name = os.path.basename(os.path.abspath(input_root))
        for root, dirs, files in os.walk(input_root):
            for file in files:
                if not file.endswith(".npy"):
                    continue
                npy_path      = os.path.join(root, file)
                relative_path = os.path.relpath(root, input_root)
                found.append((npy_path, source_root_name, relative_path))
    return found


def process_all():
    sign_summary = {}

    all_files = collect_all_npy_files(INPUT_ROOTS)
    print(f"Found {len(all_files)} .npy file(s) across all input roots.\n")

    for npy_path, source_root_name, relative_path in all_files:

        output_dir = os.path.join(OUTPUT_ROOT, source_root_name, relative_path)
        os.makedirs(output_dir, exist_ok=True)

        file        = os.path.basename(npy_path)
        output_path = os.path.join(output_dir, file)

        if os.path.exists(output_path):
            print(f"  [SKIP] {output_path}")
            stats["skipped"] += 1
            continue

        # Load (handles both old dict format and new float format)
        try:
            data = load_npy(npy_path)
        except Exception as e:
            print(f"  [ERROR] Could not load {npy_path}: {e}")
            stats["errors"] += 1
            continue

        if data.ndim != 2:
            print(f"  [WARN] Bad shape {data.shape} in {npy_path}, skipping")
            stats["skipped"] += 1
            continue

        if data.shape[0] < 2:
            print(f"  [WARN] Only {data.shape[0]} frame(s) in {npy_path}, skipping")
            stats["too_short"] += 1
            continue

        original_frames = data.shape[0]
        normalised      = resample_sequence(data, TARGET_FRAMES)

        np.save(output_path, normalised)
        stats["processed"] += 1

        sign_label = os.path.basename(relative_path)
        if sign_label == ".":
            sign_label = source_root_name
        sign_summary[sign_label] = sign_summary.get(sign_label, 0) + 1

        print(f"  [OK] {npy_path}")
        print(f"       {original_frames}f → {TARGET_FRAMES}f | {data.shape[1]} features | {data.dtype} → {output_path}")

    # ====== SUMMARY ======
    print("\n" + "=" * 65)
    print("NORMALISATION COMPLETE")
    print(f"  Target frames  : {TARGET_FRAMES}")
    print(f"  Processed      : {stats['processed']}")
    print(f"  Skipped        : {stats['skipped']}")
    print(f"  Too short      : {stats['too_short']}")
    print(f"  Errors         : {stats['errors']}")
    print(f"  Output folder  : {OUTPUT_ROOT}")
    print("=" * 65)

    if sign_summary:
        print("\nSamples per sign label:")
        for label, count in sorted(sign_summary.items()):
            flag = " ← LOW (need more data)" if count < 5 else ""
            print(f"  {label:<35} {count:>3} sample(s){flag}")

    # ====== VERIFY ======
    print("\nVerifying all output shapes...")
    bad = []
    for root, dirs, files in os.walk(OUTPUT_ROOT):
        for file in files:
            if not file.endswith(".npy"):
                continue
            path = os.path.join(root, file)
            d    = np.load(path)
            if d.shape[0] != TARGET_FRAMES:
                bad.append((path, d.shape))

    if bad:
        print(f"[WARN] {len(bad)} file(s) with wrong frame count:")
        for path, shape in bad:
            print(f"  {path} → {shape}")
    else:
        print(f"[OK] All {stats['processed']} file(s) confirmed at ({TARGET_FRAMES}, features)")


if __name__ == "__main__":
    process_all()